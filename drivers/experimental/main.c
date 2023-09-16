//compile with gcc -O3 main.c -o main -lrt
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>

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
} ControllerData;

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

    // Create the shared memory segment
    shm_fd = shm_open("my_shm", O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd, sizeof(ControllerData));
    shared_data = mmap(0, sizeof(ControllerData), PROT_WRITE, MAP_SHARED, shm_fd, 0);

    while (1) {
        // Read data from i2c device
        if (read(i2c_fd, &controller_data, sizeof(ControllerData)) != sizeof(ControllerData)) {
            perror("Failed to read from i2c device");
            break;
        }

        // Copy data to shared memory
        *shared_data = controller_data;

        // Wait for 16ms before reading again
        usleep(16000);
    }

    // Cleanup
    close(i2c_fd);
    close(shm_fd);
    shm_unlink("my_shm");

    return 0;
}
