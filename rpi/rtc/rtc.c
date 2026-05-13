#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <syslog.h>
#include <time.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/timerfd.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>

#define I2C_BUS      "/dev/i2c-1"
#define PCF8563_ADDR  0x51

#define REG_ST2   0x01
#define REG_SC    0x02
#define REG_MN    0x03
#define REG_HR    0x04
#define REG_DM    0x05
#define REG_DW    0x06
#define REG_MO    0x07
#define REG_YR    0x08

#define SC_LV       0x80
#define MO_CENTURY  0x80

static uint8_t bcd2bin(uint8_t v) { return (v >> 4) * 10 + (v & 0x0f); }
static uint8_t bin2bcd(uint8_t v) { return ((v / 10) << 4) | (v % 10); }

static int i2c_write(int fd, const uint8_t *buf, int len)
{
    struct i2c_msg msg = {
        .addr  = PCF8563_ADDR,
        .flags = 0,
        .len   = (__u16)len,
        .buf   = (uint8_t *)buf,
    };
    struct i2c_rdwr_ioctl_data tr = { .msgs = &msg, .nmsgs = 1 };
    return ioctl(fd, I2C_RDWR, &tr) < 0 ? -errno : 0;
}

static int i2c_read_from(int fd, uint8_t reg, uint8_t *out, int len)
{
    struct i2c_msg msgs[2] = {
        { .addr = PCF8563_ADDR, .flags = 0,        .len = 1,          .buf = &reg },
        { .addr = PCF8563_ADDR, .flags = I2C_M_RD, .len = (__u16)len, .buf = out  },
    };
    struct i2c_rdwr_ioctl_data tr = { .msgs = msgs, .nmsgs = 2 };
    return ioctl(fd, I2C_RDWR, &tr) < 0 ? -errno : 0;
}

static int chip_init(int fd)
{
    uint8_t buf[2] = { REG_ST2, 0x00 };
    return i2c_write(fd, buf, 2);
}

static int chip_read_time(int fd, struct tm *out)
{
    uint8_t regs[7];
    int ret = i2c_read_from(fd, REG_SC, regs, 7);
    if (ret < 0) return ret;
    if (regs[0] & SC_LV) return -EINVAL;

    out->tm_sec  = bcd2bin(regs[0] & 0x7f);
    out->tm_min  = bcd2bin(regs[1] & 0x7f);
    out->tm_hour = bcd2bin(regs[2] & 0x3f);
    out->tm_mday = bcd2bin(regs[3] & 0x3f);
    out->tm_wday = regs[4] & 0x07;
    out->tm_mon  = bcd2bin(regs[5] & 0x1f) - 1;
    out->tm_year = bcd2bin(regs[6]) + 100;
    out->tm_isdst = 0;
    return 0;
}

static int chip_write_time(int fd, const struct tm *t)
{
    uint8_t buf[8];
    buf[0] = REG_SC;
    buf[1] = bin2bcd((uint8_t)t->tm_sec);
    buf[2] = bin2bcd((uint8_t)t->tm_min);
    buf[3] = bin2bcd((uint8_t)t->tm_hour);
    buf[4] = bin2bcd((uint8_t)t->tm_mday);
    buf[5] = (uint8_t)(t->tm_wday & 0x07);
    buf[6] = bin2bcd((uint8_t)(t->tm_mon + 1));
    buf[7] = bin2bcd((uint8_t)(t->tm_year - 100));
    if (t->tm_year < 100) buf[6] |= MO_CENTURY;
    return i2c_write(fd, buf, 8);
}

static int make_cancel_timerfd(void)
{
    int tfd = timerfd_create(CLOCK_REALTIME, TFD_CLOEXEC);
    if (tfd < 0) return -errno;

    struct itimerspec its = {
        .it_value    = { .tv_sec = 0x7fffffff, .tv_nsec = 0 },
        .it_interval = { 0 },
    };
    if (timerfd_settime(tfd, TFD_TIMER_ABSTIME | TFD_TIMER_CANCEL_ON_SET, &its, NULL) < 0) {
        int e = errno; close(tfd); return -e;
    }
    return tfd;
}

int main(void)
{
    openlog("pcf8563d", LOG_PID, LOG_DAEMON);

    int i2c = open(I2C_BUS, O_RDWR | O_CLOEXEC);
    if (i2c < 0) { syslog(LOG_ERR, "open %s: %m", I2C_BUS); return 1; }

    if (chip_init(i2c) < 0) { syslog(LOG_ERR, "chip_init: %m"); return 1; }

    struct tm rtc_tm = { 0 };
    int ret = chip_read_time(i2c, &rtc_tm);
    if (ret == -EINVAL) {
        syslog(LOG_WARNING, "low-voltage flag set, skipping sync");
    } else if (ret < 0) {
        syslog(LOG_ERR, "chip_read_time: %s", strerror(-ret)); return 1;
    } else {
        struct timespec ts = { .tv_sec = timegm(&rtc_tm), .tv_nsec = 0 };
        if (clock_settime(CLOCK_REALTIME, &ts) < 0)
            syslog(LOG_ERR, "clock_settime: %m");
        else
            syslog(LOG_INFO, "system clock set from RTC");
    }

    int tfd = make_cancel_timerfd();
    if (tfd < 0) { syslog(LOG_ERR, "timerfd: %s", strerror(-tfd)); return 1; }

    for (;;) {
        uint64_t exp;
        ssize_t r = read(tfd, &exp, sizeof(exp));
        if (r < 0) {
            if (errno == EINTR) continue;
            if (errno == ECANCELED) {
                struct timespec now;
                struct tm new_tm;
                clock_gettime(CLOCK_REALTIME, &now);
                gmtime_r(&now.tv_sec, &new_tm);
                if (chip_write_time(i2c, &new_tm) < 0)
                    syslog(LOG_ERR, "chip_write_time: %m");
                else
                    syslog(LOG_INFO, "RTC updated after time change");
                close(tfd);
                tfd = make_cancel_timerfd();
                if (tfd < 0) { syslog(LOG_ERR, "timerfd re-arm: %s", strerror(-tfd)); return 1; }
            } else {
                syslog(LOG_ERR, "timerfd read: %m"); return 1;
            }
        }
    }
}
