#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <stdlib.h>

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

int main() {
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
    while (1) {
        // Read data from i2c device
        if (read(i2c_fd, &controller_data, sizeof(ControllerData)) != sizeof(ControllerData)) {
            perror("Failed to read from i2c device");
            sleep(1);
            continue;
        }

        // Compute CRC-16 for the received data
        uint16_t computedCRC = computeCRC16_CCITT((const uint8_t*)&controller_data, 9);
        uint16_t receivedCRC = (controller_data.CRCA << 8) | controller_data.CRCB;

        // Swap bytes of received CRC for comparison


        if (computedCRC != receivedCRC) {
            crcCount++;
            printf("CRC error detected. Retrying...\n");
            printf("Computed CRC: %04X, Received CRC: %04X\n", computedCRC, receivedCRC);
            printf("Data Received:\n");
            printf("Button A: %d\n", controller_data.buttonA);
            printf("Button B: %d\n", controller_data.buttonB);
            printf("SENSE_SYS: %d\n", controller_data.SENSE_SYS);
            printf("SENSE_BAT: %d\n", controller_data.SENSE_BAT);
            printf("STATUS: %d\n", controller_data.STATUS);
            printf("JOY_LX: %d\n", controller_data.JOY_LX);
            printf("JOY_LY: %d\n", controller_data.JOY_LY);
            printf("JOY_RX: %d\n", controller_data.JOY_RX);
            printf("JOY_RY: %d\n", controller_data.JOY_RY);
            printf("%d errors detected since startup.\n", crcCount);
            continue;
        }

        // Copy data to shared memory
        *shared_data = controller_data;
        // issue shutdown when button pressed or when battery is very low
        if ((controller_data.STATUS >> 4) & 1) {
          poweroffCounter++;
          if (poweroffCounter > 10) { // need to hold button for a small amount of time to initiate poweroff
            system("sudo poweroff");
            break;
          }
        } else {
          poweroffCounter = 0;
        }

        if (controller_data.STATUS & 0b00100000) {
          usleep(100000); // sleep a lot longer when the hold switch is down
        }

        // Wait for 16ms before reading again
        usleep(16000);
    }

    // Cleanup
    close(i2c_fd);

    return 0;
}
