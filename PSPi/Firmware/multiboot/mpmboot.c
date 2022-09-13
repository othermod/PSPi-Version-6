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

#define READ_BLOCK_SIZE             256 /* bytes in one flash/eeprom read request */
#define WRITE_BLOCK_SIZE             16 /* bytes in one eeprom write request */

#define CMD_SWITCH_APPLICATION      0x01
#define CMD_GET_BOOTLOADER_VERSION  0x02
#define CMD_GET_CHIP_INFO           0x03
#define CMD_READ_MEMORY             0x11
#define CMD_WRITE_MEMORY            0x12

#define CAUSE_SUCCESS               0x00
#define CAUSE_COMMAND_NOT_SUPPORTED 0xF0
#define CAUSE_INVALID_PARAMETER     0xF1
#define CAUSE_UNSPECIFIED_ERROR     0xFF

/* CMD_SWITCH_APPLICATION parameter */
#define BOOTTYPE_BOOTLOADER         0x00
#define BOOTTYPE_APPLICATION        0x80

#define MEMTYPE_FLASH               0x01
#define MEMTYPE_EEPROM              0x02

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

struct multiboot_ops mpm_ops;

struct mpm_privdata
{
    char *device;
    int fd;
    int connected;

    uint8_t address;

    uint16_t flashsize;
    uint8_t flashpage;
    uint16_t eepromsize;

    struct termios oldtio;
};

static struct option mpm_optargs[] =
{
    { "address",    1, 0, 'a'}, /* -a <addr>            */
    { "device",     1, 0, 'd'}, /* [ -d <device> ]      */
};


/* *************************************************************************
 * mpm_optarg_cb
 * ************************************************************************* */
static int mpm_optarg_cb(int val, const char *arg, void *privdata)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)privdata;

    switch (val)
    {
        case 'a': /* address */
            {
                char *endptr;
                mpm->address = strtol(arg, &endptr, 16);

                if (*endptr != '\0' || mpm->address < 0x01 || mpm->address > 0x7F)
                {
                    fprintf(stderr, "invalid address: '%s'\n", arg);
                    return -1;
                }
            }
            break;

        case 'd': /* device */
            if (mpm->device != NULL)
            {
                fprintf(stderr, "invalid device: '%s'\n", optarg);
                return -1;
            }

            mpm->device = strdup(optarg);
            if (mpm->device == NULL)
            {
                perror("strdup()");
                return -1;
            }
            break;

        case 'h':
        case '?': /* error */
            fprintf(stderr, "Usage: mpmboot [options]\n"
                "  -a <address>                 - selects mpm address (0x01 - 0xFF)\n"
                "  -d <device>                  - selects mpm device\n"
                "  -r <flash|eeprom>:<file>     - reads flash/eeprom to file   (.bin | .hex | -)\n"
                "  -w <flash|eeprom>:<file>     - write flash/eeprom from file (.bin | .hex)\n"
                "  -n                           - disable verify after write\n"
                "  -p <0|1|2>                   - progress bar mode\n"
                "\n"
                "Example: mpmboot -d /dev/ttyUSB0 -a 0x22 -w flash:blmc.hex -w eeprom:blmc_eeprom.hex\n"
                "\n");

            return -1;

        default:
            return 1;
    }

    return 0;
} /* mpm_optarg_cb */


/* *************************************************************************
 * mpm_alloc
 * ************************************************************************* */
static struct multiboot * mpm_alloc(void)
{
    struct multiboot * mboot = malloc(sizeof(struct multiboot));
    if (mboot == NULL)
    {
        return NULL;
    }

    memset(mboot, 0x00, sizeof(struct multiboot));
    mboot->ops  = &mpm_ops;

    struct mpm_privdata *mpm = malloc(sizeof(struct mpm_privdata));
    if (mpm == NULL)
    {
        free(mboot);
        return NULL;
    }

    memset(mpm, 0x00, sizeof(struct mpm_privdata));
    mpm->device  = NULL;
    mpm->address = 0;

    optarg_register(mpm_optargs, ARRAY_SIZE(mpm_optargs),
                    mpm_optarg_cb, (void *)mpm);

    mboot->privdata = mpm;
    return mboot;
} /* mpm_alloc */


/* *************************************************************************
 * mpm_free
 * ************************************************************************* */
static void mpm_free(struct multiboot *mboot)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;

    if (mpm->device != NULL)
    {
        free(mpm->device);
    }

    free(mpm);
    free(mboot);
} /* mpm_free */


/* *************************************************************************
 * mpm_get_memtype
 * ************************************************************************* */
static int mpm_get_memtype(struct multiboot *mboot,
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
} /* mpm_get_memtype */


/* *************************************************************************
 * mpm_get_memsize
 * ************************************************************************* */
static uint32_t mpm_get_memsize(struct multiboot *mboot, int memtype)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;

    if (!mpm->connected)
    {
        return 0;
    }

    switch (memtype)
    {
        case MEMTYPE_FLASH:
            return mpm->flashsize;

        case MEMTYPE_EEPROM:
            return mpm->eepromsize;

        default:
            return 0;
    }
} /* mpm_get_memsize */


/* *************************************************************************
 * mpm_send
 * ************************************************************************* */
static int mpm_send(struct mpm_privdata *mpm, uint8_t command,
                    uint8_t *data, uint16_t length)
{
    struct termios tio;

    if (tcgetattr(mpm->fd, &tio) < 0)
    {
        perror("tcgetattr(tio)");
        return -1;
    }

    tio.c_cflag |= PARODD;

    if (tcsetattr(mpm->fd, TCSAFLUSH, &tio) < 0)
    {
        perror("tcsetattr(tio)");
        return -1;
    }

//     usleep(5000);

    uint8_t address = mpm->address;
    if (write(mpm->fd, &address, sizeof(address)) != sizeof(address))
    {
        perror("write(address)");
        return -1;
    }

    usleep(500);

    tio.c_cflag &= ~(PARODD);

    if (tcsetattr(mpm->fd, TCSAFLUSH, &tio) < 0)
    {
        perror("tcsetattr(tio)");
        return -1;
    }

    uint8_t header[3];
    header[0] = command;
    header[1] = (length >> 8) & 0xFF;
    header[2] = length & 0xFF;

    if (write(mpm->fd, header, sizeof(header)) != sizeof(header))
    {
        perror("write(header)");
        return -1;
    }

    if (data != NULL && length != 0)
    {
        if (write(mpm->fd, data, length) != length)
        {
            perror("write(data)");
            return -1;
        }
    }

    return 0;
} /* mpm_send */


/* *************************************************************************
 * mpm_serial_read
 * ************************************************************************* */
static int mpm_serial_read(int fd, void *data, int size)
{
    int pos = 0;

    while (1)
    {
        fd_set fdset;
        struct timeval timeout = { .tv_sec = 1, .tv_usec = 0 };

        FD_ZERO(&fdset);
        FD_SET(fd, &fdset);

        int ret = select(fd +1, &fdset, NULL, NULL, &timeout);
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
} /* mpm_serial_read */


/* *************************************************************************
 * mpm_recv
 * ************************************************************************* */
static int mpm_recv(struct mpm_privdata *mpm,
                    uint8_t command,
                    uint8_t *cause,
                    uint8_t *buffer,
                    uint16_t buffersize)
{
    int     len;
    uint8_t header[4];

    len = mpm_serial_read(mpm->fd, header, sizeof(header));
    if (len != sizeof(header))
    {
        fprintf(stderr, "short read() from device (not addressed?)\n");
        return -1;
    }

    if (header[0] != command)
    {
        fprintf(stderr, "invalid command response (0x%02x != 0x%02x)\n", header[0], command);
        return -1;
    }

    *cause = header[1];

    uint16_t length = (header[2] << 8) | header[3];
//     printf("mpm_recv() cmd=0x%02x cause=0x%02x length=0x%04x\n", command, *cause, length);

    uint16_t bufferpos = 0;
    while (length > 0)
    {

        /* free space in output buffer? */
        if ((bufferpos < buffersize) && (buffer != NULL))
        {
            uint16_t size = MIN(buffersize - bufferpos, length);

            len = mpm_serial_read(mpm->fd, buffer + bufferpos, size);
            if (len <= 0)
            {
                fprintf(stderr, "short read() from device (%d != %d)\n", len, size);
                return -1;
            }

            bufferpos += len;
            length    -= len;
        }
        else
        {
            uint8_t dummy[256];

            /* no space in output buffer, but device still sends data -> do dummy read */
            uint16_t size = MIN(sizeof(dummy), length);

            len = mpm_serial_read(mpm->fd, dummy, size);
            if (len <= 0)
            {
                fprintf(stderr, "short read() from device (%d != %d)\n", len, size);
                return -1;
            }

            length -= len;
        }
    }

    return bufferpos;
} /* mpm_recv */


/* *************************************************************************
 * mpm_close_device
 * ************************************************************************* */
static void mpm_close_device(struct mpm_privdata *mpm)
{
    /* delay close() / tcsetattr() */
    usleep(100000);

    tcsetattr(mpm->fd, TCSANOW, &mpm->oldtio);
    close(mpm->fd);
} /* mpm_close_device */


/* *************************************************************************
 * mpm_open_device
 * ************************************************************************* */
static int mpm_open_device(struct mpm_privdata *mpm)
{
    mpm->fd = open(mpm->device, O_RDWR | O_NOCTTY | O_CLOEXEC);
    if (mpm->fd < 0)
    {
        perror("open()");
        return -1;
    }

    if (tcgetattr(mpm->fd, &mpm->oldtio) < 0)
    {
        perror("tcgetattr(oldtio)");
        close(mpm->fd);
        return -1;
    }

    struct termios newtio;
    memset(&newtio, 0, sizeof(newtio));

    newtio.c_iflag |= IGNBRK;
    newtio.c_cflag |= B115200 | CS8 | CLOCAL | CREAD | PARENB | CMSPAR;

    newtio.c_cc[VMIN] = 1;
    newtio.c_cc[VTIME] = 0;

    int err = tcsetattr(mpm->fd, TCSANOW, &newtio);
    if (err < 0)
    {
        perror("tcsetattr(newtio)");
        close(mpm->fd);
        return -1;
    }

    mpm->connected = 1;
    return 0;
} /* mpm_open_device */


/* *************************************************************************
 * mpm_switch_application
 * ************************************************************************* */
static int mpm_switch_application(struct mpm_privdata *mpm,
                                  uint8_t application)
{
    uint8_t data[] = { application };

    int ret = mpm_send(mpm, CMD_SWITCH_APPLICATION, data, sizeof(data));
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = CAUSE_SUCCESS;
    ret = mpm_recv(mpm, CMD_SWITCH_APPLICATION, &cause, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return (cause != CAUSE_SUCCESS);
} /* mpm_switch_application */


/* *************************************************************************
 * mpm_read_version
 * ************************************************************************* */
static int mpm_read_version(struct mpm_privdata *mpm,
                            uint8_t *version, uint16_t length)
{
    memset(version, 0, length);

    int ret = mpm_send(mpm, CMD_GET_BOOTLOADER_VERSION, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = CAUSE_SUCCESS;
    ret = mpm_recv(mpm, CMD_GET_BOOTLOADER_VERSION, &cause, version, length);
    if (ret < 0)
    {
        return ret;
    }

    int i;
    for (i = 0; i < length; i++)
    {
        version[i] &= ~0x80;
    }

    return (cause != CAUSE_SUCCESS);
}


/* *************************************************************************
 * mpm_read_chipinfo
 * ************************************************************************* */
static int mpm_read_chipinfo(struct mpm_privdata *mpm,
                             uint8_t *chipinfo, uint16_t length)
{
    int ret = mpm_send(mpm, CMD_GET_CHIP_INFO, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = CAUSE_SUCCESS;
    ret = mpm_recv(mpm, CMD_GET_CHIP_INFO, &cause, chipinfo, length);
    if (ret < 0)
    {
        return ret;
    }

    return (cause != CAUSE_SUCCESS);
} /* mpm_read_chipinfo */


/* *************************************************************************
 * mpm_read_memory
 * ************************************************************************* */
static int mpm_read_memory(struct mpm_privdata *mpm,
                           uint8_t *buffer, uint16_t size,
                           uint8_t memtype, uint16_t address)
{
    uint8_t param[5] = {
        memtype,
        (address >> 8) & 0xFF,
        (address & 0xFF),
        (size >> 8) & 0xFF,
        (size & 0xFF)
    };

    int ret = mpm_send(mpm, CMD_READ_MEMORY, param, sizeof(param));
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = CAUSE_SUCCESS;
    ret = mpm_recv(mpm, CMD_READ_MEMORY, &cause, buffer, size);
    if (ret < 0)
    {
        return ret;
    }

    return (cause != CAUSE_SUCCESS);
} /* mpm_read_memory */


/* *************************************************************************
 * mpm_write_memory
 * ************************************************************************* */
static int mpm_write_memory(struct mpm_privdata *mpm,
                            uint8_t *buffer, uint16_t size,
                            uint8_t memtype, uint16_t address)
{
    int bufsize;

    if (memtype == MEMTYPE_FLASH)
    {
        if ((address & (mpm->flashpage -1)) != 0x00)
        {
            fprintf(stderr, "mpm_write_memory(): address 0x%04x not aligned to pagesize 0x%02x\n", address, mpm->flashpage);
            return -1;
        }

        bufsize = 5 + mpm->flashpage;

    }
    else
    {
        bufsize = 5 + size;
    }

    uint8_t *cmd = malloc(bufsize);
    if (cmd == NULL)
    {
        return -1;
    }

    cmd[0] = memtype;
    cmd[1] = (address >> 8) & 0xFF;
    cmd[2] = (address & 0xFF);
    cmd[3] = ((bufsize -5) >> 8) & 0xFF;
    cmd[4] = ((bufsize -5) & 0xFF);
    memcpy(cmd +5, buffer, size);

    if (memtype == MEMTYPE_FLASH)
    {
        memset(cmd +5 +size, 0xFF, mpm->flashpage - size);
    }

    int ret = mpm_send(mpm, CMD_WRITE_MEMORY, cmd, bufsize);
    if (ret < 0)
    {
        return ret;
    }

    free(cmd);

    uint8_t cause = CAUSE_SUCCESS;
    ret = mpm_recv(mpm, CMD_WRITE_MEMORY, &cause, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return (cause != CAUSE_SUCCESS);
} /* mpm_write_memory */


/* *************************************************************************
 * mpm_close
 * ************************************************************************* */
static int mpm_close(struct multiboot *mboot)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;

    if (mpm->connected)
    {
        mpm_switch_application(mpm, BOOTTYPE_APPLICATION);
    }

    mpm_close_device(mpm);
    return 0;
} /* mpm_close */


/* *************************************************************************
 * mpm_open
 * ************************************************************************* */
static int mpm_open(struct multiboot *mboot)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;

    if (mpm->address == 0)
    {
        fprintf(stderr, "abort: no address given\n");
        return -1;
    }

    if (mpm->device == NULL)
    {
        fprintf(stderr, "abort: no device given\n");
        return -1;
    }

    if (mpm_open_device(mpm) < 0)
    {
        return -1;
    }

    if (mpm_switch_application(mpm, BOOTTYPE_BOOTLOADER))
    {
        fprintf(stderr, "failed to switch to bootloader (invalid address?)\n");
        mpm_close(mboot);
        return -1;
    }

    /* wait for watchdog and startup time */
    usleep(100000);

    char version[16 +1];
    if (mpm_read_version(mpm, (uint8_t *)version, sizeof(version) -1))
    {
        fprintf(stderr, "failed to get bootloader version\n");
        mpm_close(mboot);
        return -1;
    }

    version[16] = '\0';

    uint8_t chipinfo[8];
    if (mpm_read_chipinfo(mpm, chipinfo, sizeof(chipinfo)))
    {
        fprintf(stderr, "failed to get bootloader version\n");
        mpm_close(mboot);
        return -1;
    }

    const char *chipname = chipinfo_get_avr_name(chipinfo);

    mpm->flashpage  = chipinfo[3];
    mpm->flashsize  = (chipinfo[4] << 8) + chipinfo[5];
    mpm->eepromsize = (chipinfo[6] << 8) + chipinfo[7];

    printf("device         : %-16s (address: 0x%02X)\n",
           mpm->device, mpm->address);

    printf("version        : %-16s (sig: 0x%02x 0x%02x 0x%02x => %s)\n",
           version, chipinfo[0], chipinfo[1], chipinfo[2], chipname);

    printf("flash size     : 0x%04x / %5d   (0x%02x bytes/page)\n",
           mpm->flashsize, mpm->flashsize, mpm->flashpage);

    printf("eeprom size    : 0x%04x / %5d\n",
           mpm->eepromsize, mpm->eepromsize);

    return 0;
} /* mpm_open */


/* *************************************************************************
 * mpm_read
 * ************************************************************************* */
static int mpm_read(struct multiboot *mboot,
                    struct databuf *dbuf, int memtype)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "reading flash" : "reading eeprom";

    uint16_t pos = 0;
    uint16_t size = (memtype == MEMTYPE_FLASH) ? mpm->flashsize : mpm->eepromsize;

    while (pos < size)
    {
        mboot->progress_cb(progress_msg, pos, size);

        uint16_t len = MIN(READ_BLOCK_SIZE, size - pos);
        if (mpm_read_memory(mpm, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, size);
    return 0;
} /* mpm_read */


/* *************************************************************************
 * mpm_write
 * ************************************************************************* */
static int mpm_write(struct multiboot *mboot,
                     struct databuf *dbuf, int memtype)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "writing flash" : "writing eeprom";

    uint16_t pos = 0;
    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint16_t len = (memtype == MEMTYPE_FLASH) ? mpm->flashpage : WRITE_BLOCK_SIZE;

        len = MIN(len, dbuf->length - pos);
        if (mpm_write_memory(mpm, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    mboot->progress_cb(progress_msg, pos, dbuf->length);
    return 0;
} /* mpm_write */


/* *************************************************************************
 * mpm_verify
 * ************************************************************************* */
static int mpm_verify(struct multiboot *mboot,
                      struct databuf *dbuf, int memtype)
{
    struct mpm_privdata *mpm = (struct mpm_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "verifing flash" : "verifing eeprom";

    uint16_t pos = 0;
    uint8_t comp[READ_BLOCK_SIZE];

    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint16_t len = MIN(READ_BLOCK_SIZE, dbuf->length - pos);
        if (mpm_read_memory(mpm, comp, len, memtype, pos))
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
} /* mpm_verify */


struct multiboot_ops mpm_ops =
{
    .exec_name      = "mpmboot",
    .alloc          = mpm_alloc,
    .free           = mpm_free,
    .get_memtype    = mpm_get_memtype,
    .get_memsize    = mpm_get_memsize,

    .open           = mpm_open,
    .close          = mpm_close,
    .read           = mpm_read,
    .write          = mpm_write,
    .verify         = mpm_verify,
};
