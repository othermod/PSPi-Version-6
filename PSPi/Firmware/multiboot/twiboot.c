/***************************************************************************
*   Copyright (C) 10/2010 by Olaf Rempel                                  *
*   razzor@kopf-tisch.de                                                  *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; version 2 of the License,               *
*                                                                         *
*   This program is distributed in the hope that it will be useful,       *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU General Public License for more details.                          *
*                                                                         *
*   You should have received a copy of the GNU General Public License     *
*   along with this program; if not, write to the                         *
*   Free Software Foundation, Inc.,                                       *
*   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
***************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>

#include <linux/i2c.h>
#include <linux/i2c-dev.h>

#include "chipinfo_avr.h"
#include "filedata.h"
#include "list.h"
#include "multiboot.h"
#include "optarg.h"

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))

#define TWI_DEFAULT_DEVICE  "/dev/i2c-0"

#define READ_BLOCK_SIZE         128     /* bytes in one flash/eeprom read request */
#define WRITE_BLOCK_SIZE        16      /* bytes in one eeprom write request */
#define WRITE_RETRY_COUNT       50      /* write retries when slave does not not acknowledge */
#define WRITE_RETRY_DELAY_US    2000    /* delay in us per retry */

/* SLA+R */
#define CMD_WAIT                0x00
#define CMD_READ_VERSION        0x01
#define CMD_READ_MEMORY         0x02

/* SLA+W */
#define CMD_SWITCH_APPLICATION  CMD_READ_VERSION
#define CMD_WRITE_MEMORY        CMD_READ_MEMORY

/* CMD_SWITCH_APPLICATION parameter */
#define BOOTTYPE_BOOTLOADER     0x00    /* only in APP */
#define BOOTTYPE_APPLICATION    0x80

/* CMD_{READ|WRITE}_* parameter */
#define MEMTYPE_CHIPINFO        0x00
#define MEMTYPE_FLASH           0x01
#define MEMTYPE_EEPROM          0x02
#define MEMTYPE_PARAMETERS      0x03    /* only in APP */

struct multiboot_ops twi_ops;

struct twi_privdata
{
    char        *device;
    uint8_t     address;
    int         fd;
    int         connected;
    int         stay_in_bootloader;

    uint8_t     pagesize;
    uint16_t    flashsize;
    uint16_t    eepromsize;
};

static struct option twi_optargs[] =
{
    { "address",    1, 0, 'a' }, /* -a <addr>       */
    { "device",     1, 0, 'd' }, /* [ -d <device> ] */
    { "stay",       0, 0, 's' }, /* [ -s ]          */
};


/* *************************************************************************
 * twi_write_retries
 * ************************************************************************* */
static int twi_write_retries(int fd, const void *buf, size_t count)
{
    int result;
    int retries = WRITE_RETRY_COUNT;
    do {
        result = write(fd, buf, count);
        if (result >= 0)
        {
            break;
        }
        else
        {
            /*
             * slave device does not acknowledge (eg. not able to clockstretch)
             * actual error code may be driver specific
             */
            if ((errno == ENXIO) || (errno == EREMOTEIO) || (errno == EIO))
            {
                usleep(WRITE_RETRY_DELAY_US);
            }
            else
            {
                fprintf(stderr, "twi_write_retries(): %s\n",
                        strerror(errno));

                retries = 0;
            }
        }
    } while (retries--);

    return result;
} /* twi_write_retries */


/* *************************************************************************
 * twi_switch_application
 * ************************************************************************* */
static int twi_switch_application(struct twi_privdata *twi,
                                  uint8_t application)
{
    uint8_t cmd[] = { CMD_SWITCH_APPLICATION, application };

    return (twi_write_retries(twi->fd, cmd, sizeof(cmd)) != sizeof(cmd));
} /* twi_switch_application */


/* *************************************************************************
 * twi_switch_application
 * ************************************************************************* */
static int twi_read_version(struct twi_privdata *twi,
                            char *version, int length)
{
    uint8_t cmd[] = { CMD_READ_VERSION };

    if (twi_write_retries(twi->fd, cmd, sizeof(cmd)) != sizeof(cmd))
    {
        return -1;
    }

    memset(version, 0, length);
    if (read(twi->fd, version, length) != length)
    {
        return -1;
    }

    int i;
    for (i = 0; i < length; i++)
    {
        version[i] &= ~0x80;
    }

    return 0;
} /* twi_read_version */


/* *************************************************************************
 * twi_read_memory
 * ************************************************************************* */
static int twi_read_memory(struct twi_privdata *twi,
                           uint8_t *buffer, uint8_t size,
                           uint8_t memtype, uint16_t address)
{
    uint8_t cmd[] = { CMD_READ_MEMORY, memtype, (address >> 8) & 0xFF, (address & 0xFF) };

    if (twi_write_retries(twi->fd, cmd, sizeof(cmd)) != sizeof(cmd))
    {
        return -1;
    }

    return (read(twi->fd, buffer, size) != size);
} /* twi_read_memory */


/* *************************************************************************
 * twi_write_memory
 * ************************************************************************* */
static int twi_write_memory(struct twi_privdata *twi,
                            uint8_t *buffer, uint8_t size,
                            uint8_t memtype, uint16_t address)
{
    int bufsize;

    if (memtype == MEMTYPE_FLASH)
    {
        if ((address & (twi->pagesize -1)) != 0x00)
        {
            fprintf(stderr, "twi_write_memory(): address 0x%04x not aligned to pagesize 0x%02x\n",
                    address, twi->pagesize);

            return -1;
        }

        bufsize = 4 + twi->pagesize;
    }
    else
    {
        bufsize = 4 + size;
    }

    uint8_t *cmd = malloc(bufsize);
    if (cmd == NULL)
    {
        return -1;
    }

    cmd[0] = CMD_WRITE_MEMORY;
    cmd[1] = memtype;
    cmd[2] = (address >> 8) & 0xFF;
    cmd[3] = (address & 0xFF);
    memcpy(cmd +4, buffer, size);

    if (memtype == MEMTYPE_FLASH)
    {
        memset(cmd +4 +size, 0xFF, twi->pagesize - size);
    }

    int result = twi_write_retries(twi->fd, cmd, bufsize);
    free(cmd);

    return (result != bufsize);
} /* twi_write_memory */


/* *************************************************************************
 * twi_close_device
 * ************************************************************************* */
static void twi_close_device(struct twi_privdata *twi)
{
    if (twi->connected)
    {
        close(twi->fd);
    }

    twi->connected = 0;
} /* twi_close_device */


/* *************************************************************************
 * twi_open_device
 * ************************************************************************* */
static int twi_open_device(struct twi_privdata *twi)
{
    twi->fd = open(twi->device, O_RDWR);
    if (twi->fd < 0)
    {
        fprintf(stderr, "failed to open '%s': %s\n",
                twi->device, strerror(errno));

        return -1;
    }

    unsigned long funcs;
    if (ioctl(twi->fd, I2C_FUNCS, &funcs))
    {
        perror("ioctl(I2C_FUNCS)");
        close(twi->fd);
        return -1;
    }

    if (!(funcs & I2C_FUNC_I2C))
    {
        fprintf(stderr, "I2C_FUNC_I2C not supported on '%s'!\n",
                twi->device);

        close(twi->fd);
        return -1;
    }

    if (ioctl(twi->fd, I2C_SLAVE, twi->address) < 0)
    {
        fprintf(stderr, "failed to select slave address '%d': %s\n",
                twi->address, strerror(errno));

        close(twi->fd);
        return -1;
    }

    twi->connected = 1;
    return 0;
} /* twi_open_device */


/* *************************************************************************
 * twi_close
 * ************************************************************************* */
static int twi_close(struct multiboot *mboot)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;

    if (twi->connected && !twi->stay_in_bootloader)
    {
        twi_switch_application(twi, BOOTTYPE_APPLICATION);
    }

    twi_close_device(twi);
    return 0;
} /* twi_close */


/* *************************************************************************
 * twi_open
 * ************************************************************************* */
static int twi_open(struct multiboot *mboot)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;

    if (twi->address == 0)
    {
        fprintf(stderr, "abort: no address given\n");
        return -1;
    }

    if (twi->device == NULL)
    {
        twi->device = strdup(TWI_DEFAULT_DEVICE);
        if (twi->device == NULL)
        {
            perror("strdup()");
            return -1;
        }
    }

    if (twi_open_device(twi) != 0)
    {
        return -1;
    }

    if (twi_switch_application(twi, BOOTTYPE_BOOTLOADER))
    {
        fprintf(stderr, "failed to switch to bootloader (invalid address?): %s\n",
                strerror(errno));

        twi_close(mboot);
        return -1;
    }

    /* wait for watchdog and startup time */
    usleep(100000);

    char version[16 +1];
    if (twi_read_version(twi, version, sizeof(version) -1))
    {
        fprintf(stderr, "failed to get bootloader version: %s\n",
                strerror(errno));

        twi_close(mboot);
        return -1;
    }

    version[16] = '\0';

    uint8_t chipinfo[8];
    if (twi_read_memory(twi, chipinfo, sizeof(chipinfo), MEMTYPE_CHIPINFO, 0x0000))
    {
        fprintf(stderr, "failed to get chipinfo: %s\n", strerror(errno));
        twi_close(mboot);
        return -1;
    }

    const char *chipname = chipinfo_get_avr_name(chipinfo);

    twi->pagesize   = chipinfo[3];
    twi->flashsize  = (chipinfo[4] << 8) + chipinfo[5];
    twi->eepromsize = (chipinfo[6] << 8) + chipinfo[7];

    printf("device         : %-16s (address: 0x%02X)\n",
           twi->device, twi->address);

    printf("version        : %-16s (sig: 0x%02x 0x%02x 0x%02x => %s)\n",
           version, chipinfo[0], chipinfo[1], chipinfo[2], chipname);

    printf("flash size     : 0x%04x / %5d   (0x%02x bytes/page)\n",
           twi->flashsize, twi->flashsize, twi->pagesize);

    printf("eeprom size    : 0x%04x / %5d\n",
           twi->eepromsize, twi->eepromsize);

    return 0;
} /* twi_open */


/* *************************************************************************
 * twi_read
 * ************************************************************************* */
static int twi_read(struct multiboot *mboot,
                    struct databuf *dbuf,
                    int memtype)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "reading flash" : "reading eeprom";

    uint16_t pos = 0;
    uint16_t size = (memtype == MEMTYPE_FLASH) ? twi->flashsize : twi->eepromsize;

    while (pos < size)
    {
        mboot->progress_cb(progress_msg, pos, size);

        uint8_t len = MIN(READ_BLOCK_SIZE, size - pos);

        if (twi_read_memory(twi, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, size);
    return 0;
} /* twi_read */


/* *************************************************************************
 * twi_write
 * ************************************************************************* */
static int twi_write(struct multiboot *mboot,
                     struct databuf *dbuf,
                     int memtype)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "writing flash" : "writing eeprom";

    uint16_t pos = 0;
    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint8_t len = (memtype == MEMTYPE_FLASH) ? twi->pagesize : WRITE_BLOCK_SIZE;

        len = MIN(len, dbuf->length - pos);

        if (twi_write_memory(twi, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    mboot->progress_cb(progress_msg, pos, dbuf->length);
    return 0;
} /* twi_write */


/* *************************************************************************
 * twi_verify
 * ************************************************************************* */
static int twi_verify(struct multiboot *mboot, struct databuf *dbuf, int memtype)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "verifing flash" : "verifing eeprom";

    uint16_t pos = 0;
    uint8_t comp[READ_BLOCK_SIZE];

    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        int len = MIN(READ_BLOCK_SIZE, dbuf->length - pos);
        if (twi_read_memory(twi, comp, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        if (memcmp(comp, dbuf->data + pos, len) != 0x00)
        {
            mboot->progress_cb(progress_msg, -1, -1);
            fprintf(stderr, "verify failed at page 0x%04x!!\n", pos);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, dbuf->length);
    return 0;
} /* twi_verify */


/* *************************************************************************
 * twi_optarg_cb
 * ************************************************************************* */
static int twi_optarg_cb(int val, const char *arg, void *privdata)
{
    struct twi_privdata *twi = (struct twi_privdata *)privdata;

    switch (val)
    {
        case 'a': /* address */
            {
                char *endptr;

                twi->address = strtol(arg, &endptr, 16);
                if (*endptr != '\0' || twi->address < 0x01 || twi->address > 0x7F)
                {
                    fprintf(stderr, "invalid address: '%s'\n", arg);
                    return -1;
                }
            }
            break;

        case 'd': /* device */
            if (twi->device != NULL)
            {
                fprintf(stderr, "invalid device: '%s'\n", optarg);
                return -1;
            }

            twi->device = strdup(optarg);
            if (twi->device == NULL)
            {
                perror("strdup()");
                return -1;
            }
            break;

        case 's': /* stay in bootloader */
            twi->stay_in_bootloader = 1;
            break;

        case 'h':
        case '?': /* error */
                fprintf(stderr, "Usage: twiboot [options]\n"
                    "  -a <address>                 - selects i2c address (0x01 - 0x7F)\n"
                    "  -d <device>                  - selects i2c device  (default: /dev/i2c-0)\n"
                    "  -s                           - stay in bootloader afterwards\n"
                    "  -r <flash|eeprom>:<file>     - reads flash/eeprom to file   (.bin | .hex | -)\n"
                    "  -w <flash|eeprom>:<file>     - write flash/eeprom from file (.bin | .hex)\n"
                    "  -n                           - disable verify after write\n"
                    "  -p <0|1|2>                   - progress bar mode\n"
                    "\n"
                    "Example: twiboot -a 0x22 -w flash:blmc.hex -w eeprom:blmc_eeprom.hex\n"
                    "\n");
                return -1;

        default:
            return 1;
    }

    return 0;
} /* twi_optarg_cb */


/* *************************************************************************
 * twi_alloc
 * ************************************************************************* */
static struct multiboot * twi_alloc(void)
{
    struct multiboot * mboot = malloc(sizeof(struct multiboot));
    if (mboot == NULL)
    {
        return NULL;
    }

    memset(mboot, 0x00, sizeof(struct multiboot));
    mboot->ops  = &twi_ops;

    struct twi_privdata *twi = malloc(sizeof(struct twi_privdata));
    if (twi == NULL)
    {
        free(mboot);
        return NULL;
    }

    memset(twi, 0x00, sizeof(struct twi_privdata));
    twi->device  = NULL;
    twi->address = 0;

    optarg_register(twi_optargs, ARRAY_SIZE(twi_optargs), twi_optarg_cb, (void *)twi);

    mboot->privdata = twi;
    return mboot;
} /* twi_alloc */


/* *************************************************************************
 * twi_free
 * ************************************************************************* */
static void twi_free(struct multiboot *mboot)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;

    if (twi->device != NULL)
    {
        free(twi->device);
    }

    free(twi);
    free(mboot);
} /* twi_free */


/* *************************************************************************
 * twi_get_memtype
 * ************************************************************************* */
static int twi_get_memtype(struct multiboot *mboot,
                           const char *memname)
{
    /* unused parameter */
    (void)mboot;

    if (strcmp(memname, "flash") == 0)
    {
        return MEMTYPE_FLASH;
    }
    else if (strcmp(memname, "eeprom") == 0)
    {
        return MEMTYPE_EEPROM;
    }

    return -1;
} /* twi_get_memtype */


/* *************************************************************************
 * twi_get_memsize
 * ************************************************************************* */
static uint32_t twi_get_memsize(struct multiboot *mboot,
                                int memtype)
{
    struct twi_privdata *twi = (struct twi_privdata *)mboot->privdata;

    if (!twi->connected)
    {
        return 0;
    }

    switch (memtype)
    {
        case MEMTYPE_FLASH:
            return twi->flashsize;

        case MEMTYPE_EEPROM:
            return twi->eepromsize;

        default:
            return 0;
    }
} /* twi_get_memsize */


struct multiboot_ops twi_ops =
{
    .exec_name      = "twiboot",
    .alloc          = twi_alloc,
    .free           = twi_free,
    .get_memtype    = twi_get_memtype,
    .get_memsize    = twi_get_memsize,

    .open           = twi_open,
    .close          = twi_close,
    .read           = twi_read,
    .write          = twi_write,
    .verify         = twi_verify,
};
