sudo killall osd
sleep 1
./bootloader
sleep 1
./stay
sleep 1
./stay
sleep 1
/home/pi/multiboot/./twiboot -a 0x29 -d /dev/i2c-1 -w flash:/home/pi/multiboot/Firmware.ino.arduino_standard.hex
