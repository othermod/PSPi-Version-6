#ifndef _CHIPINFO_H_
#define _CHIPINFO_H_

#include <stdint.h>

typedef struct avr_chipinfo_s
{
    uint8_t     sig[3];
    const char  name[16];
    uint16_t    flashsize;
    uint16_t    eepromsize;
} avr_chipinfo_t;

const avr_chipinfo_t *  chipinfo_get_by_signature   (const uint8_t *sig);
const char *            chipinfo_get_avr_name       (const uint8_t *sig);

#endif /* _CHIPINFO_H_ */
