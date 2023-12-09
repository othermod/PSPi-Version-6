#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>

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
    int shm_fd;
    ControllerData *shared_data;

    // Try to open the shared memory segment. If it doesn't exist, wait and retry.
    while ((shm_fd = shm_open("my_shm", O_RDONLY, 0666)) == -1) {
        if (errno == ENOENT) {
            // Shared memory segment doesn't exist. Sleep and try again.
            sleep(1);
        } else {
            // Some other error occurred
            perror("shm_open");
            return 1;
        }
    }

    // Map the shared memory
    shared_data = mmap(0, sizeof(ControllerData), PROT_READ, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return 1;
    }

    // Read JOY_LX and JOY_LY values from shared memory and print them
    printf("SENSE_SYS: %u\n", shared_data->SENSE_SYS);
    printf("CALC: %u\n", shared_data->SENSE_SYS*8*3000/1024);

    // Cleanup
    close(shm_fd);
//    shm_unlink("my_shm");

    return 0;
}
