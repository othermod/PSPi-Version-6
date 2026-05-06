#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>

#define BL_ADDR                 0x29
#define FW_ADDR                 0x30

#define CMD_ABORT_TIMEOUT       0x00
#define CMD_READ_INFO           0x01
#define CMD_SET_PAGE            0x02
#define CMD_WRITE_PAGE          0x03
#define CMD_READ_PAGE           0x04
#define CMD_FINALIZE            0x05

#define EXPECTED_BL_VERSION     0x01

/* ATmega8 factory signature bytes (datasheet section 24.8) */
#define EXPECTED_SIG_0          0x1E
#define EXPECTED_SIG_1          0x93
#define EXPECTED_SIG_2          0x07

#define SPM_PAGESIZE            64
#define FLASH_SIZE              8192
#define NUM_PAGES               (FLASH_SIZE / SPM_PAGESIZE)

/* ATmega8 datasheet: max flash write time 4.5ms. 25ms gives ample margin. */
#define FLASH_WRITE_WAIT_US     25000

#define PROBE_INTERVAL_US       100000   /* 100ms between probes */
#define PROBE_TIMEOUT_S         5
#define PROBE_MAX_RETRIES       (PROBE_TIMEOUT_S * (1000000 / PROBE_INTERVAL_US))

#define DEFAULT_RESET_CMD       { 0x50, 0x00 }
#define DEFAULT_RESET_CMD_LEN   2
#define MAX_RESET_CMD_LEN       16

typedef struct {
    uint8_t  data[FLASH_SIZE];
    uint8_t  page_has_data[NUM_PAGES];
    uint16_t num_pages;
} flash_image_t;

static int i2c_fd = -1;

static int i2c_open(const char *device)
{
    i2c_fd = open(device, O_RDWR);
    if (i2c_fd < 0) {
        fprintf(stderr, "Failed to open I2C device %s: %s\n", device, strerror(errno));
        return -1;
    }
    return 0;
}

static int i2c_write(uint8_t addr, const uint8_t *buf, size_t len)
{
    if (ioctl(i2c_fd, I2C_SLAVE, addr) < 0) {
        fprintf(stderr, "i2c_write: ioctl I2C_SLAVE 0x%02X failed: %s\n", addr, strerror(errno));
        return -1;
    }
    if (write(i2c_fd, buf, len) != (ssize_t)len) {
        fprintf(stderr, "i2c_write: write to 0x%02X failed: %s\n", addr, strerror(errno));
        return -1;
    }
    return 0;
}

/* Uses I2C_RDWR to guarantee a repeated START between write and read phases. */
static int i2c_write_then_read(uint8_t addr,
                                const uint8_t *wbuf, size_t wlen,
                                uint8_t *rbuf,        size_t rlen)
{
    struct i2c_msg msgs[2] = {
        { .addr = addr, .flags = 0,        .len = (__u16)wlen, .buf = (uint8_t *)wbuf },
        { .addr = addr, .flags = I2C_M_RD, .len = (__u16)rlen, .buf = rbuf            },
    };
    struct i2c_rdwr_ioctl_data data = { .msgs = msgs, .nmsgs = 2 };

    if (ioctl(i2c_fd, I2C_RDWR, &data) < 0) {
        fprintf(stderr, "i2c_write_then_read: I2C_RDWR to 0x%02X failed: %s\n",
                addr, strerror(errno));
        return -1;
    }
    return 0;
}

static int i2c_probe(uint8_t addr)
{
    uint8_t dummy;
    if (ioctl(i2c_fd, I2C_SLAVE, addr) < 0)
        return -1;
    return read(i2c_fd, &dummy, 1) == 1 ? 0 : -1;
}

static int bl_abort_timeout(void)
{
    uint8_t cmd = CMD_ABORT_TIMEOUT;
    return i2c_write(BL_ADDR, &cmd, 1);
}

static int bl_read_info(uint8_t *sig0, uint8_t *sig1, uint8_t *sig2, uint8_t *version, uint8_t *fw_pages)
{
    uint8_t cmd = CMD_READ_INFO;
    uint8_t buf[5];
    if (i2c_write_then_read(BL_ADDR, &cmd, 1, buf, 5) < 0)
        return -1;
    *sig0      = buf[0];
    *sig1      = buf[1];
    *sig2      = buf[2];
    *version   = buf[3];
    *fw_pages = buf[4];
    return 0;
}

static int bl_set_page(uint8_t page)
{
    uint8_t buf[2] = { CMD_SET_PAGE, page };
    return i2c_write(BL_ADDR, buf, 2);
}

/* Bootloader commits the page to flash on STOP after the 64th byte. */
static int bl_write_page(const uint8_t *data)
{
    uint8_t buf[1 + SPM_PAGESIZE];
    buf[0] = CMD_WRITE_PAGE;
    memcpy(buf + 1, data, SPM_PAGESIZE);
    if (i2c_write(BL_ADDR, buf, sizeof(buf)) < 0)
        return -1;
    usleep(FLASH_WRITE_WAIT_US);
    return 0;
}

static int bl_read_page(uint8_t *buf, size_t len)
{
    uint8_t cmd = CMD_READ_PAGE;
    return i2c_write_then_read(BL_ADDR, &cmd, 1, buf, len);
}

static int bl_finalize(void)
{
    uint8_t cmd = CMD_FINALIZE;
    return i2c_write(BL_ADDR, &cmd, 1);
}

static int enter_bootloader(const uint8_t *reset_cmd, size_t reset_cmd_len)
{
    int i;

    if (i2c_probe(BL_ADDR) == 0) {
        printf("Bootloader already running at 0x%02X.\n", BL_ADDR);
        return 0;
    }

    if (i2c_probe(FW_ADDR) == 0) {
        printf("Firmware running at 0x%02X. Sending reset command...\n", FW_ADDR);
        if (i2c_write(FW_ADDR, reset_cmd, reset_cmd_len) < 0) {
            fprintf(stderr, "Failed to send reset command to firmware.\n");
            return -1;
        }
    } else {
        printf("No device found at 0x%02X or 0x%02X.\n", BL_ADDR, FW_ADDR);
    }

    printf("Waiting for bootloader");
    fflush(stdout);
    for (i = 0; i < PROBE_MAX_RETRIES; i++) {
        if (i2c_probe(BL_ADDR) == 0) {
            printf("\nBootloader detected at 0x%02X.\n", BL_ADDR);
            return 0;
        }
        usleep(PROBE_INTERVAL_US);
        printf(".");
        fflush(stdout);
    }

    printf("\n");
    fprintf(stderr, "Timed out waiting for bootloader at 0x%02X.\n", BL_ADDR);
    return -1;
}

static int parse_hex_file(const char *path, flash_image_t *image)
{
    FILE *f;
    char  line[256];
    int   line_num = 0;
    int   ret      = -1;

    f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "Failed to open HEX file %s: %s\n", path, strerror(errno));
        return -1;
    }

    memset(image->data,          0xFF, sizeof(image->data));
    memset(image->page_has_data, 0,    sizeof(image->page_has_data));
    image->num_pages = 0;

    while (fgets(line, sizeof(line), f)) {
        unsigned int byte_count, addr_val, record_type;
        unsigned int checksum_accum, record_checksum;
        unsigned int i;

        line_num++;

        if (line[0] != ':')
            continue;

        if (sscanf(line + 1, "%02X%04X%02X", &byte_count, &addr_val, &record_type) != 3) {
            fprintf(stderr, "Malformed HEX record at line %d.\n", line_num);
            goto fail;
        }

        if (record_type == 0x01)
            break;

        if (record_type != 0x00)
            continue;

        if (addr_val + byte_count > FLASH_SIZE) {
            fprintf(stderr, "HEX data at 0x%04X (line %d) exceeds flash size.\n",
                    addr_val, line_num);
            goto fail;
        }

        /* Per-record checksum: sum of all header, data, and checksum bytes must be 0x00 mod 256. */
        checksum_accum = byte_count + ((addr_val >> 8) & 0xFF) + (addr_val & 0xFF) + record_type;

        for (i = 0; i < byte_count; i++) {
            unsigned int byte_val;
            if (sscanf(line + 9 + i * 2, "%02X", &byte_val) != 1) {
                fprintf(stderr, "Failed to parse data byte at line %d.\n", line_num);
                goto fail;
            }
            checksum_accum += byte_val;
            image->data[addr_val + i] = (uint8_t)byte_val;
            image->page_has_data[(addr_val + i) / SPM_PAGESIZE] = 1;
        }

        if (sscanf(line + 9 + byte_count * 2, "%02X", &record_checksum) != 1) {
            fprintf(stderr, "Missing checksum byte at line %d.\n", line_num);
            goto fail;
        }
        if (((checksum_accum + record_checksum) & 0xFF) != 0x00) {
            fprintf(stderr, "Checksum error at line %d.\n", line_num);
            goto fail;
        }
    }

    for (int i = 0; i < NUM_PAGES; i++)
        if (image->page_has_data[i])
            image->num_pages++;

    ret = 0;

fail:
    fclose(f);
    return ret;
}

static int backup_firmware(const char *path, uint8_t fw_pages)
{
    FILE    *f;
    uint8_t  buf[SPM_PAGESIZE];
    int      page;

    f = fopen(path, "w");
    if (!f) {
        fprintf(stderr, "Failed to open backup file %s: %s\n", path, strerror(errno));
        return -1;
    }

    printf("Backing up %d page(s) to %s...\n", fw_pages, path);

    for (page = 0; page < fw_pages; page++) {
        uint16_t addr = (uint16_t)page * SPM_PAGESIZE;
        uint8_t  checksum;
        int      i;

        if (bl_set_page((uint8_t)page) < 0) {
            fprintf(stderr, "Failed to set address for page %d.\n", page);
            fclose(f);
            return -1;
        }
        if (bl_read_page(buf, SPM_PAGESIZE) < 0) {
            fprintf(stderr, "Failed to read page %d.\n", page);
            fclose(f);
            return -1;
        }

        /* Intel HEX data record: :LLAAAATT[DD...]CC */
        checksum = SPM_PAGESIZE
                 + ((addr >> 8) & 0xFF)
                 + (addr & 0xFF)
                 + 0x00; /* record type */
        for (i = 0; i < SPM_PAGESIZE; i++)
            checksum += buf[i];
        checksum = (~checksum + 1) & 0xFF;

        fprintf(f, ":%02X%04X00", SPM_PAGESIZE, addr);
        for (i = 0; i < SPM_PAGESIZE; i++)
            fprintf(f, "%02X", buf[i]);
        fprintf(f, "%02X\n", checksum);

        printf("\r  [%d/%d] read", page + 1, fw_pages);
        fflush(stdout);
    }

    fprintf(f, ":00000001FF\n"); /* EOF record */
    fclose(f);
    printf("\nBackup complete.\n\n");
    return 0;
}


static int flash_image(const flash_image_t *image)
{
    int page, written = 0;

    printf("Flashing %u page(s)...\n", image->num_pages);

    for (page = 0; page < NUM_PAGES; page++) {
        if (!image->page_has_data[page])
            continue;

        if (bl_set_page((uint8_t)page) < 0) {
            fprintf(stderr, "Failed to set address for page %d.\n", page);
            return -1;
        }
        if (bl_write_page(image->data + page * SPM_PAGESIZE) < 0) {
            fprintf(stderr, "Failed to write page %d.\n", page);
            return -1;
        }

        printf("\r  [%d/%d] written", ++written, image->num_pages);
        fflush(stdout);
    }

    printf("\nFlashing complete.\n");
    return 0;
}

static int verify_image(const flash_image_t *image)
{
    int page, verified = 0, total_errs = 0;

    printf("Verifying %u page(s)...\n", image->num_pages);

    for (page = 0; page < NUM_PAGES; page++) {
        uint8_t actual[SPM_PAGESIZE];
        int     page_errs = 0;
        int     i;

        if (!image->page_has_data[page])
            continue;

        if (bl_set_page((uint8_t)page) < 0) {
            fprintf(stderr, "Failed to set address for page %d.\n", page);
            return -1;
        }
        if (bl_read_page(actual, SPM_PAGESIZE) < 0) {
            fprintf(stderr, "Failed to read page %d.\n", page);
            return -1;
        }

        for (i = 0; i < SPM_PAGESIZE; i++)
            if (image->data[page * SPM_PAGESIZE + i] != actual[i])
                page_errs++;

        if (page_errs > 0) {
            printf("\r  [%d/%d] page %d MISMATCH (%d byte(s))\n",
                   ++verified, image->num_pages, page, page_errs);
            total_errs += page_errs;
        } else {
            printf("\r  [%d/%d] OK", ++verified, image->num_pages);
            fflush(stdout);
        }
    }

    if (total_errs > 0) {
        fprintf(stderr, "\nVerification failed: %d byte(s) mismatched.\n"
                        "Device remains in bootloader. Re-run to retry.\n", total_errs);
        return -1;
    }

    printf("\nVerification successful.\n");
    return 0;
}

static void usage(const char *prog)
{
    fprintf(stderr,
        "Usage: %s [options] <firmware.hex>\n"
        "\n"
        "Options:\n"
        "  -d <device>    I2C device node     (default: /dev/i2c-1)\n"
        "  -r <hexbytes>  Firmware reset command   (default: 5000)\n"
        "  -b <file>      Backup current firmware to HEX file before flashing\n"
        "  -n             Skip verify and finalize\n"
        "  -h             Show this help\n"
        "\n"
        "The -r value is a run of hex byte pairs, e.g. -r 5000 sends [0x50, 0x00].\n",
        prog);
}

static int parse_reset_cmd(const char *arg, uint8_t *out, size_t *out_len)
{
    size_t slen = strlen(arg);

    if (slen == 0 || slen % 2 != 0) {
        fprintf(stderr, "Reset command must be a non-empty even number of hex digits.\n");
        return -1;
    }
    if (slen / 2 > MAX_RESET_CMD_LEN) {
        fprintf(stderr, "Reset command too long (max %d bytes).\n", MAX_RESET_CMD_LEN);
        return -1;
    }

    *out_len = slen / 2;
    for (size_t i = 0; i < *out_len; i++) {
        unsigned int byte_val;
        if (sscanf(arg + i * 2, "%02X", &byte_val) != 1) {
            fprintf(stderr, "Invalid hex in reset command.\n");
            return -1;
        }
        out[i] = (uint8_t)byte_val;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    const char   *device      = "/dev/i2c-1";
    const char   *hex_file    = NULL;
    const char   *backup_file = NULL;
    int           skip_verify = 0;
    int           opt, ret    = 0;
    uint8_t       sig0, sig1, sig2, version, fw_pages;
    uint8_t       reset_cmd[MAX_RESET_CMD_LEN] = DEFAULT_RESET_CMD;
    size_t        reset_cmd_len                = DEFAULT_RESET_CMD_LEN;
    flash_image_t image;

    while ((opt = getopt(argc, argv, "d:r:b:nh")) != -1) {
        switch (opt) {
            case 'd': device = optarg;                                                       break;
            case 'r': if (parse_reset_cmd(optarg, reset_cmd, &reset_cmd_len) < 0) return 1; break;
            case 'b': backup_file = optarg;                                                  break;
            case 'n': skip_verify = 1;                                                       break;
            case 'h': usage(argv[0]); return 0;
            default:  usage(argv[0]); return 1;
        }
    }

    if (optind >= argc) {
        fprintf(stderr, "Error: no HEX file specified.\n\n");
        usage(argv[0]);
        return 1;
    }

    hex_file = argv[optind];

    printf("Parsing %s...\n\n", hex_file);
    if (parse_hex_file(hex_file, &image) < 0)
        return 1;

    if (i2c_open(device) < 0)
        return 1;

    printf("--- Enter Bootloader ---\n");
    if (enter_bootloader(reset_cmd, reset_cmd_len) < 0) { ret = 1; goto done; }

    if (bl_abort_timeout() < 0) {
        fprintf(stderr, "Failed to abort boot timeout.\n");
        ret = 1;
        goto done;
    }
    printf("Keeping Atmega in bootloader mode for flashing.\n");

    if (bl_read_info(&sig0, &sig1, &sig2, &version, &fw_pages) < 0) {
        fprintf(stderr, "Failed to read chip info.\n");
        ret = 1;
        goto done;
    }
    printf("Signature: 0x%02X 0x%02X 0x%02X\n", sig0, sig1, sig2);
    if (sig0 != EXPECTED_SIG_0 || sig1 != EXPECTED_SIG_1 || sig2 != EXPECTED_SIG_2) {
        fprintf(stderr, "Signature mismatch: expected 0x%02X 0x%02X 0x%02X. Aborting.\n",
                EXPECTED_SIG_0, EXPECTED_SIG_1, EXPECTED_SIG_2);
        ret = 1;
        goto done;
    }
    printf("Bootloader version: 0x%02X\n", version);
    if (version != EXPECTED_BL_VERSION)
        fprintf(stderr, "Warning: unexpected bootloader version 0x%02X (expected 0x%02X). "
                        "Proceeding anyway.\n", version, EXPECTED_BL_VERSION);
    printf("Firmware flash: %d pages available\n", fw_pages);
    printf("Preparing to flash %u pages with data.\n\n", image.num_pages);

    for (int i = fw_pages; i < NUM_PAGES; i++) {
        if (image.page_has_data[i]) {
            fprintf(stderr, "Error: firmware image exceeds available flash "
                            "(data in page %d, max page is %d).\n", i, fw_pages - 1);
            ret = 1;
            goto done;
        }
    }

    if (backup_file) {
        printf("--- Backup ---\n");
        if (backup_firmware(backup_file, fw_pages) < 0) { ret = 1; goto done; }
    }

    printf("--- Flash ---\n");
    if (flash_image(&image) < 0) { ret = 1; goto done; }
    printf("\n");

    if (skip_verify) {
        printf("Skipping verification and finalize (-n).\n"
               "Device remains in bootloader. Firmware will not boot until\n"
               "a verified flash is completed and finalized.\n");
        goto done;
    }

    printf("--- Verify ---\n");
    if (verify_image(&image) < 0) { ret = 1; goto done; }
    printf("\n");

    printf("--- Finalize ---\n");
    if (bl_finalize() < 0) {
        fprintf(stderr, "Failed to send finalize command.\n");
        ret = 1;
        goto done;
    }
    printf("Finalize sent. Bootloader is writing metadata and launching firmware.\n");

done:
    close(i2c_fd);
    return ret;
}
