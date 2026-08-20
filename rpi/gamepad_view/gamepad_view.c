/*
 * gamepad_view.c — PSPi V6 gamepad visualizer
 *
 * Reads the PSPi controller board over I2C (addr 0x10, /dev/i2c-1), validates
 * every packet with a CRC-16-CCITT over the first 9 bytes (required because
 * of the BCM2835 I2C clock-stretch bug on this board), and renders:
 *   - every button (PSP layout: face diamond △○✕□, L1/L2/R1/R2 shoulders,
 *     d-pad, bottom row HOME VOL- VOL+ MUTE SEL START), changing colour
 *     while pressed; MUTE reflects the muted state from the status byte
 *   - both analog stick positions as overlapping-circle indicators
 * on the display via KMS/DRM with double buffering (no cursor, no flicker).
 * The screen is only repainted when input actually changes, and the CRC
 * error counter updates occasionally, so the static image never flickers.
 *
 * Usage:
 *   ./gamepad_view --probe          one-shot I2C read + CRC check (no display)
 *   sudo ./gamepad_view [seconds]   live view until Ctrl-C or N seconds
 *
 * Build: make            (see Makefile; also supports cross-compiling)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <math.h>
#include <time.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#include "gfx_util.h"

/* ----------------------------- I2C protocol ----------------------------- */
/* 11-byte packet, little-endian:
 *  [0..1] buttons bitfield      [2] system voltage   [3] battery voltage
 *  [4]    status flags          [5..6] left stick X/Y
 *  [7..8] right stick X/Y: 7-bit position (bit0 masked off) + button bits
 *  [9..10] CRC-16-CCITT over bytes 0..8                                 */

#define I2C_BUS       "/dev/i2c-1"
#define I2C_ADDR      0x10
#define DATASIZE      11
#define CRC_LEN       9           /* CRC covers first 9 bytes */

/* Button bitfield (matches the rpi/gamepad driver) */
#define BTN_MUTE      0x0001
#define BTN_SELECT    0x0002
#define BTN_START     0x0004
#define BTN_CROSS     0x0008
#define BTN_SQUARE    0x0010
#define BTN_TRIANGLE  0x0020
#define BTN_CIRCLE    0x0040
#define BTN_R1        0x0080
#define BTN_L1        0x0100
#define BTN_DPAD_L    0x0200
#define BTN_DPAD_U    0x0400
#define BTN_DPAD_D    0x0800
#define BTN_DPAD_R    0x1000
#define BTN_VOL_P     0x2000
#define BTN_VOL_M     0x4000
#define BTN_HOME      0x8000

#define STATUS_PWR    0x10         /* status byte (pkt[4]) bit 4: power/SD key */
#define STATUS_MUTED  0x80         /* status byte (pkt[4]) bit 7 */

#define STICK_MASK    0xFE         /* right sticks: 7-bit position, bit0=btn */
#define AXIS_CENTER   127
#define AXIS_DEADZONE 20           /* matches driver's default axis_flat */

/* -------------------------------- palette ------------------------------- */

#define C_FRAME        0x444444
#define C_EDGE         0x666666
#define C_LABEL        0x888888
#define C_VAL          0xCCCCCC
#define C_TITLE        0x33DDFF   /* bright cyan accent */
#define C_UNPRESSED    0x2B2B2B
#define C_DZ           0x3A3A3A
#define C_CENTER       0x6A6A6A
#define C_AMBER        0xFFB000
#define C_WHITE        0xFFFFFF
#define C_GREEN        0x33CC66
#define C_RED          0xFF4A4A
#define C_CROSS        0x3399FF
#define C_CIRCLE       0xFF3B5C
#define C_SQUARE       0xFF6EC7
#define C_TRIANGLE     0x33CC66

/* ------------------------------ CRC-16-CCITT ---------------------------- */

static uint16_t crc16_table[256];

static void init_crc16_table(void)
{
    const uint16_t poly = 0x1021;
    for (int i = 0; i < 256; i++) {
        uint16_t crc = (uint16_t)(i << 8);
        for (int j = 0; j < 8; j++)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ poly) : (uint16_t)(crc << 1);
        crc16_table[i] = crc;
    }
}

static uint16_t crc16_ccitt(const uint8_t *data, int len)
{
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < len; i++)
        crc = (uint16_t)((crc << 8) ^ crc16_table[((crc >> 8) ^ data[i]) & 0xFF]);
    return crc;
}

/* --------------------------------- I2C ---------------------------------- */

typedef struct {
    uint16_t buttons;            /* raw button bitfield */
    uint8_t sx, sy;              /* left stick X/Y (0..255) */
    uint8_t rx, ry;              /* right stick X/Y (7-bit, masked) */
    bool l2, r2;                 /* extra buttons in right-stick bytes */
    bool muted;                  /* status flag: audio muted */
    bool power;                  /* status flag: power/SD key held */
    bool pwr_critical;           /* power held, shutdown imminent */
    unsigned crc_ok, crc_fail;   /* link statistics */
} PadState;

static int i2c_fd = -1;

static bool i2c_open(void)
{
    i2c_fd = open(I2C_BUS, O_RDWR);
    if (i2c_fd < 0) { perror("open " I2C_BUS); return false; }
    if (ioctl(i2c_fd, I2C_SLAVE, I2C_ADDR) < 0) { perror("I2C_SLAVE"); return false; }
    return true;
}

static bool parse_packet(const uint8_t *pkt, PadState *st)
{
    if (crc16_ccitt(pkt, CRC_LEN) != (uint16_t)((pkt[9] << 8) | pkt[10]))
        return false;
    st->buttons = (uint16_t)(pkt[0] | (pkt[1] << 8));
    st->sx = pkt[5];
    st->sy = pkt[6];
    st->rx = pkt[7] & STICK_MASK;
    st->ry = pkt[8] & STICK_MASK;
    st->l2 = (pkt[8] & 1) != 0;          /* matches driver: ry bit0 -> L2 */
    st->r2 = (pkt[7] & 1) != 0;          /*              rx bit0 -> R2 */
    st->muted = (pkt[4] & STATUS_MUTED) != 0;
    st->power = (pkt[4] & STATUS_PWR) != 0;
    return true;
}

/* one 11-byte read, CRC-validated; returns false on bus/CRC error */
static bool read_packet(PadState *st)
{
    uint8_t pkt[DATASIZE];
    ssize_t n = read(i2c_fd, pkt, DATASIZE);
    if (n < (ssize_t)DATASIZE) return false;
    return parse_packet(pkt, st);
}

/* --------------------------------- probe -------------------------------- */

static void probe(void)
{
    printf("PSPi gamepad probe: %s @ 0x%02X\n", I2C_BUS, I2C_ADDR);
    for (int t = 0; t < 20; t++) {
        uint8_t pkt[DATASIZE];
        ssize_t n = read(i2c_fd, pkt, DATASIZE);
        if (n != (ssize_t)DATASIZE) {
            printf("  try %d: read %zd/%d bytes (bus error)\n", t, n, DATASIZE);
            usleep(20000);
            continue;
        }
        uint16_t got = (uint16_t)((pkt[9] << 8) | pkt[10]);
        uint16_t calc = crc16_ccitt(pkt, CRC_LEN);
        printf("  packet: ");
        for (int i = 0; i < DATASIZE; i++) printf("%02X ", pkt[i]);
        printf("\n  crc16-ccitt: computed 0x%04X packet 0x%04X -> %s\n",
               calc, got, calc == got ? "OK" : "FAIL");
        if (calc != got) { usleep(20000); continue; }

        PadState st = {0};
        parse_packet(pkt, &st);
        printf("  buttons 0x%04X  L1=%d R1=%d L2=%d R2=%d SEL=%d START=%d "
               "dpad=%d%d%d%d home=%d vol=%d%d mute=%d muted_state=%d power=%d\n",
               st.buttons, !!(st.buttons & BTN_L1), !!(st.buttons & BTN_R1),
               st.l2, st.r2, !!(st.buttons & BTN_SELECT), !!(st.buttons & BTN_START),
               !!(st.buttons & BTN_DPAD_U), !!(st.buttons & BTN_DPAD_D),
               !!(st.buttons & BTN_DPAD_L), !!(st.buttons & BTN_DPAD_R),
               !!(st.buttons & BTN_HOME),
               !!(st.buttons & BTN_VOL_P), !!(st.buttons & BTN_VOL_M),
               !!(st.buttons & BTN_MUTE), st.muted, st.power);
        printf("  cross=%d square=%d triangle=%d circle=%d\n",
               !!(st.buttons & BTN_CROSS), !!(st.buttons & BTN_SQUARE),
               !!(st.buttons & BTN_TRIANGLE), !!(st.buttons & BTN_CIRCLE));
        printf("  left  stick: X=%3d Y=%3d\n", st.sx, st.sy);
        printf("  right stick: X=%3d Y=%3d (7-bit, bit0=%d/%d)\n",
               st.rx, st.ry, st.r2, st.l2);
        return;
    }
    printf("  probe failed: no CRC-valid packet after 20 tries\n");
}

/* ------------------------------ stick widget ---------------------------- */

static uint32_t stick_dot_color(int mag, int maxd)
{
    if (mag < maxd / 6) return C_WHITE;          /* effectively centered */
    if (mag < maxd * 2 / 3) return C_GREEN;      /* deflected */
    if (mag < maxd * 8 / 9) return 0xFFCC00;     /* far out */
    return C_RED;                                /* at the edge */
}

static void draw_stick(Canvas *c, int cx, int cy, int R, int maxd, int dotr,
                       int vx, int vy, const char *label, int ty,
                       const char *readout)
{
    /* rim + axis ticks + deadzone ring + center dot */
    ring_circle(c, cx, cy, R, 3, C_FRAME);
    draw_line(c, cx - R - 10, cy, cx - R + 12, cy, 2, C_EDGE);
    draw_line(c, cx + R - 12, cy, cx + R + 10, cy, 2, C_EDGE);
    draw_line(c, cx, cy - R - 10, cx, cy - R + 12, 2, C_EDGE);
    draw_line(c, cx, cy + R - 12, cx, cy + R + 10, 2, C_EDGE);
    int dz = maxd * AXIS_DEADZONE / AXIS_CENTER;
    ring_circle(c, cx, cy, dz, 1, C_DZ);
    fill_circle(c, cx, cy, 3, C_CENTER);

    /* position dot (scaled from the ADC range, deadzone in the color) */
    int ox = (vx - AXIS_CENTER) * maxd / AXIS_CENTER;
    int oy = (vy - AXIS_CENTER) * maxd / AXIS_CENTER;
    if (ox > maxd) ox = maxd;
    if (ox < -maxd) ox = -maxd;
    if (oy > maxd) oy = maxd;
    if (oy < -maxd) oy = -maxd;
    int mag = (int)hypot(ox, oy);
    uint32_t dot_col = stick_dot_color(mag, maxd);
    if (mag > maxd * AXIS_DEADZONE / AXIS_CENTER)
        ring_circle(c, cx + ox, cy + oy, dotr + 5, 2, dot_col);   /* halo */
    fill_circle(c, cx + ox, cy + oy, dotr, dot_col);

    /* labels centered above the stick */
    draw_text(c, cx - ((int)strlen(label) * 12 - 2) / 2, ty, label, 2, C_LABEL);
    draw_text(c, cx - ((int)strlen(readout) * 12 - 2) / 2, ty + 16, readout, 2, C_VAL);
}

/* ------------------------------ button widgets -------------------------- */

typedef struct { int x, y, r, pressed; const char *tag; } Btn;

static void draw_face_button(Canvas *c, Btn *b)
{
    uint32_t fill, sym;
    switch (b->tag[0]) {
        case 'X': fill = C_CROSS;    sym = C_WHITE; break;   /* cross   */
        case 'O': fill = C_CIRCLE;   sym = C_WHITE; break;   /* circle  */
        case 'S': fill = C_SQUARE;   sym = C_WHITE; break;   /* square  */
        case 'T': fill = C_TRIANGLE; sym = C_WHITE; break;   /* triangle*/
        default:  fill = C_AMBER;    sym = C_WHITE; break;
    }
    if (!b->pressed) { fill = C_UNPRESSED; sym = C_EDGE; }
    fill_circle(c, b->x, b->y, b->r, fill);
    ring_circle(c, b->x, b->y, b->r, 2, b->pressed ? C_WHITE : C_FRAME);

    int s = b->r - 12;                  /* symbol half-size */
    switch (b->tag[0]) {
        case 'X':   /* diagonal cross, same bounding size as the others */
            draw_line(c, b->x - s + 2, b->y - s + 2, b->x + s - 2, b->y + s - 2, 4, sym);
            draw_line(c, b->x - s + 2, b->y + s - 2, b->x + s - 2, b->y - s + 2, 4, sym);
            break;
        case 'O':
            ring_circle(c, b->x, b->y, s, 4, sym);
            break;
        case 'S':
            rect_outline(c, b->x - s, b->y - s, s * 2, s * 2, 4, sym);
            break;
        case 'T':   /* triangle, 2px high so its visual mass stays centered */
            fill_triangle(c, b->x, b->y - s - 2, b->x - s, b->y + s - 2,
                          b->x + s, b->y + s - 2, sym);
            break;
    }
}

static void draw_tag_rect(Canvas *c, int x, int y, int w, int h,
                          const char *tag, bool pressed)
{
    fill_rect(c, x, y, w, h, pressed ? C_AMBER : C_UNPRESSED);
    rect_outline(c, x, y, w, h, 2, pressed ? C_WHITE : C_FRAME);
    int len = (int)strlen(tag);
    int scale = (len * 12 - 2 <= w) ? 2 : 1;    /* largest scale that fits */
    int tw = len * 6 * scale - (scale == 2 ? 2 : 1);
    int ty = y + (h - 7 * scale) / 2;
    draw_text(c, x + (w - tw) / 2, ty, tag, scale, pressed ? C_WHITE : C_LABEL);
}

/* --------------------------------- layout -------------------------------- */

#define LX 115
#define LY 400
#define RX 685
#define RY 400

static void draw_frame(Canvas *c, uint16_t btns, bool l2, bool r2, bool muted,
                       bool power, bool pwr_critical,
                       int lx, int ly, int rxx, int ryy, unsigned crc_fail)
{
    clear(c);

    /* header */
    draw_text(c, 16, 12, "PSPI GAMEPAD VIEWER", 2, C_TITLE);
    char status[64];
    snprintf(status, sizeof status, "CRC ERRORS %u", crc_fail);
    int sx = c->d->w - 16 - ((int)strlen(status) * 12 - 2);
    draw_text(c, sx, 12, status, 2, crc_fail ? C_RED : C_GREEN);

    /* shoulder triggers */
    draw_tag_rect(c, 40, 30, 110, 32, "L1", btns & BTN_L1);
    draw_tag_rect(c, 40, 68, 110, 32, "L2", l2);
    draw_tag_rect(c, 650, 30, 110, 32, "R1", btns & BTN_R1);
    draw_tag_rect(c, 650, 68, 110, 32, "R2", r2);

    /* bottom row between the sticks: HOME VOL- VOL+ MUTE SEL START */
    draw_tag_rect(c, 198, 402, 64, 32, "HOME",  btns & BTN_HOME);
    draw_tag_rect(c, 270, 402, 56, 32, "VOL-",  btns & BTN_VOL_M);
    draw_tag_rect(c, 334, 402, 56, 32, "VOL+",  btns & BTN_VOL_P);
    draw_tag_rect(c, 398, 402, 64, 32, "MUTE",  muted);
    draw_tag_rect(c, 470, 402, 64, 32, "SEL",   btns & BTN_SELECT);
    draw_tag_rect(c, 542, 402, 64, 32, "START", btns & BTN_START);

    /* d-pad, horizontally centered with the left stick (x=115) */
    {
        bool up = btns & BTN_DPAD_U, down = btns & BTN_DPAD_D;
        bool left = btns & BTN_DPAD_L, right = btns & BTN_DPAD_R;
        /* base cross: two bars, arms all 60px long, thickness 34 */
        fill_rect(c,  98, 140,  34, 120, C_UNPRESSED);   /* vertical  bar  */
        fill_rect(c,  55, 183, 120,  34, C_UNPRESSED);   /* horizontal bar */
        rect_outline(c,  98, 140,  34, 120, 2, C_FRAME);
        rect_outline(c,  55, 183, 120,  34, 2, C_FRAME);
        fill_circle(c, 115, 200, 4, C_EDGE);             /* center hub dot */
        /* press highlights light the arm only, stopping at the + hub */
        if (up)    fill_rect(c,  98, 140, 34, 43, C_AMBER);
        if (down)  fill_rect(c,  98, 217, 34, 43, C_AMBER);
        if (left)  fill_rect(c,  55, 183, 43, 34, C_AMBER);
        if (right) fill_rect(c, 132, 183, 43, 34, C_AMBER);

        /* direction arrows on the resting arms */
        fill_triangle(c, 115, 154, 106, 168, 124, 168, C_LABEL);  /* up    */
        fill_triangle(c, 115, 246, 106, 232, 124, 232, C_LABEL);  /* down  */
        fill_triangle(c,  68, 200,  82, 191,  82, 209, C_LABEL);  /* left  */
        fill_triangle(c, 162, 200, 148, 191, 148, 209, C_LABEL);  /* right */
    }

    /* face buttons: PSP diamond (△ top, ○ right, ✕ bottom, □ left),
       horizontally centered with the right stick (x=685) */
    Btn tri = { 685, 145, 24, btns & BTN_TRIANGLE, "T" };
    Btn sq  = { 630, 200, 24, btns & BTN_SQUARE,   "S" };
    Btn circ = { 740, 200, 24, btns & BTN_CIRCLE,  "O" };
    Btn crs = { 685, 255, 24, btns & BTN_CROSS,    "X" };
    draw_face_button(c, &tri);
    draw_face_button(c, &sq);
    draw_face_button(c, &circ);
    draw_face_button(c, &crs);

    /* sticks: equal size, bottom-left and bottom-right */
    char lr[32], rr[32];
    snprintf(lr, sizeof lr, "LX %3d LY %3d", lx, ly);
    snprintf(rr, sizeof rr, "RX %3d RY %3d", rxx, ryy);
    draw_stick(c, LX, LY, 65, 42, 9, lx, ly, "LEFT STICK", 285, lr);
    draw_stick(c, RX, RY, 65, 42, 9, rxx, ryy, "RIGHT STICK", 285, rr);

    /* power-button indicator: far bottom-right corner, touching the edges */
    if (power) {
        uint32_t pc = pwr_critical ? C_RED : C_AMBER;
        fill_rect(c, 744, 444, 56, 36, C_UNPRESSED);   /* flush w/ edges */
        rect_outline(c, 744, 444, 56, 36, 2, pc);
        ring_circle(c, 756, 462, 7, 3, pc);            /* power symbol */
        fill_rect(c, 753, 448, 6, 7, pc);              /* stem */
        draw_text(c, 769, 456, "PWR", 1, pc);
    }
}

/* --------------------------------- main --------------------------------- */

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(int argc, char **argv)
{
    int run_secs = 0;
    bool do_probe = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--probe") == 0) do_probe = true;
        else run_secs = atoi(argv[i]);
    }

    init_crc16_table();
    if (!i2c_open()) return 1;

    if (do_probe) { probe(); return 0; }

    /* quick I2C sanity check before taking over the display */
    PadState st = {0};
    bool got_pkt = false;
    for (int i = 0; i < 10 && !got_pkt; i++) got_pkt = read_packet(&st);
    if (!got_pkt) {
        fprintf(stderr, "error: no CRC-valid gamepad packet (device at 0x%02X?)\n",
                I2C_ADDR);
        return 1;
    }
    printf("gamepad link OK (buttons=0x%04X sticks=%d,%d)\n", st.buttons, st.sx, st.sy);

    Display disp;
    const char *cname = NULL;
    if (!display_init(&disp, &cname)) return 1;
    Canvas cv = { .d = &disp };

    double t0 = now_sec();
    unsigned frames = 0;
    PadState prev = {0};

    /* initial frame so the screen isn't blank before the first poll */
    draw_frame(&cv, 0, false, false, false, false, false,
               AXIS_CENTER, AXIS_CENTER, AXIS_CENTER, AXIS_CENTER, 0);
    present(&disp);
    frames++;

    double pwr_since = 0.0;      /* time power key became pressed */
    unsigned link_fail = 0;      /* consecutive CRC-valid-less polls */

    while (1) {
        /* poll up to 3 times; keep last good state on failure */
        bool ok = false;
        for (int i = 0; i < 3 && !ok; i++) ok = read_packet(&st);
        if (ok) {
            link_fail = 0;
        } else {
            /* The screen intentionally freezes on the last good state while
               the link is down (that is the point of the display), but a
               stale power flag must never power the system off: if the board
               drops off the I2C bus mid-hold we can't tell "still held" from
               "disconnected", so once the link has been dead for a while,
               drop the power flag and let a later good packet re-raise it. */
            link_fail++;
            if (link_fail >= 50) {
                st.power = false;
                st.pwr_critical = false;
            }
        }

        double now = now_sec();

        /* power key: popup while held; 500 ms consecutive hold -> shutdown */
        if (st.power && !prev.power) pwr_since = now;
        if (!st.power && prev.power) pwr_since = 0.0;
        st.pwr_critical = st.power && (now - pwr_since) >= 0.38;
        if (st.power && (now - pwr_since) >= 0.50) {
            printf("power key held 500 ms - shutting down\n");
            fflush(stdout);
            if (system("poweroff") == -1) perror("poweroff");
            return 0;
        }

        /* redraw only when something visible actually changed */
        bool dirty = false;
        if (ok) {
            st.crc_ok++;
            dirty = (st.buttons != prev.buttons) ||
                    (st.l2 != prev.l2) || (st.r2 != prev.r2) ||
                    (st.muted != prev.muted) ||
                    (st.power != prev.power) ||
                    (st.pwr_critical != prev.pwr_critical) ||
                    abs((int)st.sx - (int)prev.sx) >= 2 ||
                    abs((int)st.sy - (int)prev.sy) >= 2 ||
                    abs((int)st.rx - (int)prev.rx) >= 2 ||
                    abs((int)st.ry - (int)prev.ry) >= 2;
        } else {
            st.crc_fail++;          /* shown on screen only when it changes */
            dirty = (st.crc_fail != prev.crc_fail);
        }
        if (dirty) {
            prev = st;
            draw_frame(&cv, st.buttons, st.l2, st.r2, st.muted, st.power,
                       st.pwr_critical, st.sx, st.sy, st.rx, st.ry, st.crc_fail);
            present(&disp);
            frames++;
        }

        if (run_secs > 0 && (now - t0) >= run_secs) break;
        usleep(8000);               /* ~100 Hz poll */
    }

    printf("done: %u redraws, crc ok=%u errors=%u\n", frames, st.crc_ok, st.crc_fail);
    return 0;
}