#define BACKLIGHT_ADDRESS 0x72

// TPS61160DRVR LCD backlight chip timings
// I had issues when setting values close to the minimum
#define tSTART 10 // minimum of 2 microseconds
#define tEOS 10 // minimum of 2 microseconds
#define tH_LB 10 // minimum of 2 microseconds
#define tH_HB 25 // minimum of 4 microseconds
#define tL_LB 25 // minimum of 4 microseconds
#define tL_HB 10 // minimum of 2 microseconds
#define toff 3000 // minimum of 2500 microseconds to reset the chip
