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

#define CMD_READ_INFO           0x01
#define CMD_WRITE_PAGE          0x03  /* page number byte precedes the 64 data bytes */
#define CMD_FINALIZE            0x05

#define EXPECTED_BL_VERSION     0x01

/* ATmega8 factory signature bytes (datasheet section 24.8) */
#define EXPECTED_SIG_0          0x1E
#define EXPECTED_SIG_1          0x93
#define EXPECTED_SIG_2          0x07

#define SPM_PAGESIZE            64
#define FLASH_SIZE              8192
#define BOOTLOADER_START        0x1C00
#define NUM_PAGES               (FLASH_SIZE / SPM_PAGESIZE)

/* ATmega8 max flash write time is 4.5ms. Sleep 10x that for safety. */
#define FLASH_WRITE_SLEEP_US    45000

/* Verification status codes, must match bootloader */
#define VERIFY_PENDING          0x00
#define VERIFY_FAILED           0x55
#define VERIFY_PASSED           0xAA

/* How many times to retry a corrupt CMD_READ_INFO response */
#define INFO_READ_RETRIES       10

/* How many times to retry a single page write before giving up on the sequence */
#define PAGE_WRITE_RETRIES      3

typedef struct {
    uint8_t  data[FLASH_SIZE];
    uint8_t  page_has_data[NUM_PAGES];
    uint16_t num_pages;
} flash_image_t;

typedef struct {
    uint8_t sig[3];
    uint8_t version;
    uint8_t fw_pages;
    uint8_t verify_status;
} bl_info_t;

static int i2c_fd = -1;

/* --- I2C layer --- */

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
    if (ioctl(i2c_fd, I2C_SLAVE, addr) < 0)
        return -1;
    if (write(i2c_fd, buf, len) != (ssize_t)len)
        return -1;
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

    if (ioctl(i2c_fd, I2C_RDWR, &data) < 0)
        return -1;
    return 0;
}

static int i2c_probe(uint8_t addr)
{
    uint8_t dummy;
    if (ioctl(i2c_fd, I2C_SLAVE, addr) < 0)
        return -1;
    return read(i2c_fd, &dummy, 1) == 1 ? 0 : -1;
}

/* --- Checksum --- */

/* Matches the bootloader algorithm exactly: uint8_t accumulators, natural overflow. */
static void compute_fletcher_xor(const uint8_t *data, uint16_t len,
                                  uint8_t *f_a, uint8_t *f_b, uint8_t *xorsum)
{
    uint8_t  sum1 = 0, sum2 = 0, xor = 0;
    uint16_t i;
    for (i = 0; i < len; i++) {
        sum1 += data[i];
        sum2 += sum1;
        xor  ^= data[i];
    }
    *f_a   = sum1;
    *f_b   = sum2;
    *xorsum = xor;
}

/* --- Bootloader commands --- */

/*
 * Reads all 9 CMD_READ_INFO bytes and validates the trailing 3-byte
 * Fletcher+XOR checksum over the first 6 info bytes. Retries on a
 * corrupt read to mitigate RPi I2C read unreliability.
 */
static int bl_read_info(bl_info_t *info)
{
    uint8_t cmd = CMD_READ_INFO;
    uint8_t buf[9];
    uint8_t f_a, f_b, xor;
    int     attempt;

    for (attempt = 0; attempt < INFO_READ_RETRIES; attempt++) {
        if (attempt > 0)
            usleep(10000);

        if (i2c_write_then_read(BL_ADDR, &cmd, 1, buf, 9) < 0)
            continue;

        /* Validate checksum over bytes 0-5 */
        compute_fletcher_xor(buf, 6, &f_a, &f_b, &xor);
        if (f_a != buf[6] || f_b != buf[7] || xor != buf[8]) {
            fprintf(stderr, "  CMD_READ_INFO checksum mismatch (attempt %d/%d), retrying...\n",
                    attempt + 1, INFO_READ_RETRIES);
            continue;
        }

        info->sig[0]        = buf[0];
        info->sig[1]        = buf[1];
        info->sig[2]        = buf[2];
        info->version       = buf[3];
        info->fw_pages      = buf[4];
        info->verify_status = buf[5];
        usleep(10000); /* allow bus to settle after read */
        return 0;
    }

    fprintf(stderr, "Failed to read valid info after %d attempts.\n", INFO_READ_RETRIES);
    return -1;
}

/*
 * Sends CMD_WRITE_PAGE followed by the page number and 64 data bytes,
 * then sleeps 10x the ATmega8 max flash write time (4.5ms) to ensure
 * the write completes before the next transaction.
 */
static int bl_write_page(uint8_t page, const uint8_t *data)
{
    uint8_t buf[2 + SPM_PAGESIZE];
    buf[0] = CMD_WRITE_PAGE;
    buf[1] = page;
    memcpy(buf + 2, data, SPM_PAGESIZE);
    if (i2c_write(BL_ADDR, buf, sizeof(buf)) < 0)
        return -1;
    usleep(FLASH_WRITE_SLEEP_US);
    return 0;
}

/*
 * Sends CMD_FINALIZE with the 3-byte Fletcher+XOR checksum computed
 * over the full application flash region. The bootloader will verify
 * this against what it finds in flash and update its verify_status.
 */
static int bl_finalize(uint8_t f_a, uint8_t f_b, uint8_t xor)
{
    uint8_t buf[4] = { CMD_FINALIZE, f_a, f_b, xor };
    if (i2c_write(BL_ADDR, buf, sizeof(buf)) < 0)
        return -1;
    usleep(100000); /* 10x time for compute_flash_checksum to complete */
    return 0;
}



/* --- Flash image --- */

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

static int flash_image(const flash_image_t *image, uint8_t fw_pages)
{
    int page;

    printf("Flashing %d page(s)...\n", fw_pages);

    for (page = 0; page < fw_pages; page++) {
        int retry;
        int ok = 0;

        for (retry = 0; retry <= PAGE_WRITE_RETRIES; retry++) {
            if (retry > 0) {
                usleep(FLASH_WRITE_SLEEP_US);
                if (i2c_probe(BL_ADDR) < 0) {
                    fprintf(stderr, "\n  page %d: device not responding after write failure.\n",
                            page);
                    return -1;
                }
                fprintf(stderr, "\n  page %d: device still responding, retrying write "
                        "(%d/%d)...\n", page, retry, PAGE_WRITE_RETRIES);
            }

            if (bl_write_page((uint8_t)page, image->data + page * SPM_PAGESIZE) == 0) {
                ok = 1;
                break;
            }
        }

        if (!ok) {
            fprintf(stderr, "\n  page %d: bl_write_page failed after %d attempts.\n",
                    page, PAGE_WRITE_RETRIES + 1);
            return -1;
        }

        printf("\r  [%d/%d] written", page + 1, fw_pages);
        fflush(stdout);
    }

    printf("\nFlashing complete.\n");
    return 0;
}

/* --- Entry point --- */

static void usage(const char *prog)
{
    fprintf(stderr, "Usage: %s <firmware.hex>\n", prog);
}

/*
 * Runs one full probe -> read_info -> flash -> finalize -> verify sequence.
 *
 * Returns:
 *   0   success
 *  -1   I/O or verification failure
 *  -2   unrecoverable error (bad signature, image out of range, etc.)
 */
static int run_flash_sequence(const flash_image_t *image)
{
    bl_info_t info;
    uint8_t   f_a, f_b, xor;
    bl_info_t verify_info;

    printf("--- Bootloader ---\n");
    if (i2c_probe(BL_ADDR) < 0) {
        fprintf(stderr,
                "Bootloader not found at 0x%02X.\n"
                "To enter bootloader mode: fully shut down the device, then\n"
                "hold the display button at power-on. Then re-run this tool.\n",
                BL_ADDR);
        return -2;
    }
    printf("Bootloader detected at 0x%02X.\n", BL_ADDR);

    if (bl_read_info(&info) < 0)
        return -1;

    printf("Signature:          0x%02X 0x%02X 0x%02X\n",
           info.sig[0], info.sig[1], info.sig[2]);
    printf("Bootloader version: 0x%02X\n", info.version);
    printf("App flash pages:    %d\n\n", info.fw_pages);

    if (info.sig[0] != EXPECTED_SIG_0 ||
        info.sig[1] != EXPECTED_SIG_1 ||
        info.sig[2] != EXPECTED_SIG_2) {
        fprintf(stderr, "Signature mismatch: expected 0x%02X 0x%02X 0x%02X. Aborting.\n",
                EXPECTED_SIG_0, EXPECTED_SIG_1, EXPECTED_SIG_2);
        return -2;
    }

    if (info.version != EXPECTED_BL_VERSION)
        fprintf(stderr, "Warning: unexpected bootloader version 0x%02X (expected 0x%02X). "
                "Proceeding anyway.\n\n", info.version, EXPECTED_BL_VERSION);

    for (int i = info.fw_pages; i < NUM_PAGES; i++) {
        if (image->page_has_data[i]) {
            fprintf(stderr, "Error: firmware image has data in page %d, "
                    "but app flash only has %d page(s). Aborting.\n", i, info.fw_pages);
            return -2;
        }
    }

    printf("--- Flash ---\n");
    if (flash_image(image, info.fw_pages) < 0)
        return -1;
    printf("\n");

    printf("--- Finalize ---\n");
    compute_fletcher_xor(image->data, BOOTLOADER_START, &f_a, &f_b, &xor);
    if (bl_finalize(f_a, f_b, xor) < 0) {
        fprintf(stderr, "Failed to send CMD_FINALIZE.\n");
        return -1;
    }
    printf("Checksum sent (0x%02X 0x%02X 0x%02X). Waiting for verification...\n",
           f_a, f_b, xor);

    if (bl_read_info(&verify_info) < 0)
        return -1;

    if (verify_info.verify_status == VERIFY_PASSED) {
        printf("Verification passed. Firmware update complete.\n");
        return 0;
    }

    fprintf(stderr, "Verification FAILED (status 0x%02X). Flash may be corrupt.\n",
            verify_info.verify_status);
    return -1;
}

int main(int argc, char *argv[])
{
    const char   *hex_file = NULL;
    flash_image_t image;
    int           ret;

    if (geteuid() != 0) {
        fprintf(stderr, "Error: firmware update requires root privileges.\n");
        return 2;
    }

    if (argc < 2 || strcmp(argv[1], "-h") == 0) {
        usage(argv[0]);
        return argc < 2 ? 2 : 0;
    }

    hex_file = argv[1];

    printf("Parsing %s...\n", hex_file);
    if (parse_hex_file(hex_file, &image) < 0)
        return 2;
    printf("  %u page(s) with data.\n\n", image.num_pages);

    if (i2c_open("/dev/i2c-1") < 0)
        return 2;

    ret = run_flash_sequence(&image);

    close(i2c_fd);
    return ret == 0 ? 0 : 1;
}
