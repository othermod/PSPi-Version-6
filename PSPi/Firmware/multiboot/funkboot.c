#include <stdio.h>
#include <stdlib.h>
#include <stddef.h> /* offsetof */
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

#define FUNK_BRIDGE_DEBUG           0
#define FUNK_PACKET_DEBUG           0

/* *********************************************************************** */

#define BRIDGE_CMD_TRANSMIT             'T'
#define BRIDGE_CMD_RECEIVE              'R'
#define BRIDGE_CMD_VERSION              'V'

#define BRIDGE_CAUSE_SUCCESS            0x00
#define BRIDGE_CAUSE_TIMEOUT            0x01
#define BRIDGE_CAUSE_NOT_SUPPORTED      0xF0
#define BRIDGE_CAUSE_INVALID_PARAMETER  0xF1
#define BRIDGE_CAUSE_UNSPECIFIED_ERROR  0xFF

/* *********************************************************************** */

#define MSG_TYPE_REQUEST                0x00    /* master -> slave req */
#define MSG_TYPE_CONFIRMATION           0x40    /* master -> slave rsp */
#define MSG_TYPE_INDICATION             0x80    /* slave -> master req */
#define MSG_TYPE_RESPONSE               0xC0    /* slave -> master rsp */
#define MSG_TYPE_MASK                   0xC0
#define MSG_CMD_MASK                    0x3F

#define MSG_CMD_SWITCHAPP_REQUEST       (MSG_TYPE_REQUEST       | 0x20)
#define MSG_CMD_SWITCHAPP_RESPONSE      (MSG_TYPE_RESPONSE      | 0x20)

#define MSG_CMD_VERSION_REQUEST         (MSG_TYPE_REQUEST       | 0x21)
#define MSG_CMD_VERSION_RESPONSE        (MSG_TYPE_RESPONSE      | 0x21)

#define MSG_CMD_CHIPINFO_REQUEST        (MSG_TYPE_REQUEST       | 0x22)
#define MSG_CMD_CHIPINFO_RESPONSE       (MSG_TYPE_RESPONSE      | 0x22)

#define MSG_CMD_READ_REQUEST            (MSG_TYPE_REQUEST       | 0x23)
#define MSG_CMD_READ_RESPONSE           (MSG_TYPE_RESPONSE      | 0x23)

#define MSG_CMD_WRITE_REQUEST           (MSG_TYPE_REQUEST       | 0x24)
#define MSG_CMD_WRITE_RESPONSE          (MSG_TYPE_RESPONSE      | 0x24)

#define CAUSE_SUCCESS                   0x00

#define BOOTTYPE_BOOTLOADER             0x00
#define BOOTTYPE_APPLICATION            0x80

#define MEMTYPE_FLASH                   0x01
#define MEMTYPE_EEPROM                  0x02

/* *********************************************************************** */

struct bootloader_msg
{
    uint8_t command;
    uint8_t seqnum;
    uint8_t cause;

    union {
        struct {
            uint8_t     app;
        } switchapp;

        struct {
            uint8_t     data[16];
        } version;

        struct {
            uint8_t     data[8];
        } chipinfo;

        struct {
            uint16_t    address;
            uint8_t     mem_type;
            uint8_t     size;
        } read_req;

        struct {
            uint8_t     data[32];
        } read_rsp;

        struct {
            uint16_t    address;
            uint8_t     mem_type;
            uint8_t     size;
            uint8_t     data[32];
        } write_req;
    } p;
} __attribute__ ((__packed__));

struct rfm12_pkt
{
    uint8_t dest_address;
    uint8_t source_address;
    uint8_t data_length;
    uint8_t header_checksum;

    struct bootloader_msg msg;
} __attribute__ ((__packed__));

/* *********************************************************************** */

#define READ_BLOCK_SIZE                 32 /* bytes in one flash/eeprom read request */
#define WRITE_BLOCK_SIZE                32 /* bytes in one eeprom write request */

/* *********************************************************************** */

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*x))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

struct multiboot_ops funk_ops;

struct funk_privdata
{
    char *device;
    int fd;
    int connected;

    int address;
    int src_address;
    int seqnum;

    int flashsize;
    int flashpage;
    int eepromsize;

    struct termios oldtio;
};


static struct option funk_optargs[] =
{
    { "address",    1, 0, 'a'}, /* -a <addr>            */
    { "device",     1, 0, 'd'}, /* [ -d <device> ]      */
};


/* *************************************************************************
 * funk_optarg_cb
 * ************************************************************************* */
static int funk_optarg_cb(int val, const char *arg, void *privdata)
{
    struct funk_privdata *funk = (struct funk_privdata *)privdata;

    switch (val)
    {
        case 'a': /* address */
            {
                char *endptr;

                funk->address = strtol(arg, &endptr, 16);
                if (*endptr != '\0' || funk->address < 0x00 || funk->address > 0xFF) {
                    fprintf(stderr, "invalid address: '%s'\n", arg);
                    return -1;
                }
            }
            break;

        case 'd': /* device */
            if (funk->device != NULL) {
                fprintf(stderr, "invalid device: '%s'\n", optarg);
                return -1;
            }

            funk->device = strdup(optarg);
            if (funk->device == NULL) {
                perror("strdup()");
                return -1;
            }
            break;

        case 'h':
        case '?': /* error */
            fprintf(stderr, "Usage: funkboot [options]\n"
                "  -a <address>                 - selects rfm12 address (0x00 - 0xFF)\n"
                "  -d <device>                  - selects funkbridge device\n"
                "  -r <flash|eeprom>:<file>     - reads flash/eeprom to file   (.bin | .hex | -)\n"
                "  -w <flash|eeprom>:<file>     - write flash/eeprom from file (.bin | .hex)\n"
                "  -n                           - disable verify after write\n"
                "  -p <0|1|2>                   - progress bar mode\n"
                "\n"
                "Example: funkboot -d /dev/ttyUSB0 -a 0x22 -w flash:blmc.hex -w eeprom:blmc_eeprom.hex\n"
                "\n");
            return -1;

        default:
            return 1;
    }

    return 0;
} /* funk_optarg_cb */


/* *************************************************************************
 * funk_alloc
 * ************************************************************************* */
static struct multiboot * funk_alloc(void)
{
    struct multiboot * mboot = malloc(sizeof(struct multiboot));
    if (mboot == NULL)
    {
        return NULL;
    }

    memset(mboot, 0x00, sizeof(struct multiboot));
    mboot->ops = &funk_ops;

    struct funk_privdata *funk = malloc(sizeof(struct funk_privdata));
    if (funk == NULL)
    {
        free(mboot);
        return NULL;
    }

    memset(funk, 0x00, sizeof(struct funk_privdata));
    funk->device = NULL;
    funk->address = 0;

    optarg_register(funk_optargs, ARRAY_SIZE(funk_optargs), funk_optarg_cb, (void *)funk);

    mboot->privdata = funk;
    return mboot;
} /* funk_alloc */


/* *************************************************************************
 * funk_free
 * ************************************************************************* */
static void funk_free(struct multiboot *mboot)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;

    if (funk->device != NULL)
    {
        free(funk->device);
    }

    free(funk);
    free(mboot);
} /* funk_free */


/* *************************************************************************
 * funk_get_memtype
 * ************************************************************************* */
static int funk_get_memtype(struct multiboot *mboot,
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
} /* funk_get_memtype */


/* *************************************************************************
 * funk_get_memsize
 * ************************************************************************* */
static uint32_t funk_get_memsize(struct multiboot *mboot,
                                 int memtype)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;

    if (!funk->connected)
    {
        return 0;
    }

    switch (memtype)
    {
        case MEMTYPE_FLASH:
            return funk->flashsize;

        case MEMTYPE_EEPROM:
            return funk->eepromsize;

        default:
            return 0;
    }
} /* funk_get_memsize */


/* *************************************************************************
 * funk_serial_read
 * ************************************************************************* */
static int funk_serial_read(int fd, void *data, int size)
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
} /* funk_serial_read */


#if (FUNK_BRIDGE_DEBUG == 1) || (FUNK_PACKET_DEBUG == 1)
/* *************************************************************************
 * funk_print_data
 * ************************************************************************* */
static char * funk_print_data(uint8_t *data, uint16_t length)
{
    int pos = 0, i = 0, j;
    char *buf = malloc(length * 4 + 64);

    while (pos < length)
    {
        i += sprintf(buf + i, "%04X: ", pos);
        for (j = 0; j < 16; j++)
        {
            if (pos + j < length)
            {
                i += sprintf(buf + i, "%02X", data[pos + j]);
            }
            else
            {
                i += sprintf(buf + i, "  ");
                if (j % 2)
                {
                    buf[i++] = ' ';
                }
            }

        for (j = 0; j < 16; j++)
        {
            if (pos + j < length)
            {
                unsigned char val = data[pos + j];
                if (val >= 0x20 && val < 0x80)
                {
                    buf[i++] = val;
                }
                else
                {
                    buf[i++] = '.';
                }
            }
            else
            {
                buf[i++] = ' ';
            }
        }

        pos += 16;
        buf[i++] = '\r';
        buf[i++] = '\n';
    }

    buf[i] = 0;
    return buf;
} /* funk_print_data */
#endif


/* *************************************************************************
 * funk_bridge_send
 * ************************************************************************* */
static int funk_bridge_send(struct funk_privdata *funk,
                            uint8_t *header,
                            uint8_t headerlength,
                            uint8_t *data,
                            uint8_t datalength)
{
    if (headerlength > 0)
    {
        if (write(funk->fd, header, headerlength) != headerlength)
        {
            return -1;
        }
    }

    if (datalength > 0)
    {
        if (write(funk->fd, data, datalength) != datalength)
        {
            return -1;
        }
    }

#if (FUNK_BRIDGE_DEBUG == 1)
    char *dump = funk_print_data(data, datalength);
    printf("funk_bridge_send() cmd=0x%02x length=0x%02x\n%s\n", header[0], datalength, dump);
    free(dump);
#endif

    return 0;
} /* funk_bridge_send */


/* *************************************************************************
 * funk_bridge_recv
 * ************************************************************************* */
static int funk_bridge_recv(struct funk_privdata *funk,
                            uint8_t command,
                            uint8_t *cause,
                            uint8_t *buffer,
                            int buffersize)
{
    uint8_t response[3];
    int len;

    len = funk_serial_read(funk->fd, response, sizeof(response));
    if (len != sizeof(response))
    {
        fprintf(stderr, "short read() from device\n");
        return -1;
    }

    if (response[0] != command)
    {
        fprintf(stderr, "invalid command response (0x%02x != 0x%02x)\n",
                response[0], command);

        return -1;
    }

    *cause = response[1];
    uint16_t length = response[2];
    uint16_t bufferpos = 0;

    while (length > 0)
    {

        /* free space in output buffer? */
        if ((bufferpos < buffersize) && (buffer != NULL))
        {
            uint16_t size = MIN(buffersize - bufferpos, length);

            len = funk_serial_read(funk->fd, buffer + bufferpos, size);
            if (len <= 0)
            {
                fprintf(stderr, "short read() from device (%d != %d)\n",
                        len, size);

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

            len = funk_serial_read(funk->fd, dummy, size);
            if (len <= 0)
            {
                fprintf(stderr, "short read() from device (%d != %d)\n",
                        len, size);

                return -1;
            }

            length -= len;
        }
    }

#if (FUNK_BRIDGE_DEBUG == 1)
    char *dump = funk_print_data(buffer, bufferpos);
    printf("funk_bridge_recv() cmd=0x%02x cause=0x%02x length=0x%02x\n%s\n",
           command, *cause, length, dump);

    free(dump);
#endif

    return bufferpos;
} /* funk_bridge_recv */


/* *************************************************************************
 * funk_send_packet
 * ************************************************************************* */
static int funk_send_packet(struct funk_privdata *funk,
                            struct rfm12_pkt *pkt,
                            int length)
{
    uint8_t request[] = { BRIDGE_CMD_TRANSMIT, length };

    int ret = funk_bridge_send(funk, request, sizeof(request), (uint8_t *)pkt, length);
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = BRIDGE_CAUSE_SUCCESS;
    ret = funk_bridge_recv(funk, request[0], &cause, NULL, 0);
    if (ret != 0)
    {
        return -1;
    }

#if (FUNK_PACKET_DEBUG == 1)
    char *dump = funk_print_data((uint8_t *)pkt, length);
    printf("funk_send_packet() cause=0x%02x length=0x%02x\n%s\n",
           cause, length, dump);

    free(dump);
#endif

    return (cause != BRIDGE_CAUSE_SUCCESS);
} /* funk_send_packet */


/* *************************************************************************
 * funk_recv_packet
 * ************************************************************************* */
static int funk_recv_packet(struct funk_privdata *funk,
                            struct rfm12_pkt *pkt,
                            int *length)
{
    uint8_t request[] = { BRIDGE_CMD_RECEIVE, 0 };

    int ret = funk_bridge_send(funk, request, sizeof(request), NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = BRIDGE_CAUSE_SUCCESS;
    ret = funk_bridge_recv(funk, request[0], &cause, (uint8_t *)pkt, *length);
    if (ret < 0)
    {
        return -1;
    }

    *length = ret;

#if (FUNK_PACKET_DEBUG == 1)
    char *dump = funk_print_data((uint8_t *)pkt, *length);
    printf("funk_recv_packet() cause=0x%02x length=0x%02x\n%s\n", cause, *length, dump);
    free(dump);
#endif

    return (cause != BRIDGE_CAUSE_SUCCESS);
} /* funk_recv_packet */


/* *************************************************************************
 * funk_bridge_version
 * ************************************************************************* */
static int funk_bridge_version(struct funk_privdata *funk,
                               uint8_t *version,
                               int size)
{
    uint8_t request[] = { BRIDGE_CMD_VERSION, 0 };

    int ret = funk_bridge_send(funk, request, sizeof(request), NULL, 0);
    if (ret < 0)
    {
        return ret;
    }

    uint8_t cause = BRIDGE_CAUSE_SUCCESS;
    ret = funk_bridge_recv(funk, request[0], &cause, version, size);
    if (ret < 0)
    {
        return ret;
    }

    version[ret] = '\0';

    return (cause != BRIDGE_CAUSE_SUCCESS);
} /* funk_bridge_version */


/* *************************************************************************
 * funk_close_device
 * ************************************************************************* */
static void funk_close_device(struct funk_privdata *funk)
{
    /* delay close() / tcsetattr() */
    usleep(100000);

    tcsetattr(funk->fd, TCSANOW, &funk->oldtio);
    close(funk->fd);
} /* funk_close_device */


/* *************************************************************************
 * funk_open_device
 * ************************************************************************* */
static int funk_open_device(struct funk_privdata *funk)
{
    funk->fd = open(funk->device, O_RDWR | O_NOCTTY | O_CLOEXEC);
    if (funk->fd < 0)
    {
        perror("open()");
        return -1;
    }

    if (tcgetattr(funk->fd, &funk->oldtio) < 0)
    {
        perror("tcgetattr(oldtio)");
        close(funk->fd);
        return -1;
    }

    struct termios newtio;
    memset(&newtio, 0, sizeof(newtio));

    newtio.c_iflag |= IGNBRK;
    newtio.c_cflag |= B38400 | CS8 | CLOCAL | CREAD;

    newtio.c_cc[VMIN] = 1;
    newtio.c_cc[VTIME] = 0;

    int err = tcsetattr(funk->fd, TCSANOW, &newtio);
    if (err < 0)
    {
        perror("tcsetattr(newtio)");
        close(funk->fd);
        return -1;
    }

    funk->connected = 1;
    return 0;
} /* funk_open_device */


/* *************************************************************************
 * funk_switch_application
 * ************************************************************************* */
static int funk_switch_application(struct funk_privdata *funk,
                                   uint8_t application)
{
    struct rfm12_pkt packet;

    packet.dest_address         = funk->address;
    packet.source_address       = 0xCC;             // TODO: changed in bridge
    packet.data_length          = 0x04;
    packet.header_checksum      = 0xCC;             // TODO: calced in bridge
    packet.msg.command          = MSG_CMD_SWITCHAPP_REQUEST;
    packet.msg.seqnum           = ++funk->seqnum;   // TODO: retransmit in bridge?
    packet.msg.cause            = CAUSE_SUCCESS;
    packet.msg.p.switchapp.app  = application;

    int ret = funk_send_packet(funk, &packet, 4 + packet.data_length);
    if (ret < 0)
    {
        fprintf(stderr, "funk_switch_application(): funk_send_packet()\n");
        return ret;
    }

    int response_size = sizeof(packet);
    ret = funk_recv_packet(funk, &packet, &response_size);
    if (ret < 0)
    {
        fprintf(stderr, "funk_switch_application(): funk_recv_packet()\n");
        return ret;
    }

    if ((packet.msg.command != MSG_CMD_SWITCHAPP_RESPONSE) ||
        (packet.msg.cause != CAUSE_SUCCESS)
       )
    {
        return -1;
    }

    return 0;
} /* funk_switch_application */


/* *************************************************************************
 * funk_read_version
 * ************************************************************************* */
static int funk_read_version(struct funk_privdata *funk,
                             uint8_t *version,
                             uint16_t length)
{
    struct rfm12_pkt packet;

    packet.dest_address         = funk->address;
    packet.source_address       = 0xCC;             // TODO: changed in bridge
    packet.data_length          = 0x03;
    packet.header_checksum      = 0xCC;             // TODO: calced in bridge
    packet.msg.command          = MSG_CMD_VERSION_REQUEST;
    packet.msg.seqnum           = ++funk->seqnum;   // TODO: retransmit in bridge?
    packet.msg.cause            = CAUSE_SUCCESS;

    int ret = funk_send_packet(funk, &packet, 4 + packet.data_length);
    if (ret < 0)
    {
        fprintf(stderr, "funk_read_version(): funk_send_packet()\n");
        return ret;
    }

    int response_size = sizeof(packet);
    ret = funk_recv_packet(funk, &packet, &response_size);
    if (ret < 0)
    {
        fprintf(stderr, "funk_read_version(): funk_recv_packet()\n");
        return ret;
    }

    if ((packet.msg.command != MSG_CMD_VERSION_RESPONSE) ||
        (packet.msg.cause != CAUSE_SUCCESS)
       )
    {
        return -1;
    }

    int i;
    for (i = 0; i < MIN(length, packet.data_length -3); i++)
    {
        version[i] = packet.msg.p.version.data[i] & 0x7F;
    }

    version[i] = '\0';

    return 0;
} /* funk_read_version */


/* *************************************************************************
 * funk_read_chipinfo
 * ************************************************************************* */
static int funk_read_chipinfo(struct funk_privdata *funk,
                              uint8_t *chipinfo,
                              uint16_t length)
{
    struct rfm12_pkt packet;

    packet.dest_address         = funk->address;
    packet.source_address       = 0xCC;             // TODO: changed in bridge
    packet.data_length          = 0x03;
    packet.header_checksum      = 0xCC;             // TODO: calced in bridge
    packet.msg.command          = MSG_CMD_CHIPINFO_REQUEST;
    packet.msg.seqnum           = ++funk->seqnum;   // TODO: retransmit in bridge?
    packet.msg.cause            = CAUSE_SUCCESS;

    int ret = funk_send_packet(funk, &packet, 4 + packet.data_length);
    if (ret < 0)
    {
        fprintf(stderr, "funk_read_chipinfo(): funk_send_packet()\n");
        return ret;
    }

    int response_size = sizeof(packet);
    ret = funk_recv_packet(funk, &packet, &response_size);
    if (ret < 0) {
        fprintf(stderr, "funk_read_chipinfo(): funk_recv_packet()\n");
        return ret;
    }

    if ((packet.msg.command != MSG_CMD_CHIPINFO_RESPONSE) ||
        (packet.msg.cause != CAUSE_SUCCESS)
       )
    {
        return -1;
    }

    memcpy(chipinfo, packet.msg.p.chipinfo.data, MIN(packet.data_length -3, length));

    return 0;
} /* funk_read_chipinfo */


/* *************************************************************************
 * funk_read_memory
 * ************************************************************************* */
static int funk_read_memory(struct funk_privdata *funk,
                            uint8_t *buffer,
                            uint16_t size,
                            uint8_t memtype,
                            uint16_t address)
{
    struct rfm12_pkt packet;

    packet.dest_address         = funk->address;
    packet.source_address       = 0xCC;             // TODO: changed in bridge
    packet.data_length          = 0x07;
    packet.header_checksum      = 0xCC;             // TODO: calced in bridge
    packet.msg.command          = MSG_CMD_READ_REQUEST;
    packet.msg.seqnum           = ++funk->seqnum;   // TODO: retransmit in bridge?
    packet.msg.cause            = CAUSE_SUCCESS;
    packet.msg.p.read_req.address   = address;
    packet.msg.p.read_req.mem_type  = memtype;
    packet.msg.p.read_req.size      = size;

    int ret = funk_send_packet(funk, &packet, 4 + packet.data_length);
    if (ret < 0) {
        fprintf(stderr, "funk_read_memory(): funk_send_packet()\n");
        return ret;
    }

    int response_size = sizeof(packet);
    ret = funk_recv_packet(funk, &packet, &response_size);
    if (ret < 0) {
        fprintf(stderr, "funk_read_memory(): funk_recv_packet()\n");
        return ret;
    }

    if ((packet.msg.command != MSG_CMD_READ_RESPONSE) ||
        (packet.msg.cause != CAUSE_SUCCESS)
       )
    {
        return -1;
    }

    memcpy(buffer, packet.msg.p.read_rsp.data, MIN(packet.data_length -3, size));

    return 0;
} /* funk_read_memory */


/* *************************************************************************
 * __funk_write_memory
 * ************************************************************************* */
static int __funk_write_memory(struct funk_privdata *funk,
                               uint8_t *buffer,
                               uint16_t size,
                               uint8_t memtype,
                               uint16_t address)
{
    struct rfm12_pkt packet;

    packet.dest_address         = funk->address;
    packet.source_address       = 0xCC;             // TODO: changed in bridge
    packet.data_length          = 0x07 + size;
    packet.header_checksum      = 0xCC;             // TODO: calced in bridge
    packet.msg.command          = MSG_CMD_WRITE_REQUEST;
    packet.msg.seqnum           = ++funk->seqnum;   // TODO: retransmit in bridge?
    packet.msg.cause            = CAUSE_SUCCESS;
    packet.msg.p.write_req.address   = address;
    packet.msg.p.write_req.mem_type  = memtype;
    packet.msg.p.write_req.size      = size;

    memcpy(packet.msg.p.write_req.data, buffer, size);

    int ret = funk_send_packet(funk, &packet, 4 + packet.data_length);
    if (ret < 0)
    {
        fprintf(stderr, "funk_write_memory(): funk_send_packet()\n");
        return ret;
    }

    int response_size = sizeof(packet);
    ret = funk_recv_packet(funk, &packet, &response_size);
    if (ret < 0)
    {
        fprintf(stderr, "funk_write_memory(): funk_recv_packet()\n");
        return ret;
    }

    if ((packet.msg.command != MSG_CMD_WRITE_RESPONSE) ||
        (packet.msg.cause != CAUSE_SUCCESS)
       )
    {
        return -1;
    }

    return 0;
} /* __funk_write_memory */


/* *************************************************************************
 * funk_write_memory
 * ************************************************************************* */
static int funk_write_memory(struct funk_privdata *funk,
                             uint8_t *buffer,
                             uint16_t size,
                             uint8_t memtype,
                             uint16_t address)
{
    if (memtype == MEMTYPE_EEPROM)
    {
        return __funk_write_memory(funk, buffer, size, memtype, address);
    }
    else if ((address & (funk->flashpage -1)) != 0x00)
    {
        fprintf(stderr, "funk_write_memory(): address 0x%04x not aligned to pagesize 0x%02x\n", address, funk->flashpage);
        return -1;
    }

    uint8_t *pagebuf = malloc(funk->flashpage);
    if (pagebuf == NULL)
    {
        perror("malloc()");
        return -1;
    }

    memcpy(pagebuf, buffer, size);
    memset(pagebuf + size, 0xFF, funk->flashpage - size);

    int pos = 0;
    int ret = 0;
    for (pos = 0; pos < funk->flashpage; pos += WRITE_BLOCK_SIZE)
    {
        ret = __funk_write_memory(funk, &pagebuf[pos], WRITE_BLOCK_SIZE, memtype, address + pos);
        if (ret < 0)
        {
            break;
        }
    }

    free(pagebuf);
    return ret;
} /* funk_write_memory */


/* *************************************************************************
 * funk_close
 * ************************************************************************* */
static int funk_close(struct multiboot *mboot)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;

    if (funk->connected)
    {
        funk_switch_application(funk, BOOTTYPE_APPLICATION);
    }

    funk_close_device(funk);
    return 0;
} /* funk_close */


/* *************************************************************************
 * funk_open
 * ************************************************************************* */
static int funk_open(struct multiboot *mboot)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;

    if (funk->address == 0)
    {
        fprintf(stderr, "abort: no address given\n");
        return -1;
    }

    if (funk->device == NULL)
    {
        fprintf(stderr, "abort: no device given\n");
        return -1;
    }

    if (funk_open_device(funk) < 0)
    {
        return -1;
    }

    printf("funkbridge dev : %-16s\n", funk->device);

    char bridge_version[20];
    if (funk_bridge_version(funk, (uint8_t *)bridge_version, sizeof(bridge_version)))
    {
        fprintf(stderr, "failed to get funkbridge version\n");
        funk_close(mboot);
        return -1;
    }

    printf("funkbridge ver : %-16s\n", bridge_version);

    if (funk_switch_application(funk, BOOTTYPE_BOOTLOADER))
    {
        fprintf(stderr, "failed to switch to bootloader (invalid address?)\n");
        funk_close(mboot);
        return -1;
    }

    printf("address        : 0x%02X\n", funk->address);

    /* wait for watchdog and startup time */
    usleep(100000);

    char version[20];
    if (funk_read_version(funk, (uint8_t *)version, sizeof(version)))
    {
        fprintf(stderr, "failed to get bootloader version\n");
        funk_close(mboot);
        return -1;
    }

    uint8_t chipinfo[8];
    if (funk_read_chipinfo(funk, chipinfo, sizeof(chipinfo)))
    {
        fprintf(stderr, "failed to get bootloader chipinfo\n");
        funk_close(mboot);
        return -1;
    }

    const char *chipname = chipinfo_get_avr_name(chipinfo);

    funk->flashpage  = chipinfo[3];
    funk->flashsize  = (chipinfo[4] << 8) + chipinfo[5];
    funk->eepromsize = (chipinfo[6] << 8) + chipinfo[7];

    printf("version        : %-16s (sig: 0x%02x 0x%02x 0x%02x => %s)\n",
           version, chipinfo[0], chipinfo[1], chipinfo[2], chipname);

    printf("flash size     : 0x%04x / %5d   (0x%02x bytes/page)\n",
           funk->flashsize, funk->flashsize, funk->flashpage);

    printf("eeprom size    : 0x%04x / %5d\n",
           funk->eepromsize, funk->eepromsize);

    return 0;
} /* funk_open */


/* *************************************************************************
 * funk_read
 * ************************************************************************* */
static int funk_read(struct multiboot *mboot,
                     struct databuf *dbuf,
                     int memtype)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "reading flash" : "reading eeprom";

    uint16_t pos = 0;
    uint16_t size = (memtype == MEMTYPE_FLASH) ? funk->flashsize : funk->eepromsize;

    while (pos < size)
    {
        mboot->progress_cb(progress_msg, pos, size);

        uint16_t len = MIN(READ_BLOCK_SIZE, size - pos);
        if (funk_read_memory(funk, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    dbuf->length = pos;

    mboot->progress_cb(progress_msg, pos, size);
    return 0;
} /* funk_read */


/* *************************************************************************
 * funk_write
 * ************************************************************************* */
static int funk_write(struct multiboot *mboot,
                      struct databuf *dbuf,
                      int memtype)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "writing flash" : "writing eeprom";

    uint16_t pos = 0;
    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint16_t len = (memtype == MEMTYPE_FLASH) ? funk->flashpage : WRITE_BLOCK_SIZE;

        len = MIN(len, dbuf->length - pos);

        if (funk_write_memory(funk, dbuf->data + pos, len, memtype, pos))
        {
            mboot->progress_cb(progress_msg, -1, -1);
            return -1;
        }

        pos += len;
    }

    mboot->progress_cb(progress_msg, pos, dbuf->length);
    return 0;
} /* funk_write */


/* *************************************************************************
 * funk_verify
 * ************************************************************************* */
static int funk_verify(struct multiboot *mboot,
                       struct databuf *dbuf,
                       int memtype)
{
    struct funk_privdata *funk = (struct funk_privdata *)mboot->privdata;
    char *progress_msg = (memtype == MEMTYPE_FLASH) ? "verifing flash" : "verifing eeprom";

    uint16_t pos = 0;
    uint8_t comp[READ_BLOCK_SIZE];

    while (pos < dbuf->length)
    {
        mboot->progress_cb(progress_msg, pos, dbuf->length);

        uint16_t len = MIN(READ_BLOCK_SIZE, dbuf->length - pos);
        if (funk_read_memory(funk, comp, len, memtype, pos))
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
} /* funk_verify */


struct multiboot_ops funk_ops =
{
    .exec_name      = "funkboot",
    .alloc          = funk_alloc,
    .free           = funk_free,
    .get_memtype    = funk_get_memtype,
    .get_memsize    = funk_get_memsize,

    .open           = funk_open,
    .close          = funk_close,
    .read           = funk_read,
    .write          = funk_write,
    .verify         = funk_verify,
};
