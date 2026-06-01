#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <net/if.h>
#include <linux/rtnetlink.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/i2c-dev.h>
#include <errno.h>

#define INTERFACE_NAME     "wlan0"
#define I2C_DEVICE_ADDRESS 0x10

static int  i2c_fd         = -1;
static int  netlink_fd     = -1;
static int  wlan0_ifindex  = 0;
static bool wifi_connected = false;

// --- Shared memory layout --------------------------------------------------

// PSPi controller board data structure (11 bytes), must match gamepad.c
typedef struct {
    union {
        struct Buttons {
            uint16_t mute:1;         // bit 0  - Unused (Mute)
            uint16_t select:1;       // bit 1  - Back (Select)
            uint16_t start:1;        // bit 2  - Start
            uint16_t a:1;            // bit 3  - A
            uint16_t x:1;            // bit 4  - X
            uint16_t y:1;            // bit 5  - Y
            uint16_t b:1;            // bit 6  - B
            uint16_t rshoulder:1;    // bit 7  - Right Shoulder
            uint16_t lshoulder:1;    // bit 8  - Left Shoulder
            uint16_t dpad_left:1;    // bit 9  - D-Pad Left
            uint16_t dpad_up:1;      // bit 10 - D-Pad Up
            uint16_t dpad_down:1;    // bit 11 - D-Pad Down
            uint16_t dpad_right:1;   // bit 12 - D-Pad Right
            uint16_t vol_plus:1;     // bit 13 - Unused (Vol+)
            uint16_t vol_minus:1;    // bit 14 - Unused (Vol-)
            uint16_t home:1;         // bit 15 - Guide (Home)
        } bits;
        uint16_t raw;
    } buttons;
    uint8_t system_voltage;
    uint8_t battery_voltage;
    union {
        struct Status {
            uint8_t brightness:3;    // Bits 0-2: Display brightness level (1-8)
            uint8_t headphones:1;    // Bit 3: Reserved for future use
            uint8_t sd_pressed:1;    // Bit 4: SD button status
            uint8_t sleeping:1;      // Bit 5: Sleep status
            uint8_t left_switch:1;   // Bit 6: Left switch status
            uint8_t muted:1;         // Bit 7: Mute status
        } bits;
        uint8_t raw;
    } status_flags;
    uint8_t left_stick_x;
    uint8_t left_stick_y;
    union {
        struct RightX {
            uint8_t button:1;        // Button data in bit 0
            uint8_t position:7;      // Position data in bits 1-7
        } bits;
        uint8_t raw;
    } right_stick_x;
    union {
        struct RightY {
            uint8_t button:1;        // Button data in bit 0
            uint8_t position:7;      // Position data in bits 1-7
        } bits;
        uint8_t raw;
    } right_stick_y;
    uint8_t crc_high;
    uint8_t crc_low;
} SharedData;

static SharedData *shared_data = NULL;
static int         shm_fd      = -1;

// --- I2C -------------------------------------------------------------------

static void init_i2c(void) {
    i2c_fd = open("/dev/i2c-1", O_RDWR);
    if (i2c_fd < 0) {
        perror("Failed to open i2c bus");
        exit(1);
    }
    if (ioctl(i2c_fd, I2C_SLAVE, I2C_DEVICE_ADDRESS) < 0) {
        perror("Failed to set i2c slave");
        close(i2c_fd);
        exit(1);
    }
}

static void write_wifi_status(void) {
    write(i2c_fd, (uint8_t[]){0x20, wifi_connected, 0, 0}, 4);
}

// --- WiFi control ----------------------------------------------------------

static void set_wifi_enabled(bool enabled) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) { perror("socket for SIOCSIFFLAGS"); return; }

    struct ifreq ifr = {0};
    strncpy(ifr.ifr_name, INTERFACE_NAME, IFNAMSIZ - 1);
    if (ioctl(sock, SIOCGIFFLAGS, &ifr) == 0) {
        if (enabled) ifr.ifr_flags |=  IFF_UP;
        else         ifr.ifr_flags &= ~IFF_UP;
        ioctl(sock, SIOCSIFFLAGS, &ifr);
    }
    close(sock);
}

// --- WiFi monitoring -------------------------------------------------------

static void init_wifi_monitoring(void) {
    netlink_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (netlink_fd == -1) {
        perror("Error creating netlink socket");
        return;
    }

    // Subscribe to RTMGRP_LINK so the kernel pushes RTM_NEWLINK messages
    // to us whenever any interface changes state - no polling required.
    struct sockaddr_nl local = {
        .nl_family = AF_NETLINK,
        .nl_pid    = getpid(),
        .nl_groups = RTMGRP_LINK,
    };
    if (bind(netlink_fd, (struct sockaddr *)&local, sizeof(local)) < 0) {
        perror("Error binding netlink socket");
        close(netlink_fd);
        netlink_fd = -1;
        return;
    }

    wlan0_ifindex = if_nametoindex(INTERFACE_NAME);
    if (wlan0_ifindex == 0) {
        perror("Error getting interface index");
        close(netlink_fd);
        netlink_fd = -1;
        return;
    }

    // Bootstrap: do a one-shot RTM_GETLINK query to get the current state
    // before any change events arrive. Without this, wifi_connected stays
    // false until the next state change, even if we're already connected.
    struct {
        struct nlmsghdr nlh;
        struct ifinfomsg ifi;
    } req;
    memset(&req, 0, sizeof(req));
    req.nlh.nlmsg_len   = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    req.nlh.nlmsg_flags = NLM_F_REQUEST;
    req.nlh.nlmsg_type  = RTM_GETLINK;
    req.nlh.nlmsg_seq   = 1;
    req.ifi.ifi_family  = AF_UNSPEC;
    req.ifi.ifi_index   = wlan0_ifindex;

    struct sockaddr_nl kernel = { .nl_family = AF_NETLINK, .nl_pid = 0, .nl_groups = 0 };
    if (sendto(netlink_fd, &req, req.nlh.nlmsg_len, 0,
               (struct sockaddr *)&kernel, sizeof(kernel)) < 0) {
        perror("Error sending initial netlink request");
        return;
    }

    char buf[4096];
    int len = recv(netlink_fd, buf, sizeof(buf), 0);
    if (len < 0) {
        perror("Error receiving initial netlink response");
        return;
    }
    struct nlmsghdr *nh = (struct nlmsghdr *)buf;
    if (NLMSG_OK(nh, len) && nh->nlmsg_type == RTM_NEWLINK) {
        struct ifinfomsg *ifi = NLMSG_DATA(nh);
        wifi_connected = ifi->ifi_flags & IFF_RUNNING;
        write_wifi_status();
    }
}

static void check_wifi_status(void) {
    char buf[4096];
    int len;

    // MSG_DONTWAIT returns immediately if nothing is pending - no blocking.
    // The while loop handles multiple batched messages in one recv buffer.
    while ((len = recv(netlink_fd, buf, sizeof(buf), MSG_DONTWAIT)) > 0) {
        for (struct nlmsghdr *nh = (struct nlmsghdr *)buf;
             NLMSG_OK(nh, len);
             nh = NLMSG_NEXT(nh, len)) {
            if (nh->nlmsg_type != RTM_NEWLINK)
                continue;

            struct ifinfomsg *ifi = NLMSG_DATA(nh);

            // Ignore events for interfaces other than wlan0
            if (ifi->ifi_index != wlan0_ifindex)
                continue;

            bool new_state = ifi->ifi_flags & IFF_RUNNING;
            if (new_state != wifi_connected) {
                wifi_connected = new_state;
                write_wifi_status();
            }
        }
    }
}

// --- Main ------------------------------------------------------------------

int main(void) {
    init_i2c();

    // Wait for gamepad to create the shared memory segment
    while ((shm_fd = shm_open("my_shm", O_RDONLY, 0666)) == -1) {
        if (errno == ENOENT) sleep(1);
        else { perror("shm_open"); close(i2c_fd); return 1; }
    }
    shared_data = mmap(0, sizeof(SharedData), PROT_READ, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        close(i2c_fd);
        return 1;
    }

    init_wifi_monitoring();

    bool prev_left_switch = !shared_data->status_flags.bits.left_switch;
    set_wifi_enabled(prev_left_switch);

    if (netlink_fd == -1) {
        fprintf(stderr, "WiFi monitoring unavailable, exiting\n");
        close(i2c_fd);
        return 1;
    }

    while (1) {
        bool left_switch = !shared_data->status_flags.bits.left_switch;
        if (left_switch != prev_left_switch) {
            set_wifi_enabled(left_switch);
            prev_left_switch = left_switch;
        }

        check_wifi_status();
        usleep(500000); // poll every 500ms
    }

    close(netlink_fd);
    munmap(shared_data, sizeof(SharedData));
    close(shm_fd);
    close(i2c_fd);
    return 0;
}
