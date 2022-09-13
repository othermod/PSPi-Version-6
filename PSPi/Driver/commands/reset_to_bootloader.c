#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <string.h>

#define I2C_ADDRESS 0x06

int openI2C() {
  int file;
  char * filename = "/dev/i2c-1"; //specify which I2C bus to use
  if ((file = open(filename, O_RDWR)) < 0) {
    fprintf(stderr, "Failed to open the i2c bus"); /* ERROR HANDLING: you can check errno to see what went wrong */
    exit(1);
  }
  return file;
}


int main(int argc, char * argv[]) {
  int I2CFile = openI2C(); // open I2C device
  if (ioctl(I2CFile, I2C_SLAVE, I2C_ADDRESS) < 0) { // initialize communication
    fprintf(stderr, "I2C: Failed to acquire bus access/talk to slave 0x%x\n", I2C_ADDRESS);
    return 0;
  }
  int data[] = {0x02, 0x01};
 if (write(I2CFile, data, 2) != 2) {
   printf("Unable to write command\n");
 }

  close(I2CFile); // close file
}
