#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/uinput.h>
#include <string.h>

uint8_t dualJoystick = 0;

typedef struct {
    uint16_t buttons; // Combined buttonA and buttonB
    uint8_t SENSE_SYS;
    uint8_t SENSE_BAT;
    uint8_t STATUS;
    uint8_t JOY_LX;
    uint8_t JOY_LY;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
} ControllerData;

int setup_uinput_device(int uinput_fd) {
    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));

    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi-Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1234;
    uidev.id.product = 0x5678;
    uidev.id.version = 1;
    uidev.absmin[ABS_X] = 40;
    uidev.absmax[ABS_X] = 215;
    uidev.absflat[ABS_X] = 20;
    uidev.absfuzz[ABS_X] = 20;
    uidev.absmin[ABS_Y] = 40;
    uidev.absmax[ABS_Y] = 215;
    uidev.absflat[ABS_Y] = 20;
    uidev.absfuzz[ABS_Y] = 20;
    if (dualJoystick) {
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
    if (dualJoystick) {
      ioctl(uinput_fd, UI_SET_KEYBIT, BTN_0);  // New button 1
      ioctl(uinput_fd, UI_SET_KEYBIT, BTN_1);  // New button 2
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);
    if (dualJoystick) {
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RX);
      ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RY);
    }

    return ioctl(uinput_fd, UI_DEV_CREATE);
}
uint16_t prevCombinedButtons;
void update_controller_data(ControllerData *shared_data, int uinput_fd) {
    struct input_event event;
    uint16_t combinedButtons = shared_data->buttons;

    // Check if the Home button was pressed in the last data set (bit position 15)
    if (prevCombinedButtons & 0b1000000000000000) {
      // Force the Select button to be pressed in the current data set (set bit position 1 in combinedButtons)
      combinedButtons |= 0b0000000000000010;
    }
    prevCombinedButtons = combinedButtons;

    // Update all button states
    for(int i = 0; i < 16; i++) {
        event.type = EV_KEY;
        event.code = BTN_TRIGGER_HAPPY1 + i;
        event.value = (combinedButtons >> i) & 1;

        // Send the button event to uinput
        ssize_t ret = write(uinput_fd, &event, sizeof(event));
        if (ret < 0) {
            perror("Failed to write button event in update_controller_data");
            // Handle error as appropriate
        }
    }

    if (dualJoystick) {
      // Handle the additional buttons encoded in JOY_RX and JOY_RY
      uint8_t button_rx = shared_data->JOY_RX & 1; // Extract bit 0
      uint8_t button_ry = shared_data->JOY_RY & 1; // Extract bit 0

      event.type = EV_KEY;
      event.code = BTN_0;  // Button from JOY_RX
      event.value = button_rx;
      write(uinput_fd, &event, sizeof(event));

      event.code = BTN_1;  // Button from JOY_RY
      event.value = button_ry;
      write(uinput_fd, &event, sizeof(event));
    }

    // Update joystick positions
    event.type = EV_ABS;
    event.code = ABS_X;
    event.value = shared_data->JOY_LX;
    write(uinput_fd, &event, sizeof(event));

    event.code = ABS_Y;
    event.value = shared_data->JOY_LY;
    write(uinput_fd, &event, sizeof(event));

    // Send the SYN event
    event.type = EV_SYN;
    event.code = SYN_REPORT;
    event.value = 0;
    write(uinput_fd, &event, sizeof(event));

    if (dualJoystick) {
      event.type = EV_ABS;
      event.code = ABS_RX;
      event.value = shared_data->JOY_RX;
      write(uinput_fd, &event, sizeof(event));

      event.code = ABS_RY;
      event.value = shared_data->JOY_RY;
      write(uinput_fd, &event, sizeof(event));

      // Send the SYN event
      event.type = EV_SYN;
      event.code = SYN_REPORT;
      event.value = 0;
      write(uinput_fd, &event, sizeof(event));
    }
}


int main(int argc, char *argv[]) {
  // Check command-line arguments
  for (int i = 1; i < argc; i++) {
      if (strcmp(argv[i], "--dual") == 0) {
          dualJoystick = 1;
          printf("Dual Joystick Enabled\n");
      }
  }
    int uinput_fd;
    ControllerData *shared_data;
    ControllerData last_data;
    memset(&last_data, 0, sizeof(ControllerData));

    int shm_fd;

    uinput_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if(uinput_fd < 0) {
        perror("Could not open uinput device");
        return 1;
    }

    if (setup_uinput_device(uinput_fd) != 0) {
        perror("Error setting up uinput device");
        return 1;
    }

    shm_fd = shm_open("my_shm", O_RDWR, 0666);
    shared_data = mmap(0, sizeof(ControllerData), PROT_READ, MAP_SHARED, shm_fd, 0);

    while(1) {
        while (shared_data->STATUS & 0b00100000) {
            usleep(100000); // Sleep when the hold switch is down (sleep mode)
        }
        // Update only when it does not match shared_data
        if(memcmp(shared_data, &last_data, sizeof(ControllerData)) != 0) {
          update_controller_data(shared_data, uinput_fd);
          memcpy(&last_data, shared_data, sizeof(ControllerData));
        }

        usleep(16666);
    }

    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);
    close(shm_fd);
    return 0;
}
