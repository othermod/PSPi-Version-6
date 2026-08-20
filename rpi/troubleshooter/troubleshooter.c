/*
 * troubleshooter.c — PSPi V6 gamepad visualizer
 *
 * Reads the PSPi controller board over I2C (addr 0x10, /dev/i2c-1), validates
 * every packet with a CRC-16-CCITT over the first 9 bytes (required because
 * of the BCM2835 I2C clock-stretch bug on this board), and renders:
 *   - every button (PSP layout: face diamond △○✕□, L1/L2/R1/R2 shoulders,
 *     d-pad, bottom row HOME VOL- VOL+ MUTE SEL START), changing colour
 *     while pressed; MUTE reflects the muted state from the status byte
 *   - both analog stick positions as overlapping-circle indicators
 *   - a bottom strip: WiFi state (green/red), backlight level (8 segments),
 *     and the power-key popup (PWR, fills amber->red as the shutdown hold
 *     progresses; red = shutdown imminent)
 * on the display via KMS/DRM with double buffering (no cursor, no flicker).
 * The screen is only repainted when input actually changes, so the static
 * image never flickers.
 *
 * Usage:
 *   ./troubleshooter --probe          one-shot I2C read + CRC check (no display)
 *   sudo ./troubleshooter [seconds]   live view until Ctrl-C or N seconds
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
#include <signal.h>
#include <sys/wait.h>
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
#define STATUS_WIFI   0x40         /* status byte (pkt[4]) bit 6: left switch =
                                       raw WiFi switch position; the wifi
                                       monitor treats WIFI ENABLED as !leftSwitch */
#define STATUS_BRIGHT 0x07         /* status byte (pkt[4]) bits 0-2: backlight */
#define STATUS_MUTED  0x80         /* status byte (pkt[4]) bit 7 */

#define STICK_MASK    0xFE         /* right sticks: 7-bit position, bit0=btn */
#define AXIS_CENTER   127
#define AXIS_DEADZONE 20           /* matches driver's default axis_flat */

/* -------------------------------- palette ------------------------------- */

#define C_FRAME        0x444444
#define C_EDGE         0x666666
#define C_LABEL        0x888888
#define C_VAL          0xCCCCCC
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
    bool wifi;                   /* status flag: WiFi link switch is ON (the
                                    raw bit is active-low — monitor does
                                    set_wifi_enabled(!left_switch)) */
    uint8_t brightness;          /* backlight level from status bits 0-2 (0..7,
                                    dimmest..brightest); the bar shows +1 */
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
    st->wifi = (pkt[4] & STATUS_WIFI) == 0;   /* bit is raw switch pos; wifi on = clear */
    st->brightness = pkt[4] & STATUS_BRIGHT;
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

/* linear RGB interpolation between two 0xRRGGBB colors (integer math) */
static uint32_t lerp_rgb(uint32_t c0, uint32_t c1, int t, int span)
{
    if (span <= 0 || t >= span) return c1;
    if (t <= 0) return c0;
    int r = (int)((c0 >> 16) & 0xFF) +
            ((int)((c1 >> 16) & 0xFF) - (int)((c0 >> 16) & 0xFF)) * t / span;
    int g = (int)((c0 >> 8) & 0xFF) +
            ((int)((c1 >> 8) & 0xFF) - (int)((c0 >> 8) & 0xFF)) * t / span;
    int b = (int)(c0 & 0xFF) +
            ((int)(c1 & 0xFF) - (int)(c0 & 0xFF)) * t / span;
    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | (uint32_t)b;
}

/* stick dot colour: white in the centre zone, then a smooth
   green -> yellow -> red gradient with deflection (no banding) */
static uint32_t stick_dot_color(int mag, int maxd)
{
    if (mag < maxd / 6) return C_WHITE;                  /* effectively centred */
    if (mag < maxd * 2 / 3)                              /* green -> yellow */
        return lerp_rgb(C_GREEN, 0xFFCC00, mag - maxd / 6,
                        maxd * 2 / 3 - maxd / 6);
    return lerp_rgb(0xFFCC00, C_RED, mag - maxd * 2 / 3, /* yellow -> red */
                    maxd - maxd * 2 / 3);
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

    /* labels centered above the stick; the readout sits a few px below the
       scale-2 label (14px tall) so the two lines don't touch */
    draw_text(c, cx - ((int)strlen(label) * 12 - 2) / 2, ty, label, 2, C_LABEL);
    draw_text(c, cx - ((int)strlen(readout) * 12 - 2) / 2, ty + 20, readout, 2, C_VAL);
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

static void draw_leader(Canvas *c, int x, int y, int to, int dir);  /* defined below */

#define LX 115                          /* left stick anchor (center) */
#define LY 400
#define RX 685                          /* right stick anchor (center) */
#define RY 400
#define ROW_Y (LY - 16)                 /* bottom button row (32px tall),
                                           vertically centered on the sticks */

/* trigger tags, centered on their stick-side cluster (d-pad / face diamond) */
#define TAG_W    110
#define L_TAG_CX 115
#define R_TAG_CX 685

/* d-pad: centered on (DPAD_X, DPAD_Y); arms DPAD_ARM long, DPAD_TH thick
   (10% bigger than the original layout) */
#define DPAD_X   115
#define DPAD_Y   180
#define DPAD_ARM 66
#define DPAD_TH  38

/* LCD data-line bit-slice band, always on. Eight swatches per row each show
   exactly one bit of its channel (bit 7 leftmost -> bit 0 rightmost). Rows
   R, G, B set that bit on a single channel; row W sets it on ALL three at
   once, so a broken line there turns the swatch a tint of the remaining
   channels (e.g. dead RED bit 4 => dark cyan) -- never black or white --
   which is visible against the pure-black screen. No bezel, no per-swatch
   outlines: swatches sit directly on the cleared black framebuffer so color
   differences show clearly. Vertically centered on the d-pad (DPAD_Y). */
#define LCD_CX    393   /* band center x (in the free gap, x 181..606) */
#define LCD_CY    DPAD_Y /* band center y: aligned with the d-pad center */
#define LCD_W     34    /* swatch width */
#define LCD_H     28    /* swatch height */
#define LCD_GAP   4     /* gap between swatches */

static void draw_lcd_test(Canvas *c)
{
    static const uint32_t rowcol[4] = { C_RED, C_GREEN, C_CROSS, C_WHITE }; /* R G B W */
    static const char *label[4] = { "R", "G", "B", "W" };

    int grid_w = 8 * (LCD_W + LCD_GAP);
    int grid_h = 4 * (LCD_H + LCD_GAP);
    int gx = LCD_CX - grid_w / 2 + 22;    /* leave room for the R/G/B/W labels */
    int gy = LCD_CY - grid_h / 2;

    for (int row = 0; row < 4; row++) {
        /* label, vertically centered on the row */
        draw_text(c, gx - 24, gy + row * (LCD_H + LCD_GAP) + (LCD_H - 14) / 2,
                  label[row], 2, rowcol[row]);

        for (int col = 0; col < 8; col++) {
            int bit = 7 - col;                      /* bit 7 leftmost */
            uint32_t v = (uint32_t)(1 << bit);
            uint32_t color = row == 0 ? v << 16               /* red   */
                            : row == 1 ? v << 8               /* green */
                            : row == 2 ? v                    /* blue  */
                            :            (v << 16) | (v << 8) | v;  /* white: all 3 */
            int sx = gx + col * (LCD_W + LCD_GAP);
            int sy = gy + row * (LCD_H + LCD_GAP);
            fill_rect(c, sx, sy, LCD_W, LCD_H, color);
        }
    }
}

static void draw_frame(Canvas *c, const PadState *st, bool audio_on, double pwr_fill)
{
    clear(c);

    /* shoulder triggers, centered over their stick-side cluster */
    draw_tag_rect(c, L_TAG_CX - TAG_W / 2, 10, TAG_W, 32, "L1", st->buttons & BTN_L1);
    draw_tag_rect(c, L_TAG_CX - TAG_W / 2, 48, TAG_W, 32, "L2", st->l2);
    draw_tag_rect(c, R_TAG_CX - TAG_W / 2, 10, TAG_W, 32, "R1", st->buttons & BTN_R1);
    draw_tag_rect(c, R_TAG_CX - TAG_W / 2, 48, TAG_W, 32, "R2", st->r2);

    /* audio-test hint, top center between the trigger tags: "ENABLE AUDIO
       TEST" while the tone is off (white), "DISABLE AUDIO TEST" once it's
       playing (amber). Thick horizontal leaders run from the text's left/right
       edges straight out to just short of the L1/R1 boxes — all at y=26, the
       common vertical center of the text AND the boxes — with the arrowhead
       pointing AT each box. */
    {
        const char *label = audio_on ? "DISABLE AUDIO TEST" : "ENABLE AUDIO TEST";
        uint32_t col = audio_on ? C_AMBER : C_WHITE;
        int w = (int)strlen(label) * 12 - 2;      /* scale-2 text width */
        int xl = (c->d->w - w) / 2;               /* text left edge */
        draw_text(c, xl, 19, label, 2, col);

        int ty = 26;                              /* text & L1/R1 box center */
        draw_leader(c, xl + w + 14, ty, 618, 1);  /* -> R1: arrowhead stays at 618 (box edge x=630) */
        draw_leader(c, xl - 14, ty, 182, -1);     /* -> L1: arrowhead stays at 182 (box edge x=170) */
    }

    /* bottom row between the sticks: HOME VOL- VOL+ MUTE SEL START, raised
       to sit vertically centered on the stick axis */
    draw_tag_rect(c, 198, ROW_Y, 64, 32, "HOME",  st->buttons & BTN_HOME);
    draw_tag_rect(c, 270, ROW_Y, 56, 32, "VOL-",  st->buttons & BTN_VOL_M);
    draw_tag_rect(c, 334, ROW_Y, 56, 32, "VOL+",  st->buttons & BTN_VOL_P);
    draw_tag_rect(c, 398, ROW_Y, 64, 32, "MUTE",  st->muted);
    draw_tag_rect(c, 470, ROW_Y, 64, 32, "SEL",   st->buttons & BTN_SELECT);
    draw_tag_rect(c, 542, ROW_Y, 64, 32, "START", st->buttons & BTN_START);

    /* d-pad, centered on (DPAD_X, DPAD_Y): two crossing bars, arms
       DPAD_ARM long, thickness DPAD_TH */
    {
        bool up = st->buttons & BTN_DPAD_U, down = st->buttons & BTN_DPAD_D;
        bool left = st->buttons & BTN_DPAD_L, right = st->buttons & BTN_DPAD_R;
        fill_rect(c, DPAD_X - DPAD_TH / 2, DPAD_Y - DPAD_ARM, DPAD_TH, DPAD_ARM * 2, C_UNPRESSED);   /* vertical  bar */
        fill_rect(c, DPAD_X - DPAD_ARM, DPAD_Y - DPAD_TH / 2, DPAD_ARM * 2, DPAD_TH, C_UNPRESSED);   /* horizontal bar */
        rect_outline(c, DPAD_X - DPAD_TH / 2, DPAD_Y - DPAD_ARM, DPAD_TH, DPAD_ARM * 2, 2, C_FRAME);
        rect_outline(c, DPAD_X - DPAD_ARM, DPAD_Y - DPAD_TH / 2, DPAD_ARM * 2, DPAD_TH, 2, C_FRAME);
        fill_circle(c, DPAD_X, DPAD_Y, 4, C_EDGE);       /* center hub dot */
        /* press highlights light the arm only, stopping at the + hub */
        if (up)    fill_rect(c, DPAD_X - DPAD_TH / 2, DPAD_Y - DPAD_ARM, DPAD_TH, DPAD_ARM - DPAD_TH / 2, C_AMBER);
        if (down)  fill_rect(c, DPAD_X - DPAD_TH / 2, DPAD_Y + DPAD_TH / 2, DPAD_TH, DPAD_ARM - DPAD_TH / 2, C_AMBER);
        if (left)  fill_rect(c, DPAD_X - DPAD_ARM, DPAD_Y - DPAD_TH / 2, DPAD_ARM - DPAD_TH / 2, DPAD_TH, C_AMBER);
        if (right) fill_rect(c, DPAD_X + DPAD_TH / 2, DPAD_Y - DPAD_TH / 2, DPAD_ARM - DPAD_TH / 2, DPAD_TH, C_AMBER);

        /* direction arrows on the resting arms */
        fill_triangle(c, 115, 130, 106, 144, 124, 144, C_LABEL);  /* up    */
        fill_triangle(c, 115, 230, 106, 216, 124, 216, C_LABEL);  /* down  */
        fill_triangle(c,  65, 180,  79, 171,  79, 189, C_LABEL);  /* left  */
        fill_triangle(c, 164, 180, 150, 171, 150, 189, C_LABEL);  /* right */
    }

    /* face buttons: PSP diamond (△ top, ○ right, ✕ bottom, □ left),
       centered on the right stick's column (x=685) */
    Btn tri = { 685, 125, 24, st->buttons & BTN_TRIANGLE, "T" };
    Btn sq  = { 630, 180, 24, st->buttons & BTN_SQUARE,   "S" };
    Btn circ = { 740, 180, 24, st->buttons & BTN_CIRCLE,  "O" };
    Btn crs = { 685, 235, 24, st->buttons & BTN_CROSS,    "X" };
    draw_face_button(c, &tri);
    draw_face_button(c, &sq);
    draw_face_button(c, &circ);
    draw_face_button(c, &crs);

    /* sticks: equal size, bottom-left and bottom-right */
    char lr[32], rr[32];
    snprintf(lr, sizeof lr, "LX %3d LY %3d", st->sx, st->sy);
    snprintf(rr, sizeof rr, "RX %3d RY %3d", st->rx, st->ry);
    draw_stick(c, LX, LY, 49, 31, 7, st->sx, st->sy, "LEFT STICK", 285, lr);
    draw_stick(c, RX, RY, 49, 31, 7, st->rx, st->ry, "RIGHT STICK", 285, rr);

    /* bottom strip: WiFi state (left), backlight level (center),
       power-key indicator (right corner, only while held); the wifi bit is
       active-low (see parse_packet) */
    {
        uint32_t wc = st->wifi ? C_GREEN : C_RED;
        fill_rect(c, 0, 444, 56, 36, C_UNPRESSED);      /* flush w/ edges */
        rect_outline(c, 0, 444, 56, 36, 2, wc);
        draw_text(c, (56 - (4 * 12 - 2)) / 2, 444 + (36 - 14) / 2, "WIFI", 2, wc);
    }
    {
        /* status holds 0..7; show 1..8 blocks so the lowest setting still
           leaves one segment lit and brightest shows all 8 */
        int lvl = st->brightness + 1;
        if (lvl > 8) lvl = 8;
        int total = 8 * 14 + 7 * 4;             /* 8 segments, 14px + 4px gaps */
        int x0 = (c->d->w - total) / 2;         /* centered */
        fill_rect(c, x0 - 9, 444, total + 18, 36, C_UNPRESSED);
        rect_outline(c, x0 - 9, 444, total + 18, 36, 2, C_FRAME);
        for (int i = 0; i < 8; i++)
            fill_rect(c, x0 + i * 18, 454, 14, 16, i < lvl ? C_WHITE : C_DZ);
    }
    if (st->power) {
        uint32_t pc = st->pwr_critical ? C_RED : C_AMBER;
        const int bx = 744, by = 444, bw = 56, bh = 36;
        fill_rect(c, bx, by, bw, bh, C_UNPRESSED);    /* flush w/ edges */
        rect_outline(c, bx, by, bw, bh, 2, pc);
        /* fill bottom-up by power-hold progress (0..1); 0.25 s => half full,
           0.50 s => full (then shutdown). White text stays readable on the
           fill. */
        int fh = (int)((bh - 4) * (pwr_fill > 1.0 ? 1.0 : pwr_fill));
        if (fh > 0) fill_rect(c, bx + 2, by + bh - 2 - fh, bw - 4, fh, pc);
        draw_text(c, bx + (bw - 34) / 2, by + (bh - 14) / 2, "PWR", 2, C_WHITE);   /* same y as WIFI (455) */
    }

    /* LCD data-line band, drawn last so it sits on top of the frame */
    draw_lcd_test(c);
}

/* ---------------------------- audio test loop --------------------------- */

#define AUDIO_HOLD_SECS 0.6   /* L1+R1 hold duration that toggles the test */
#define AUDIO_FREQ      440   /* test tone frequency (Hz) */

#define PWR_SHUTDOWN_SECS 0.50   /* power-key hold that shuts the system down */
#define PWR_CRITICAL_SECS 0.38   /* PWR fill turns red past this hold */

static pid_t audio_pid = -1;
static bool  audio_on = false;

/* Spawn a continuous, single-channel sine tone. speaker-test ships with the
   base image (raspios-trixie arm64-lite includes /usr/bin/speaker-test), so
   the patcher needs no extra provisioning and nothing here adds build deps.
   forked + setsid so troubleshooter's own death doesn't kill the tone;
   audio_cleanup() and the boot.sh restart loop remove strays. */
static void audio_start(void)
{
    pid_t pid = fork();
    if (pid < 0) { perror("fork speaker-test"); return; }
    if (pid == 0) {
        setsid();
        char f[16];
        snprintf(f, sizeof f, "%d", AUDIO_FREQ);
        execlp("speaker-test", "speaker-test",
               "-t", "sine", "-f", f, "-l", "0", "-c", "1",
               (char *)NULL);
        perror("exec speaker-test");
        _exit(127);
    }
    audio_pid = pid;
    audio_on = true;
    printf("audio test: %.0f Hz sine on (pid %d)\n", (double)AUDIO_FREQ, pid);
}

static void audio_stop(void)
{
    if (audio_pid > 0) {
        kill(audio_pid, SIGTERM);
        waitpid(audio_pid, NULL, 0);     /* reap; speaker-test dies promptly */
        audio_pid = -1;
    }
    audio_on = false;
    printf("audio test: off\n");
}

static void audio_toggle(void) { if (audio_on) audio_stop(); else audio_start(); }

static void audio_cleanup(void) { if (audio_pid > 0) audio_stop(); }

/* Leader line + arrowhead, drawn HORIZONTALLY at row y. The shaft runs from
   (x, y) toward x=to (dir +1 = arrow points right, -1 = left), stopping at
   the arrowhead's BASE so the arrow sits at the very end of the line; the
   arrowhead itself then spans base..to. Used to point at the L1/R1 trigger
   boxes from the audio-test hint text. */
static void draw_leader(Canvas *c, int x, int y, int to, int dir)
{
    int len = dir > 0 ? to - x : x - to;    /* total span */
    int head = 10;                          /* arrowhead length */
    draw_line(c, x, y, x + dir * (len - head), y, 5, C_EDGE);  /* shaft stops at head base */

    /* arrowhead: tip at x=to, base at to - dir*head */
    int tip_x = x + dir * len;
    fill_triangle(c, tip_x, y, tip_x - dir * head, y - 6, tip_x - dir * head, y + 6, C_EDGE);
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
    atexit(audio_cleanup);
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
    PadState init = {0};
    init.sx = init.sy = init.rx = init.ry = AXIS_CENTER;
    draw_frame(&cv, &init, false, 0.0);
    present(&disp);
    frames++;

    double pwr_since = 0.0;      /* time power key became pressed */
    double trig_since = 0.0;     /* time L1+R1 became pressed */
    bool prev_audio = false;     /* audio-test state for redraw detection */
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
        st.pwr_critical = st.power && (now - pwr_since) >= PWR_CRITICAL_SECS;
        if (st.power && (now - pwr_since) >= PWR_SHUTDOWN_SECS) {
            printf("power key held 500 ms - shutting down\n");
            fflush(stdout);
            if (system("poweroff") == -1) perror("poweroff");
            return 0;
        }

        /* audio test: hold L1+R1 ~0.6 s toggles the speaker sine. Gated on
           ok so a dead link with the triggers still held can't toggle by
           surprise; once fired, release the triggers before it can retoggle. */
        if (ok) {
            bool both = (st.buttons & (BTN_L1 | BTN_R1)) == (BTN_L1 | BTN_R1);
            bool both_prev = (prev.buttons & (BTN_L1 | BTN_R1)) == (BTN_L1 | BTN_R1);
            if (both && !both_prev) trig_since = now;
            if (!both && both_prev) trig_since = 0.0;
            if (both && trig_since > 0.0 && now - trig_since >= AUDIO_HOLD_SECS) {
                audio_toggle();
                trig_since = 0.0;       /* require a release before re-toggling */
            }
        }

        /* power-hold progress: 0..1 for the PWR fill indicator */
        double pwr_fill = st.power ? (now - pwr_since) / PWR_SHUTDOWN_SECS : 0.0;
        if (pwr_fill > 1.0) pwr_fill = 1.0;

        /* redraw only when something visible actually changed */
        bool dirty = false;
        if (ok) {
            st.crc_ok++;
            dirty = (st.buttons != prev.buttons) ||
                    (st.l2 != prev.l2) || (st.r2 != prev.r2) ||
                    (st.muted != prev.muted) ||
                    (audio_on != prev_audio) ||
                    (st.wifi != prev.wifi) ||
                    (st.brightness != prev.brightness) ||
                    (st.power != prev.power) ||
                    (st.pwr_critical != prev.pwr_critical) ||
                    abs((int)st.sx - (int)prev.sx) >= 2 ||
                    abs((int)st.sy - (int)prev.sy) >= 2 ||
                    abs((int)st.rx - (int)prev.rx) >= 2 ||
                    abs((int)st.ry - (int)prev.ry) >= 2;
        } else {
            /* CRC failures aren't shown on screen anymore; while the bus is
               down the only thing that can change the display is the stale
               power flag being dropped (link dead >50 polls) */
            st.crc_fail++;
            dirty = (st.power != prev.power) ||
                    (st.pwr_critical != prev.pwr_critical);
        }
        if (dirty || st.power) {
            /* st.power forces a redraw every poll while held so the PWR fill
               animates continuously; on release the power change dirtys. */
            prev = st;
            prev_audio = audio_on;
            draw_frame(&cv, &st, audio_on, pwr_fill);
            present(&disp);
            frames++;
        }

        if (run_secs > 0 && (now - t0) >= run_secs) break;
        usleep(8000);               /* ~100 Hz poll */
    }

    printf("done: %u redraws, crc ok=%u errors=%u\n", frames, st.crc_ok, st.crc_fail);
    return 0;
}