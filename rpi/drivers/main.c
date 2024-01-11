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

#define INTERFACE_NAME "wlan0"

bool WiFiEnabled = false;
bool WiFiConnected = false;  // the program needs to set the led as soon as it loads.

// Define your data structure
typedef struct {
    uint8_t buttonA;
    uint8_t buttonB;
    uint8_t SENSE_SYS;
    uint8_t SENSE_BAT;
    uint8_t STATUS;
    uint8_t JOY_LX;
    uint8_t JOY_LY;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
    uint8_t CRCA;  // 16-bit CRC
    uint8_t CRCB;  // 16-bit CRC
} ControllerData;

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

int main(int argc, char *argv[]) {
  int disableCRC = 0;

    // Check command-line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--nocrc") == 0) {
            disableCRC = 1;
            printf("CRC Disabled\n");
        }
    }

  int i2c_fd;
  ControllerData controller_data;

  int shm_fd;
  ControllerData *shared_data;

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
    ftruncate(shm_fd, sizeof(ControllerData));
    shared_data = mmap(0, sizeof(ControllerData), PROT_WRITE, MAP_SHARED, shm_fd, 0);

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

    uint8_t loop_counter = 0;

    while (1) {
        // Read data from i2c device
        if (read(i2c_fd, &controller_data, sizeof(ControllerData)) != sizeof(ControllerData)) {
            perror("Failed to read from i2c device");
            sleep(1);
            continue;
        }

        // Conditionally perform CRC check
        if (!disableCRC) {
            uint16_t computedCRC = computeCRC16_CCITT((const uint8_t*)&controller_data, 9);
            uint16_t receivedCRC = (controller_data.CRCA << 8) | controller_data.CRCB;

            if (computedCRC != receivedCRC) {
                crcCount++;
                printf("CRC error detected. Retrying...\n");
                printf("%d errors detected since startup.\n", crcCount);
                continue;
            }
        }

        // Copy data to shared memory
        *shared_data = controller_data;
        // issue shutdown when button pressed or when battery is very low
        if (((controller_data.STATUS >> 4) & 1) | (controller_data.SENSE_SYS <= 128)) {
          poweroffCounter++;
          if (poweroffCounter > 10) { // need to hold button for a small amount of time to initiate poweroff
            system("poweroff");
            break;
          }
        } else {
          poweroffCounter = 0;
        }

        if (controller_data.STATUS & 0b00100000) {
          usleep(100000); // sleep a lot longer when the hold switch is down
        }

        if (!loop_counter) { // its a uint8_t. checks whenever it rolls over. runs every 4 seconds
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
                  //printf("%s is %s\n", INTERFACE_NAME, WiFiEnabled ? "enabled" : "disabled");
                  //printf("%s is %s\n", INTERFACE_NAME, WiFiConnected ? "connected" : "disconnected");
                }
            }
        }

        loop_counter++; // Increment counter

        // Wait for 16ms before reading again
        usleep(16000);
    }

    // Cleanup
    close(fd);
    close(i2c_fd);

    return 0;
}
