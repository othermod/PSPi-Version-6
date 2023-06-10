#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>

int main() {

int file;
char *filename = "/dev/i2c-1";
if ((file = open(filename, O_RDWR)) < 0) {
    /* ERROR HANDLING: you can check errno to see what went wrong */
    perror("Failed to open the i2c bus");
    exit(1);
}

int addr = 0x06;          // The I2C address of the ADC
if (ioctl(file, I2C_SLAVE, addr) < 0) {
	printf("Failed to acquire bus access and/or talk to slave.\n");
	/* ERROR HANDLING; you can check errno to see what went wrong */
	exit(1);
}

char buf[1] = {0};
while(1) {
	buf[0] = 4; //led on
	if (write(file,buf,1) != 1) {
		/* ERROR HANDLING: i2c transaction failed */
		printf("Failed to write to the i2c bus.\n");
	}
	sleep(2);
	buf[0] = 5; //led off
	if (write(file,buf,1) != 1) {
		/* ERROR HANDLING: i2c transaction failed */
		printf("Failed to write to the i2c bus.\n");
	}
	sleep(2);
	}
}
