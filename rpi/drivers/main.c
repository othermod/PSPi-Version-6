#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <net/if.h>
#include <linux/rtnetlink.h>
#include <sys/socket.h>
#include <linux/uinput.h>

#include <time.h>

#define INTERFACE_NAME "wlan0"

int enableCRC = 1;
bool enableGamepad = 1;
bool isDim = 0;
bool isIdle = 0;
uint32_t previousStatus;
bool WiFiEnabled = false;
bool WiFiConnected = false;
uint8_t loop_counter = 0;
uint16_t Count = 0;
uint32_t timeAtLastChange;
bool fast = 0;

uint8_t brightness;
#define DATASIZE 11

// fix these names
uint8_t JOYSTICKS = 1;
uint32_t DIMMING = 0;

typedef struct {
    uint16_t BUTTONS;
    uint8_t SENSE_SYS;
    uint8_t SENSE_BAT;
    uint8_t STATUS;
    uint8_t JOY_LX;
    uint8_t JOY_LY;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
    uint8_t CRCA;  // 16-bit CRC
    uint8_t CRCB;  // 16-bit CRC
} SharedData;

SharedData *mappedMemory;
SharedData previousData;

// CRC16 calculation function
uint16_t computeCRC16_CCITT(const uint8_t *data, uint8_t length) {
    uint16_t crc = 0xFFFF; // Initial value for CRC-16-CCITT
    uint16_t poly = 0x1021; // Polynomial for CRC-16-CCITT

    for (uint8_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ poly;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

int setup_uinput_device(int uinput_fd) {
    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));

    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi-Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1234;
    uidev.id.product = 0x5678;
    uidev.id.version = 1;

    if (JOYSTICKS) {
      uidev.absmin[ABS_X] = 40;
      uidev.absmax[ABS_X] = 215;
      uidev.absflat[ABS_X] = 20;
      uidev.absfuzz[ABS_X] = 20;
      uidev.absmin[ABS_Y] = 40;
      uidev.absmax[ABS_Y] = 215;
      uidev.absflat[ABS_Y] = 20;
      uidev.absfuzz[ABS_Y] = 20;
    }
    if (JOYSTICKS==2) {
      uidev.absmin[ABS_RX] = 40;  // Adjust these values as per your needs
      uidev.absmax[ABS_RX] = 215;
      uidev.absflat[ABS_RX] = 20;
      uidev.absfuzz[ABS_RX] = 20;
      uidev.absmin[ABS_RY] = 40;
      uidev.absmax[ABS_RY] = 215;
      uidev.absflat[ABS_RY] = 20;
      uidev.absfuzz[ABS_RY] = 20;
    }

    ssize_t ret = write(uinput_fd, &uidev, sizeof(uidev));
    if (ret < 0) {
        perror("Failed to write to uinput device in setup_uinput_device");
        return -1;
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    for(int i = 0; i < 16; i++) {
        ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TRIGGER_HAPPY1 + i);
    }
    if (JOYSTICKS==2) {
      ioctl(uinput_fd, UI_SET_KEYBIT, BTN_0);  // New button 1
      ioctl(uinput_fd, UI_SET_KEYBIT, BTN_1);  // New button 2
    }
    if (JOYSTICKS) {
      ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);
    }

    if (JOYSTICKS==2) {
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RX);
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RY);
    }

    return ioctl(uinput_fd, UI_DEV_CREATE);
}

void update_controller_data(int uinput_fd) {
    struct input_event event;

    // Update all button states
    for(int i = 0; i < 16; i++) {
        event.type = EV_KEY;
        event.code = BTN_TRIGGER_HAPPY1 + i;
        event.value = (mappedMemory->BUTTONS >> i) & 1;

        // Send the button event to uinput
        ssize_t ret = write(uinput_fd, &event, sizeof(event));
        if (ret < 0) {
            perror("Failed to write button event in update_controller_data");
            // Handle error as appropriate
        }
    }

    if (JOYSTICKS == 2) {
      // Handle the additional buttons encoded in JOY_RX and JOY_RY
      uint8_t button_rx = mappedMemory->JOY_RX & 1; // Extract bit 0
      uint8_t button_ry = mappedMemory->JOY_RY & 1; // Extract bit 0

      event.type = EV_KEY;
      event.code = BTN_0;  // Button from JOY_RX
      event.value = button_rx;
      write(uinput_fd, &event, sizeof(event));

      event.code = BTN_1;  // Button from JOY_RY
      event.value = button_ry;
      write(uinput_fd, &event, sizeof(event));
    }

    if (JOYSTICKS) {
      // Update joystick positions
      event.type = EV_ABS;
      event.code = ABS_X;
      event.value = mappedMemory->JOY_LX;
      write(uinput_fd, &event, sizeof(event));

      event.code = ABS_Y;
      event.value = mappedMemory->JOY_LY;
      write(uinput_fd, &event, sizeof(event));

      // Send the SYN event
      event.type = EV_SYN;
      event.code = SYN_REPORT;
      event.value = 0;
      write(uinput_fd, &event, sizeof(event));
    }

    if (JOYSTICKS == 2) {
      event.type = EV_ABS;
      event.code = ABS_RX;
      event.value = mappedMemory->JOY_RX;
      write(uinput_fd, &event, sizeof(event));

      event.code = ABS_RY;
      event.value = mappedMemory->JOY_RY;
      write(uinput_fd, &event, sizeof(event));

      // Send the SYN event
      event.type = EV_SYN;
      event.code = SYN_REPORT;
      event.value = 0;
      write(uinput_fd, &event, sizeof(event));
    }
}

void dimmingFunction(int i2c_fd) {
  uint32_t Status = 0;
  // Combine the values into Status
  Status |= (uint32_t)mappedMemory->BUTTONS << 18; // Shifted to the highest 8 bits

  //Status |= (uint32_t)mappedMemory->STATUS << 8;     // Next 8 bits
  Status |= (uint32_t)(mappedMemory->JOY_LX >> 4) << 4; // Next 4 bits
  Status |= (uint32_t)(mappedMemory->JOY_LY >> 4);      // Last 4 bits

  if (previousStatus == Status) {
    if (isIdle==0) {
      timeAtLastChange = time(NULL);
    }
    isIdle = 1;
    if (timeAtLastChange + DIMMING <= time(NULL) ) {
      if (!isDim) {
        uint8_t i2cData[4];
        i2cData[0] = 0x22; // Command byte
        i2cData[1] = 1;
        write(i2c_fd, i2cData, 4);
        isDim = 1;
        //printf("Current time (raw): %ld\n", time(NULL));
        brightness = mappedMemory->STATUS&0b00000111;
        brightness++;
        //printf("Brightness %d\n", brightness);
      }
    }
  } else {
    isIdle = 0;
    if (isDim) {
      timeAtLastChange = time(NULL); // this seems like its in the wrong place. how is it functioning?
      uint8_t temp = mappedMemory->STATUS&0b00000111;

      if (temp == 0b00000000) {
        uint8_t i2cData[4];
        i2cData[0] = 0x22; // Command byte
        i2cData[1] = brightness;
        write(i2c_fd, i2cData, 4);
      }

      isDim = 0;
      //printf("Current time (raw): %ld\n", timeAtLastChange);
    }
  }

  previousStatus = Status;
}

int main(int argc, char *argv[]) {
  // Check command-line arguments
  for (int i = 1; i < argc; i++) {
    if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
      printf("Usage: [options]\n");
      printf("Options:\n");
      printf("  --nocrc            Disable CRC checks\n");
      printf("  --joysticks <num>  Set number of joysticks, where <num> is between 0 and 2\n");
      printf("  --dim <seconds>    Enable dimming after <seconds>, between 1 and 3600\n");
      printf("  --fast             Enable fast mode (double input polling rate)\n");
      printf("  --nogamepad        Display the gamepad\n");
      printf("  --help, -h         Display this help and exit\n");
      return 0;
    } else if (strcmp(argv[i], "--nocrc") == 0) {
      enableCRC = 0;
      printf("CRC Disabled\n");
  } else if (strcmp(argv[i], "--joysticks") == 0) {
      if (i + 1 < argc) {
          JOYSTICKS = atoi(argv[++i]);
          if (JOYSTICKS < 0 || JOYSTICKS > 2) {
              printf("Invalid number of joysticks. Must be between 0 and 2.\n");
              return 1;
          }
          printf("Number of joysticks: %d\n", JOYSTICKS);
      } else {
          printf("No number specified for --joysticks\n");
          return 1;
      }
  } else if (strcmp(argv[i], "--dim") == 0) {
      if (i + 1 < argc && atoi(argv[i + 1]) >= 1 && atoi(argv[i + 1]) <= 3600) {
          DIMMING = atoi(argv[++i]);
          printf("Dimming enabled: %d seconds\n", DIMMING);
      } else {
          DIMMING = 120; // default value
          printf("Dimming enabled: default 120 seconds\n");
      }
  } else if (strcmp(argv[i], "--fast") == 0) {
    printf("Gotta go fast\n");
    fast = 1;
  } else if (strcmp(argv[i], "--nogamepad") == 0) {
    printf("Gamepad disabled\n");
    enableGamepad = 0;
  }
}

  int i2c_fd;
  int shm_fd;

  int uinput_fd;
  uinput_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
  if(uinput_fd < 0) {
      perror("Could not open uinput device");
      return 1;
  }
  if (enableGamepad) {
    if (setup_uinput_device(uinput_fd) != 0) {
        perror("Error setting up uinput device");
        return 1;
    }
  }

    // Open i2c device
    i2c_fd = open("/dev/i2c-1", O_RDWR);
    if (i2c_fd < 0) {
        perror("Failed to open i2c bus");
        return 1;
    }

    // Set i2c slave
    if (ioctl(i2c_fd, I2C_SLAVE, 0x10) < 0) {
        perror("Failed to set i2c slave");
        close(i2c_fd);
        return 1;
    }

    shm_fd = shm_open("my_shm", O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd, sizeof(SharedData));
    mappedMemory = mmap(0, sizeof(SharedData), PROT_WRITE, MAP_SHARED, shm_fd, 0);

    int crcCount = 0;
    int poweroffCounter = 0;

    // Setup for WiFi status checking
    int ifindex = if_nametoindex(INTERFACE_NAME);
    if (ifindex == 0) {
        perror("Error getting interface index");
        return 1;
    }

    struct {
        struct nlmsghdr nlh;
        struct ifinfomsg ifi;
    } req;

    char buf[4096];
    int fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (fd == -1) {
        perror("Error creating socket");
        return 1;
    }

    memset(&req, 0, sizeof(req));
    req.nlh.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req.nlh.nlmsg_flags = NLM_F_REQUEST;
    req.nlh.nlmsg_type = RTM_GETLINK;
    req.ifi.ifi_family = AF_UNSPEC;
    req.ifi.ifi_index = ifindex;

    while (1) {
        // Read data from i2c device
        if (read(i2c_fd, mappedMemory, DATASIZE) != DATASIZE) {
            perror("Failed to read from i2c device");
            sleep(1);
            continue;
        }
        // Conditionally perform CRC check
        if (enableCRC) {
            uint16_t computedCRC = computeCRC16_CCITT((const uint8_t*) & *mappedMemory, 9);
            uint16_t receivedCRC = (mappedMemory->CRCA << 8) | mappedMemory->CRCB;

            if (computedCRC != receivedCRC) {
                crcCount++;
                //printf("CRC error detected. Retrying...\n");
                //printf("%d errors detected since startup.\n", crcCount);
                continue;
            }
        }

        // issue shutdown when button pressed or when battery is very low
        if (((mappedMemory->STATUS >> 4) & 1) | (mappedMemory->SENSE_SYS <= 128)) {
          poweroffCounter++;
          if (poweroffCounter > 10) { // need to hold button for a small amount of time to initiate poweroff
            system("poweroff");
            break;
          }
        } else {
          poweroffCounter = 0;
        }

        if (mappedMemory->STATUS & 0b00100000) {
          usleep(100000); // sleep a lot longer when the hold switch is down
        }

        if (!loop_counter) { // checks whenever it rolls over
            send(fd, &req, req.nlh.nlmsg_len, 0);
            int len = recv(fd, buf, sizeof(buf), 0);
            struct nlmsghdr *nh = (struct nlmsghdr *)buf;
            bool checkConnection = 0;

            if (nh->nlmsg_type == RTM_NEWLINK) {
                struct ifinfomsg *ifi = NLMSG_DATA(nh);
                WiFiEnabled = ifi->ifi_flags & IFF_UP;
                checkConnection = ifi->ifi_flags & IFF_RUNNING;
                if (checkConnection != WiFiConnected) {
                  WiFiConnected = checkConnection;
                  uint8_t i2cData[4];
                  i2cData[0] = 0x20; // Command byte
                  i2cData[1] = WiFiConnected ? 1 : 0;// Data byte: 1 for connected, 0 for disconnected
                  write(i2c_fd, i2cData, 4);
                }
            }
        }

        loop_counter++; // Increment counter

        if (DIMMING) {
          dimmingFunction(i2c_fd);
        }
        if (enableGamepad) {
          if (memcmp(&previousData, mappedMemory, sizeof(SharedData)) != 0) {
            update_controller_data(uinput_fd);
            previousData = *mappedMemory;
            }
        }

        // Wait for 16ms before reading again
        if (fast) {
          usleep(8000);
        } else {
          usleep(16000);
        }
    }

    // Cleanup
    close(fd);
    close(i2c_fd);
    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);

    return 0;
}
