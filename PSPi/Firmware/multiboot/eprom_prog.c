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

#include "multiboot.h"
#include "optarg.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

#define MEMTYPE_EPROM           1

#define SERIAL_BAUDRATE         B115200
#define SERIAL_TIMEOUT          1000
#define SERIAL_TIMEOUT_SYNC     5

#define MSGTYPE_SYNC            0x00    /* trigger { MSGTYPE_ERROR_RSP, 1, ERROR_UNKNOWN_COMMAND } */
#define MSGTYPE_VERSION_REQ     0x01    /* no payload */
#define MSGTYPE_PAGESIZE_REQ    0x02    /* no payload */
#define MSGTYPE_CONFIG_REQ      0x03    /* eprom_type(1), pagesize(1), reset_polarity(1) */
#define MSGTYPE_PROGMODE_REQ    0x04    /* progmode(1) */
#define MSGTYPE_SETADDRESS_REQ  0x05    /* address(3) msb first */
#define MSGTYPE_WRITE_REQ       0x06    /* data(0-pagesize) */
#define MSGTYPE_READ_REQ        0x07    /* length(1) */

#define MSGTYPE_ERROR_RSP       0x80    /* error_code(1) */
#define MSGTYPE_VERSION_RSP     0x81    /* version(?) */
#define MSGTYPE_PAGESIZE_RSP    0x82    /* pagesize(1) */
#define MSGTYPE_CONFIG_RSP      0x83    /* no payload */
#define MSGTYPE_PROGMODE_RSP    0x84    /* no payload */
#define MSGTYPE_SETADDRESS_RSP  0x85    /* no payload */
#define MSGTYPE_WRITE_RSP       0x86    /* no payload */
#define MSGTYPE_READ_RSP        0x87    /* data(0-pagesize) */

#define SUCCESS                 0x00
#define ERROR_UNKNOWN_COMMAND   0x01    /* unknown message type */
#define ERROR_NOT_SUPPORTED     0x02    /* command not supported */
#define ERROR_INVALID_MODE      0x03    /* invalid progmode */
#define ERROR_INVALID_PARAMETER 0x04    /* invalid parameter in request */
#define ERROR_INVALID_ADDRESS   0x05    /* write outside of configured region */

#define RESET_POLARITY_LOW      0x00    /* low active reset */
#define RESET_POLARITY_HIGH     0x01    /* high active reset */

#define EPROM_TYPE_2K           0x02    /* 2716 */
#define EPROM_TYPE_4K           0x04    /* 2732 */
#define EPROM_TYPE_8K           0x08    /* 2764 */
#define EPROM_TYPE_16K          0x10    /* 27128 */
#define EPROM_TYPE_32K          0x20    /* 27256 */
#define EPROM_TYPE_64K          0x40    /* 27512 */
#define EPROM_TYPE_128K         0x80    /* 27010 */

#define PROGMODE_DISABLED       0x00    /* target running, no write access to RAM */
#define PROGMODE_ENABLED        0x01    /* target reset, write access to RAM */


struct multiboot_ops eprog_ops;

struct eprog_privdata
{
    char            * device;
    struct termios  oldtio;
    int             fd;

    uint8_t         version[32];
    uint8_t         pagesize_max;

    uint8_t         eprom_type;
    uint8_t         pagesize;
    int             reset_polarity;

    uint8_t         progmode;
};

struct eprog_type
{
    const char      name[8];
    uint8_t         eprom_type;
    uint8_t         pagesize;
};

static struct eprog_type eprom_types[] =
{
    { "2716",   EPROM_TYPE_2K,      0xFF },
    { "2732",   EPROM_TYPE_4K,      0xFF },
    { "2764",   EPROM_TYPE_8K,      0xFF },
    { "2864",   EPROM_TYPE_8K,      0x40 },
    { "27128",  EPROM_TYPE_16K,     0xFF },
    { "27256",  EPROM_TYPE_32K,     0xFF },
    { "27512",  EPROM_TYPE_64K,     0xFF },
    { "27010",  EPROM_TYPE_128K,    0xFF },
};

static struct option eprog_optargs[] =
{
    { "device",     1, 0, 'd' },    /* [ -d <device> ]      */
    { "reset",      1, 0, 'x' },    /* [ -x <reset polarity> ]        */
    { "type",       1, 0, 't' },    /* [ -t <type> ]        */
};

/* *************************************************************************
 * eprog_optarg_cb
 * ************************************************************************* */
static int eprog_optarg_cb(int val, const char *arg, void *privdata)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)privdata;

    switch (val)
    {
        case 'd': /* device */
            if (p_prog->device != NULL)
            {
                fprintf(stderr, "invalid device: '%s'\n", arg);
                return -1;
            }

            p_prog->device = strdup(optarg);
            if (p_prog->device == NULL)
            {
                perror("strdup()");
                return -1;
            }
            break;

        case 'x':
            if (strcasecmp(arg, "high") == 0)
            {
                p_prog->reset_polarity = RESET_POLARITY_HIGH;
            }
            else if (strcasecmp(arg, "low") == 0)
            {
                p_prog->reset_polarity = RESET_POLARITY_LOW;
            }
            else
            {
                fprintf(stderr, "invalid reset polarity: '%s'\n", arg);
                return -1;
            }
            break;

        case 't':
            {
                unsigned int i;

                if (p_prog->eprom_type != 0)
                {
                    fprintf(stderr, "invalid EPROM type: '%s'\n", arg);
                    return -1;
                }

                for (i = 0; i < ARRAY_SIZE(eprom_types); i++)
                {
                    if (strcmp(arg, eprom_types[i].name) == 0)
                    {
                        p_prog->eprom_type  = eprom_types[i].eprom_type;
                        p_prog->pagesize    = eprom_types[i].pagesize;
                    }
                }

                if (p_prog->eprom_type == 0)
                {
                    fprintf(stderr, "invalid EPROM type: '%s'\n", arg);
                    return -1;
                }
            }
            break;

        case 'h':
        case '?': /* error */
            fprintf(stderr, "Usage: eprom_sim [options]\n"
            "  -d <device>                  - selects eprom_sim device\n"
            "  -x <reset polarity>          - select 'high' or 'low' active reset\n"
            "  -t <type>                    - selects EPROM type (2716 - 27010)\n"
            "  -r eprom:<file>              - reads EPROM to file   (.bin | .hex | -)\n"
            "  -w eprom:<file>              - write EPROM from file (.bin | .hex)\n"
            "  -p <0|1|2>                   - progress bar mode\n"
            "\n"
            "Example: eprom_sim -d /dev/ttyUSB0 -t 2764 -r high -w eprom:data.hex\n"
            "\n");

            return -1;

        default:
            return 1;
    }

    return 0;
} /* eprog_optarg_cb */


/* *************************************************************************
 * eprog_alloc
 * ************************************************************************* */
static struct multiboot * eprog_alloc(void)
{
    struct multiboot * mboot = malloc(sizeof(struct multiboot));
    if (mboot == NULL)
    {
        return NULL;
    }

    memset(mboot, 0x00, sizeof(struct multiboot));
    mboot->ops= &eprog_ops;

    struct eprog_privdata *p_prog = malloc(sizeof(struct eprog_privdata));
    if (p_prog == NULL)
    {
        free(mboot);
        return NULL;
    }

    memset(p_prog, 0x00, sizeof(struct eprog_privdata));
    p_prog->device = NULL;

    optarg_register(eprog_optargs, ARRAY_SIZE(eprog_optargs),
                    eprog_optarg_cb, (void *)p_prog);

    mboot->privdata = p_prog;
    return mboot;
} /* eprog_alloc */


/* *************************************************************************
 * eprog_free
 * ************************************************************************* */
static void eprog_free(struct multiboot *mboot)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;

    if (p_prog->device != NULL)
    {
        free(p_prog->device);
    }

    free(p_prog);
    free(mboot);
} /* eprog_free */


/* *************************************************************************
 * eprog_get_memtype
 * ************************************************************************* */
static int eprog_get_memtype(struct multiboot *mboot,
                                const char *memname)
{
    /* unused parameter */
    (void)mboot;

    if (strcmp(memname, "eprom") == 0)
    {
        return MEMTYPE_EPROM;
    }

    return -1;
} /* eprog_get_memtype */


/* *************************************************************************
 * eprog_get_memsize
 * ************************************************************************* */
static uint32_t eprog_get_memsize(struct multiboot *mboot,
                                  int memtype)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;

    if (memtype != MEMTYPE_EPROM)
    {
        return 0;
    }

    return p_prog->eprom_type * 1024;
} /* eprog_get_memsize */


/* *************************************************************************
 * eprog_close_device
 * ************************************************************************* */
static void eprog_close_device(struct eprog_privdata *p_prog)
{
    /* delay close() / tcsetattr() */
    usleep(100000);

    tcsetattr(p_prog->fd, TCSANOW, &p_prog->oldtio);
    close(p_prog->fd);
} /* eprog_close_device */


/* *************************************************************************
 * eprog_open_device
 * ************************************************************************* */
static int eprog_open_device(struct eprog_privdata *p_prog)
{
    p_prog->fd = open(p_prog->device, O_RDWR | O_NOCTTY | O_CLOEXEC);
    if (p_prog->fd < 0)
    {
        perror("open()");
        return -1;
    }

    if (tcgetattr(p_prog->fd, &p_prog->oldtio) < 0)
    {
        perror("tcgetattr(oldtio)");
        close(p_prog->fd);
        return -1;
    }

    struct termios newtio;
    memset(&newtio, 0, sizeof(newtio));

    newtio.c_iflag |= IGNBRK;
    newtio.c_cflag |= SERIAL_BAUDRATE | CS8 | CLOCAL | CREAD;

    newtio.c_cc[VMIN] = 1;
    newtio.c_cc[VTIME] = 0;

    int err = tcsetattr(p_prog->fd, TCSANOW, &newtio);
    if (err < 0)
    {
        perror("tcsetattr(newtio)");
        close(p_prog->fd);
        return -1;
    }

    return 0;
} /* eprog_open_device */


/* *************************************************************************
 * eprog_serial_read
 * ************************************************************************* */
static int eprog_serial_read(int fd, void * data, int size, unsigned int timeout_ms)
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
} /* eprog_serial_read */


/* *************************************************************************
 * eprog_recv
 * ************************************************************************* */
static int eprog_recv(int fd, uint8_t msgtype, uint8_t * data, uint8_t length)
{
    uint8_t header[2];
    uint8_t dummy[64];

    int ret = eprog_serial_read(fd, header, sizeof(header), SERIAL_TIMEOUT);
    if (ret < (int)sizeof(header))
    {
        fprintf(stderr, "short read from device (header)\n");
        return -1;
    }

    uint8_t pos = 0;
    uint8_t msgsize = header[1];

    while (msgsize > 0)
    {
        if ((data != NULL) && (pos < length))
        {
            uint8_t readsize = MIN(msgsize, length - pos);

            ret = eprog_serial_read(fd, &data[pos], readsize, SERIAL_TIMEOUT);
            if (ret <= 0)
            {
                fprintf(stderr, "short read from device (payload)\n");
                return -1;
            }

            pos += ret;
        }
        else
        {
            uint8_t readsize = MIN(msgsize, sizeof(dummy));

            ret = eprog_serial_read(fd, &dummy, readsize, SERIAL_TIMEOUT);
            if (ret <= 0)
            {
                fprintf(stderr, "short read from device (dummy)\n");
                return -1;
            }
        }

        msgsize -= ret;
    }

    if (header[0] != msgtype)
    {
        if ((header[0] == MSGTYPE_ERROR_RSP) && (header[1] == 1))
        {
            uint8_t error_code = (data != NULL) ? data[0] : dummy[0];

            fprintf(stderr, "expected msgtype 0x%x received ERROR_RSP error_code 0x%x\n",
                    msgtype, error_code);
        }
        else
        {
            fprintf(stderr, "wrong msgtype received (0x%x != 0x%x)\n",
                    header[0], msgtype);
        }

        return -1;
    }

    return pos;
} /* eprog_recv */


/* *************************************************************************
 * eprog_sync
 * ************************************************************************* */
static int eprog_sync(struct eprog_privdata *p_prog)
{
    int sync_count = 255;

    while (sync_count > 0)
    {
        /* send only MSGTYPE, no request length! */
        uint8_t request[] = { MSGTYPE_SYNC };
        uint8_t response[3];

        int ret = write(p_prog->fd, request, sizeof(request));
        if (ret <= 0)
        {
            return ret;
        }

        ret = eprog_serial_read(p_prog->fd, response, sizeof(response), SERIAL_TIMEOUT_SYNC);
        if ((ret == sizeof(response)) &&
            (response[0] == MSGTYPE_ERROR_RSP) &&
            (response[1] == 1) &&
            (response[2] == ERROR_UNKNOWN_COMMAND)
           )
        {
           return 0;
        }

        sync_count--;
    }

    return -1;
} /* eprog_sync */


/* *************************************************************************
 * eprog_get_version
 * ************************************************************************* */
static int eprog_get_version(struct eprog_privdata *p_prog,
                             uint8_t *version, uint8_t length)
{
    uint8_t request[] = { MSGTYPE_VERSION_REQ, 0 };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_VERSION_RSP, version, length);
    if (ret <= 0)
    {
        return -1;
    }

    if (ret < length)
    {
        version[ret] = '\0';
    }
    else
    {
        version[length -1] = '\0';
    }

    return 0;
} /* eprog_get_version */


/* *************************************************************************
 * eprog_get_pagesize
 * ************************************************************************* */
static int eprog_get_pagesize(struct eprog_privdata *p_prog,
                              uint8_t *pagesize)
{
    uint8_t request[] = { MSGTYPE_PAGESIZE_REQ, 0 };
    uint8_t response[1];

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_PAGESIZE_RSP, response, sizeof(response));
    if (ret != sizeof(response))
    {
        return -1;
    }

    *pagesize = response[0];

    return 0;
} /* eprog_get_pagesize */


/* *************************************************************************
 * eprog_set_config
 * ************************************************************************* */
static int eprog_set_config(struct eprog_privdata *p_prog,
                            uint8_t eprom_type,
                            uint8_t pagesize,
                            uint8_t reset_polarity)
{
    uint8_t request[] = { MSGTYPE_CONFIG_REQ, 3, eprom_type, pagesize, reset_polarity };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_CONFIG_RSP, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return 0;
} /* eprog_set_config */


/* *************************************************************************
 * eprog_set_progmode
 * ************************************************************************* */
static int eprog_set_progmode(struct eprog_privdata *p_prog,
                              uint8_t progmode)
{
    uint8_t request[] = { MSGTYPE_PROGMODE_REQ, 1, progmode };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_PROGMODE_RSP, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return 0;
} /* eprog_set_progmode */


/* *************************************************************************
 * eprog_set_address
 * ************************************************************************* */
static int eprog_set_address(struct eprog_privdata *p_prog,
                             uint32_t address)
{
    uint8_t request[] = { MSGTYPE_SETADDRESS_REQ, 3,
                          (address >> 16) & 0xFF,
                          (address >> 8) & 0xFF,
                          (address >> 0) & 0xFF };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_SETADDRESS_RSP, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return 0;
} /* eprog_set_address */


/* *************************************************************************
 * eprog_read_data
 * ************************************************************************* */
static int eprog_read_data(struct eprog_privdata *p_prog,
                           uint8_t * data,
                           uint8_t length)
{
    uint8_t request[] = { MSGTYPE_READ_REQ, 1, length };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_READ_RSP, data, length);
    if (ret < 0)
    {
        return ret;
    }

    return 0;
} /* eprog_read_data */


/* *************************************************************************
 * eprog_write_data
 * ************************************************************************* */
static int eprog_write_data(struct eprog_privdata *p_prog,
                            const uint8_t * data,
                            uint8_t length)
{
    uint8_t request[] = { MSGTYPE_WRITE_REQ, length };

    int ret = write(p_prog->fd, request, sizeof(request));
    if (ret <= 0)
    {
        return ret;
    }

    ret = write(p_prog->fd, data, length);
    if (ret <= 0)
    {
        return ret;
    }

    ret = eprog_recv(p_prog->fd, MSGTYPE_WRITE_RSP, NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    return 0;
} /* eprog_write_data */


/* *************************************************************************
 * eprog_close
 * ************************************************************************* */
static int eprog_close(struct multiboot *mboot)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;

    if (p_prog->progmode == PROGMODE_ENABLED)
    {
        eprog_set_progmode(p_prog, PROGMODE_DISABLED);
    }

    eprog_close_device(p_prog);

    return 0;
} /* eprog_close */


/* *************************************************************************
 * eprog_open
 * ************************************************************************* */
static int eprog_open(struct multiboot *mboot)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;

    if (p_prog->device == NULL)
    {
        fprintf(stderr, "abort: no device given\n");
        return -1;
    }

    if (p_prog->eprom_type == 0)
    {
        fprintf(stderr, "abort: no EPROM type given\n");
        return -1;
    }

    if (eprog_open_device(p_prog) < 0)
    {
        return -1;
    }

    if (eprog_sync(p_prog) < 0)
    {
        fprintf(stderr, "failed to sync\n");
        eprog_close_device(p_prog);
        return -1;
    }

    if (eprog_get_version(p_prog, p_prog->version, sizeof(p_prog->version)) < 0)
    {
        fprintf(stderr, "failed to get version\n");
        eprog_close_device(p_prog);
        return -1;
    }

    if ((eprog_get_pagesize(p_prog, &p_prog->pagesize_max) < 0) ||
        (p_prog->pagesize_max == 0)
       )
    {
        fprintf(stderr, "failed to get pagesize\n");
        eprog_close_device(p_prog);
        return -1;
    }

    p_prog->pagesize = MIN(p_prog->pagesize, p_prog->pagesize_max);
    if (eprog_set_config(p_prog, p_prog->eprom_type, p_prog->pagesize, p_prog->reset_polarity) < 0)
    {
        fprintf(stderr, "failed to set configuration\n");
        eprog_close_device(p_prog);
        return -1;
    }

    if (eprog_set_progmode(p_prog, PROGMODE_ENABLED) < 0)
    {
        fprintf(stderr, "failed to enter progmode\n");
        eprog_close_device(p_prog);
        return -1;
    }

    p_prog->progmode = PROGMODE_ENABLED;

    printf("device         : %-16s\n",
           p_prog->device);

    printf("version        : %-32s\n",
           p_prog->version);

    printf("reset polarity : %-4s\n",
           p_prog->reset_polarity ? "high" : "low");

    printf("EPROM size     : 0x%05x (%d)\n",
           p_prog->eprom_type * 1024,
           p_prog->eprom_type * 1024);

    return 0;
} /* eprog_open */


/* *************************************************************************
 * eprog_read
 * ************************************************************************* */
static int eprog_read(struct multiboot *mboot,
                      struct databuf *dbuf, int memtype)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;
    char *progress_msg = "reading EPROM";

    /* unused parameter */
    (void)memtype;

    uint32_t pos = 0;
    uint32_t size = p_prog->eprom_type * 1024;

    if (eprog_set_address(p_prog, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < size)
    {
        mboot->progress_cb(progress_msg, pos, size);

        uint8_t len = MIN(p_prog->pagesize_max, size - pos);
        if (eprog_read_data(p_prog, dbuf->data + pos, len))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, size);
    return 0;
} /* eprog_read */


/* *************************************************************************
 * eprog_write
 * ************************************************************************* */
static int eprog_write(struct multiboot *mboot,
                       struct databuf *dbuf,
                       int memtype)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;
    char *progress_msg = "writing EPROM";

    /* unused parameter */
    (void)memtype;

    uint32_t pos = 0;

    if (eprog_set_address(p_prog, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint8_t len = MIN(p_prog->pagesize, dbuf->length - pos);
        if (eprog_write_data(p_prog, dbuf->data + pos, len))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    mboot->progress_cb(progress_msg, pos, dbuf->length);

    return 0;
} /* eprog_write */


/* *************************************************************************
 * eprog_verify
 * ************************************************************************* */
static int eprog_verify(struct multiboot *mboot,
                       struct databuf *dbuf, int memtype)
{
    struct eprog_privdata *p_prog = (struct eprog_privdata *)mboot->privdata;
    char *progress_msg = "verifing EPROM";

    /* unused parameter */
    (void)memtype;

    uint32_t pos = 0;
    uint8_t comp[256];

    if (eprog_set_address(p_prog, pos) < 0)
    {
        fprintf(stderr, "failed to set address\n");
        return -1;
    }

    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint8_t len = MIN(p_prog->pagesize, dbuf->length - pos);
        if (eprog_read_data(p_prog, comp, len))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        if (memcmp(comp, dbuf->data + pos, len) != 0x00)
        {
            mboot->progress_cb(progress_msg, -1, -1);
            fprintf(stderr, "verify failed at pos 0x%04x!!\n", pos);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, dbuf->length);
    return 0;
} /* eprog_verify */


struct multiboot_ops eprog_ops =
{
    .exec_name      = "eprom_prog",
    .alloc          = eprog_alloc,
    .free           = eprog_free,
    .get_memtype    = eprog_get_memtype,
    .get_memsize    = eprog_get_memsize,

    .open           = eprog_open,
    .close          = eprog_close,
    .read           = eprog_read,
    .write          = eprog_write,
    .verify         = eprog_verify,
};
