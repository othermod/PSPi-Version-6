/***************************************************************************
 *   Copyright (C) 01/2020 by Olaf Rempel                                  *
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
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/time.h>

#include "chipinfo_avr.h"
#include "multiboot.h"
#include "optarg.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

#define SERIAL_BAUDRATE         B115200
#define SERIAL_TIMEOUT          1000

#define WRITE_SIZE_EEPROM       16

struct multiboot_ops butterfly_ops;

typedef struct bfly_privdata_s
{
    char            * p_device;
    struct termios  oldtio;
    int             fd;

    uint8_t         twi_address;
    uint8_t         chip_erase;
    uint8_t         stay_in_bootloader;

    uint16_t        buffersize;
    uint16_t        flashsize;
    uint16_t        eepromsize;

    uint8_t         progmode_active;
} bfly_privdata_t;

static struct option bfly_optargs[] =
{
    { "address",    1, 0, 'a' },    /* [ -a <address ]      */
    { "device",     1, 0, 'd' },    /* -d <device>          */
    { "erase",      0, 0, 'e' },    /* [ -e ]               */
    { "stay",       0, 0, 's' },    /* [ -s ]               */
};

/* *************************************************************************
 * bfly_optarg_cb
 * ************************************************************************* */
static int bfly_optarg_cb(int val, const char *arg, void *privdata)
{
    bfly_privdata_t * p_priv;

    p_priv = (bfly_privdata_t *)privdata;

    switch (val)
    {
        case 'a': /* address */
            {
                char *endptr;

                p_priv->twi_address = strtol(arg, &endptr, 16);
                if ((*endptr != '\0') ||
                    (p_priv->twi_address < 0x01) ||
                    (p_priv->twi_address > 0x7F)
                   )
                {
                    fprintf(stderr, "invalid address: '%s'\n", arg);
                    return -1;
                }
            }
            break;

        case 'd': /* device */
            if (p_priv->p_device != NULL)
            {
                fprintf(stderr, "invalid device: '%s'\n", arg);
                return -1;
            }

            p_priv->p_device = strdup(optarg);
            if (p_priv->p_device == NULL)
            {
                perror("strdup()");
                return -1;
            }
            break;

        case 'e': /* chip erase */
            p_priv->chip_erase = 1;
            break;

        case 's': /* stay in bootloader */
            p_priv->stay_in_bootloader = 1;
            break;

        case 'h':
        case '?': /* error */
            fprintf(stderr, "Usage: butterfly_prog [options]\n"
            "  -a <address>                 - optional: twi address for twiboot bridge mode\n"
            "  -d <device>                  - selects butterfly serial device\n"
            "  -e                           - executes a chip erase\n"
            "  -s                           - stay in bootloader afterwards\n"
            "  -r <flash|eeprom>:<file>     - reads flash/eeprom to file   (.bin | .hex | -)\n"
            "  -w <flash|eeprom>:<file>     - write flash/eeprom from file (.bin | .hex)\n"
            "  -n                           - disable verify after write\n"
            "  -p <0|1|2>                   - progress bar mode\n"
            "\n"
            "Example: butterfly_prog -d /dev/ttyUSB0 -w flash:code.hex\n"
            "\n");

            return -1;

        default:
            return 1;
    }

    return 0;
} /* bfly_optarg_cb */


/* *************************************************************************
 * butterfly_alloc
 * ************************************************************************* */
static struct multiboot * butterfly_alloc(void)
{
    struct multiboot * mboot = malloc(sizeof(struct multiboot));
    if (mboot == NULL)
    {
        return NULL;
    }

    memset(mboot, 0x00, sizeof(struct multiboot));
    mboot->ops= &butterfly_ops;

    bfly_privdata_t * p_priv = malloc(sizeof(bfly_privdata_t));
    if (p_priv == NULL)
    {
        free(mboot);
        return NULL;
    }

    memset(p_priv, 0x00, sizeof(bfly_privdata_t));

    optarg_register(bfly_optargs, ARRAY_SIZE(bfly_optargs),
                    bfly_optarg_cb, (void *)p_priv);

    mboot->privdata = p_priv;
    return mboot;
} /* butterfly_alloc */


/* *************************************************************************
 * butterfly_free
 * ************************************************************************* */
static void butterfly_free(struct multiboot * p_mboot)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;

    if (p_priv->p_device != NULL)
    {
        free(p_priv->p_device);
    }

    free(p_priv);
    free(p_mboot);
} /* butterfly_free */


/* *************************************************************************
 * butterfly_get_memtype
 * ************************************************************************* */
static int butterfly_get_memtype(struct multiboot * p_mboot,
                                 const char * p_memname)
{
    /* unused parameter */
    (void)p_mboot;

    if (strcmp(p_memname, "flash") == 0)
    {
        return 'F';
    }
    else if (strcmp(p_memname, "eeprom") == 0)
    {
        return 'E';
    }

    return -1;
} /* butterfly_get_memtype */


/* *************************************************************************
 * butterfly_get_memsize
 * ************************************************************************* */
static uint32_t butterfly_get_memsize(struct multiboot * p_mboot,
                                      int memtype)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;

    if (!p_priv->progmode_active)
    {
        return 0;
    }

    switch (memtype)
    {
        case 'F':
            return p_priv->flashsize;

        case 'E':
            return p_priv->eepromsize;

        default:
            return 0;
    }
} /* butterfly_get_memsize */


/* *************************************************************************
 * butterfly_close_device
 * ************************************************************************* */
static void butterfly_close_device(bfly_privdata_t * p_priv)
{
    tcsetattr(p_priv->fd, TCSANOW, &p_priv->oldtio);
    close(p_priv->fd);
} /* butterfly_close_device */


/* *************************************************************************
 * butterlfy_open_device
 * ************************************************************************* */
static int butterfly_open_device(bfly_privdata_t * p_priv)
{
    p_priv->fd = open(p_priv->p_device, O_RDWR | O_NOCTTY | O_CLOEXEC);
    if (p_priv->fd < 0)
    {
        perror("open()");
        return -1;
    }

    if (tcgetattr(p_priv->fd, &p_priv->oldtio) < 0)
    {
        perror("tcgetattr(oldtio)");
        close(p_priv->fd);
        return -1;
    }

    struct termios newtio;
    memset(&newtio, 0, sizeof(newtio));

    newtio.c_iflag = IGNBRK;
    newtio.c_cflag = (CS8 | CREAD | CLOCAL);
    cfsetispeed(&newtio, SERIAL_BAUDRATE);
    cfsetospeed(&newtio, SERIAL_BAUDRATE);
    newtio.c_cc[VMIN] = 1;
    newtio.c_cc[VTIME] = 0;

    int err = tcsetattr(p_priv->fd, TCSANOW, &newtio);
    if (err < 0)
    {
        perror("tcsetattr(newtio)");
        close(p_priv->fd);
        return -1;
    }

    /* needed for some slow USB2Serial adapters */
    usleep(200000);

    return 0;
} /* butterlfy_open_device */


/* *************************************************************************
 * butterfly_serial_read
 * ************************************************************************* */
static int butterfly_serial_read(int fd, void * data, int size,
                                 unsigned int timeout_ms)
{
    int pos = 0;

    while (1)
    {
        fd_set fdset;
        struct timeval timeout;
        struct timeval * p_timeout = NULL;

        FD_ZERO(&fdset);
        FD_SET(fd, &fdset);

        if (timeout_ms != 0)
        {
            p_timeout = &timeout;

            timeout.tv_sec = timeout_ms / 1000;
            timeout.tv_usec = (timeout_ms % 1000) * 1000;
        }

        int ret = select(fd +1, &fdset, NULL, NULL, p_timeout);
        if (ret == -1)
        {
            perror("select");
            return -1;
        }
        else if (ret == 0)
        {
            break;
        }
        else if (FD_ISSET(fd, &fdset))
        {
            int len = read(fd, data + pos, size - pos);
            if (len < 0)
            {
                return -1;
            }
            else
            {
                pos += len;
                if (pos == size)
                {
                    break;
                }
            }
        }
    }

    return pos;
} /* butterfly_serial_read */


/* *************************************************************************
 * butterfly_expect_cr
 * ************************************************************************* */
static int butterfly_expect_cr(bfly_privdata_t * p_priv)
{
    uint8_t buffer[1];
    int result;

    result = butterfly_serial_read(p_priv->fd, buffer, sizeof(buffer),
                                   SERIAL_TIMEOUT);
    if ((result == sizeof(buffer)) &&
        (buffer[0] == '\r')
       )
    {
        return 0;
    }

    return -1;
} /* butterfly_expect_cr */


/* *************************************************************************
 * butterfly_enter_progmode
 * ************************************************************************* */
static int butterfly_enter_progmode(bfly_privdata_t * p_priv)
{
    if (p_priv->twi_address == 0x00)
    {
        (void)write(p_priv->fd, "P", 1);
    }
    else
    {
        uint8_t cmd[2] = { 'I' , p_priv->twi_address };
        (void)write(p_priv->fd, cmd, 2);
    }

    return butterfly_expect_cr(p_priv);
} /* butterfly_enter_progmode */


/* *************************************************************************
 * butterfly_leave_progmode
 * ************************************************************************* */
static int butterfly_leave_progmode(bfly_privdata_t * p_priv)
{
    if (p_priv->stay_in_bootloader)
    {
        /* Leave programming mode */
        (void)write(p_priv->fd, "L", 1);
    }
    else
    {
        /* Exit Bootloader */
        (void)write(p_priv->fd, "E", 1);
    }

    return butterfly_expect_cr(p_priv);
} /* butterfly_leave_progmode */


/* *************************************************************************
 * butterfly_get_signature
 * ************************************************************************* */
static int butterfly_get_signature(bfly_privdata_t * p_priv,
                                   uint8_t * p_signature)
{
    int result;
    uint8_t buffer[3];

    (void)write(p_priv->fd, "s", 1);

    result = butterfly_serial_read(p_priv->fd, buffer, sizeof(buffer),
                                   SERIAL_TIMEOUT);

    if (result == 3)
    {
        p_signature[0] = buffer[2];
        p_signature[1] = buffer[1];
        p_signature[2] = buffer[0];
        return 0;
    }

    return -1;
} /* butterfly_get_signature */


/* *************************************************************************
 * butterfly_get_buffersize
 * ************************************************************************* */
static int butterfly_get_buffersize(bfly_privdata_t * p_priv,
                                    uint16_t * p_buffersize)
{
    int result;
    uint8_t buffer[3];

    (void)write(p_priv->fd, "b", 1);

    result = butterfly_serial_read(p_priv->fd, buffer, sizeof(buffer),
                                   SERIAL_TIMEOUT);
    if (result == sizeof(buffer))
    {
        if (buffer[0] == 'Y')
        {
            *p_buffersize = (buffer[1] << 8) | buffer[2];
        }
        else
        {
            *p_buffersize = 0;
        }
    }

    return (result != sizeof(buffer));
} /* butterfly_get_buffersize */


/* *************************************************************************
 * butterfly_chiperase
 * ************************************************************************* */
static int butterfly_chiperase(bfly_privdata_t * p_priv)
{
    (void)write(p_priv->fd, "e", 1);

    return butterfly_expect_cr(p_priv);
} /* butterfly_chiperase */


/* *************************************************************************
 * butterfly_set_address
 * ************************************************************************* */
static int butterfly_set_address(bfly_privdata_t * p_priv, uint16_t pos)
{
    uint8_t buffer[1];
    int result;

    (void)write(p_priv->fd, "a", 1);

    result = butterfly_serial_read(p_priv->fd, buffer, sizeof(buffer),
                                   SERIAL_TIMEOUT);
    if ((result == 1) &&
        (buffer[0] == 'Y')
       )
    {
        /* convert to word address */
        pos >>= 1;

        uint8_t cmd[3] = { 'A', pos >> 8, pos & 0xFF };
        (void)write(p_priv->fd, cmd, sizeof(cmd));

        result = butterfly_expect_cr(p_priv);
    }

    return result;
} /* butterfly_set_address */


/* *************************************************************************
 * butterfly_read_data
 * ************************************************************************* */
static int butterfly_read_data(bfly_privdata_t * p_priv,
                               uint8_t * p_data, uint16_t size,
                               uint8_t memtype)
{
    int result;

    uint8_t cmd[4] = { 'g', size >> 8, size & 0xFF, memtype };
    (void)write(p_priv->fd, cmd, 4);

    result = butterfly_serial_read(p_priv->fd, p_data, size,
                                   SERIAL_TIMEOUT);
    return (result != size);
} /* butterfly_read_data */


/* *************************************************************************
 * butterfly_write_data
 * ************************************************************************* */
static int butterfly_write_data(bfly_privdata_t * p_priv,
                                const uint8_t * p_data, uint16_t size,
                                uint8_t memtype)
{
    uint8_t cmd[4] = { 'B', size >> 8, size & 0xFF, memtype };
    (void)write(p_priv->fd, cmd, 4);

    (void)write(p_priv->fd, p_data, size);

    return butterfly_expect_cr(p_priv);
} /* butterfly_write_data */


/* *************************************************************************
 * butterfly_close
 * ************************************************************************* */
static int butterfly_close(struct multiboot * p_mboot)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;

    if (p_priv->progmode_active)
    {
        butterfly_leave_progmode(p_priv);
    }

    butterfly_close_device(p_priv);

    return 0;
} /* butterfly_close */


/* *************************************************************************
 * butterfly_open
 * ************************************************************************* */
static int butterfly_open(struct multiboot * p_mboot)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;

    if (p_priv->p_device == NULL)
    {
        fprintf(stderr, "abort: no device given\n");
        return -1;
    }

    if (butterfly_open_device(p_priv) < 0)
    {
        return -1;
    }

    if (butterfly_enter_progmode(p_priv) != 0)
    {
        fprintf(stderr, "failed to enter progmode\n");
        butterfly_close_device(p_priv);
        return -1;
    }

    p_priv->progmode_active = 1;

    uint8_t signature[3];
    if (butterfly_get_signature(p_priv, signature) != 0)
    {
        fprintf(stderr, "failed to get signature\n");
        butterfly_close_device(p_priv);
        return -1;
    }

    const avr_chipinfo_t * p_chipinfo;
    p_chipinfo = chipinfo_get_by_signature(signature);
    if (p_chipinfo == NULL)
    {
        fprintf(stderr, "failed to identify chip signature [0x%02x 0x%02x 0x%02x]\n",
                signature[0], signature[1], signature[2]);
        butterfly_close_device(p_priv);
        return -1;
    }

    p_priv->flashsize   = p_chipinfo->flashsize;
    p_priv->eepromsize  = p_chipinfo->eepromsize;

    if (butterfly_get_buffersize(p_priv, &p_priv->buffersize) != 0)
    {
        fprintf(stderr, "failed to get buffersize\n");
        butterfly_close_device(p_priv);
        return -1;
    }

    if (p_priv->twi_address != 0x00)
    {
        printf("twi address    : 0x%02x\n",
               p_priv->twi_address);
    }

    printf("device         : %-16s (sig: 0x%02x 0x%02x 0x%02x)\n",
           p_chipinfo->name, p_chipinfo->sig[0],
           p_chipinfo->sig[1], p_chipinfo->sig[2]);

    printf("flash size     : 0x%04x / %5d\n",
           p_chipinfo->flashsize, p_chipinfo->flashsize);

    printf("eeprom size    : 0x%04x / %5d\n",
           p_chipinfo->eepromsize, p_chipinfo->eepromsize);

    if (p_priv->chip_erase)
    {
        if (butterfly_chiperase(p_priv) != 0)
        {
            fprintf(stderr, "failed to chip erase\n");
            butterfly_close_device(p_priv);
            return -1;
        }

        printf("chip erased    : OK\n");
    }

    return 0;
} /* butterfly_open */


/* *************************************************************************
 * butterfly_read
 * ************************************************************************* */
static int butterfly_read(struct multiboot * p_mboot,
                          struct databuf * p_dbuf,
                          int memtype)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;
    char * p_progress_msg = (memtype == 'F') ? "reading flash" : "reading eeprom";

    uint16_t pos = 0;
    uint16_t size = (memtype == 'F') ? p_priv->flashsize :
                                       p_priv->eepromsize;

    if (butterfly_set_address(p_priv, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < size)
    {
        p_mboot->progress_cb(p_progress_msg, pos, size);

        uint16_t len = MIN(p_priv->buffersize, size - pos);
        if (butterfly_read_data(p_priv, p_dbuf->data + pos, len, memtype))
        {
            p_mboot->progress_cb(p_progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    p_dbuf->length = pos;

    p_mboot->progress_cb(p_progress_msg, pos, size);
    return 0;
} /* butterfly_read */


/* *************************************************************************
 * butterfly_write
 * ************************************************************************* */
static int butterfly_write(struct multiboot * p_mboot,
                           struct databuf * p_dbuf,
                           int memtype)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;
    char * p_progress_msg = (memtype == 'F') ? "writing flash" : "writing eeprom";

    uint16_t pos = 0;

    if (butterfly_set_address(p_priv, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < p_dbuf->length)
    {
        p_mboot->progress_cb(p_progress_msg, pos, p_dbuf->length);

        uint16_t len = (memtype == 'F') ? p_priv->buffersize : WRITE_SIZE_EEPROM;

        len = MIN(len, p_dbuf->length - pos);

        if (butterfly_write_data(p_priv, p_dbuf->data + pos, len, memtype))
        {
            p_mboot->progress_cb(p_progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    p_mboot->progress_cb(p_progress_msg, pos, p_dbuf->length);
    return 0;
} /* butterfly_write */


/* *************************************************************************
 * butterfly_verify
 * ************************************************************************* */
static int butterfly_verify(struct multiboot * p_mboot,
                            struct databuf * p_dbuf,
                            int memtype)
{
    bfly_privdata_t * p_priv = (bfly_privdata_t *)p_mboot->privdata;
    char * p_progress_msg = (memtype == 'F') ? "verifing flash" : "verifing eeprom";

    uint16_t pos = 0;
    uint8_t comp[256];

    if (butterfly_set_address(p_priv, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < p_dbuf->length)
    {
        p_mboot->progress_cb(p_progress_msg, pos, p_dbuf->length);

        uint16_t len = MIN(p_priv->buffersize, p_dbuf->length - pos);
        if (butterfly_read_data(p_priv, comp, len, memtype))
        {
            p_mboot->progress_cb(p_progress_msg, -1, -1);
            return -1;
        }

        if (memcmp(comp, p_dbuf->data + pos, len) != 0x00)
        {
            p_mboot->progress_cb(p_progress_msg, -1, -1);
            fprintf(stderr, "verify failed at pos 0x%04x!!\n", pos);
            return -1;
        }

        pos += len;
    }

    p_dbuf->length = pos;

    p_mboot->progress_cb(p_progress_msg, pos, p_dbuf->length);
    return 0;
} /* butterfly_verify */


struct multiboot_ops butterfly_ops =
{
    .exec_name      = "butterfly_prog",
    .alloc          = butterfly_alloc,
    .free           = butterfly_free,
    .get_memtype    = butterfly_get_memtype,
    .get_memsize    = butterfly_get_memsize,

    .open           = butterfly_open,
    .close          = butterfly_close,
    .read           = butterfly_read,
    .write          = butterfly_write,
    .verify         = butterfly_verify,
};
