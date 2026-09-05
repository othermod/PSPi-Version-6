/*
 * firmware.c — PSPi V6 firmware flasher UI
 *
 * Full-screen (KMS/DRM) interactive firmware flashing tool for the ATmega8
 * controller board. Runs on a dedicated Raspberry Pi OS Lite image
 * (scripts/distros/firmware.sh) over the bit-banged i2c-gpio bus.
 *
 * Talks to the bootloader (I2C 0x29, CRC'd info/pins/pages protocol) and the
 * application firmware (I2C 0x10, gamepad packet protocol) to:
 *   - report whether the ATmega is in bootloader mode
 *   - report bootloader/app status: signature, verify state, flash fingerprint
 *   - compare the installed firmware fingerprint against the firmware.hex
 *     bundled in the image ("same/different version")
 *   - flash the bundled firmware on a button press, with progress + verify
 *
 * Display code is ported from rpi/troubleshooter (raw KMS/DRM UAPI, no
 * libdrm; double-buffered page flips with in-place fallback).
 *
 * Build: make 32 / make 64 (see Makefile; also supports cross-compiling)
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
#include <sys/mman.h>
#include <poll.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>

/* DRM_MODE_CONNECTED is a libdrm enum value, not in the kernel UAPI header;
   define it for the connector-status check below. */
#define DRM_MODE_CONNECTED 1

/* ------------------------------------------------------------------ */
/* DRM display (raw KMS ioctl UAPI -- no libdrm)                       */
/* ------------------------------------------------------------------ */

/* Double-buffered DRM display. Field layout matches rpi/troubleshooter so
   its display_init/present port drops in unchanged (piece 3). */
typedef struct {
    int fd;              /* drm fd (master) */
    int w, h;            /* mode resolution */
    int pitch;           /* buffer pitch in pixels */
    uint32_t crtc_id;
    uint32_t fb[2];      /* two framebuffer IDs */
    size_t size;         /* buffer size in bytes */
    uint8_t *map[2];     /* mmaps of the two buffers */
    int scan, paint;     /* which buffer is displayed / being painted */
    uint32_t *buf;       /* pixel pointer to the current paint target */
    bool flip_ok;        /* false if flips unsupported (paints in place) */
} Display;

typedef struct { Display *d; } Canvas;

/* libdrm's drmModeGetConnectorTypeName -- replicated here so we don't link
   libdrm just for this one string lookup. */
static const char *connector_type_name(uint32_t t)
{
    switch (t) {
    case DRM_MODE_CONNECTOR_Unknown:    return "Unknown";
    case DRM_MODE_CONNECTOR_VGA:        return "VGA";
    case DRM_MODE_CONNECTOR_DVII:       return "DVII";
    case DRM_MODE_CONNECTOR_DVID:       return "DVID";
    case DRM_MODE_CONNECTOR_DVIA:       return "DVIA";
    case DRM_MODE_CONNECTOR_Composite:  return "Composite";
    case DRM_MODE_CONNECTOR_SVIDEO:     return "SVideo";
    case DRM_MODE_CONNECTOR_Component:  return "Component";
    case DRM_MODE_CONNECTOR_9PinDIN:    return "9PinDIN";
    case DRM_MODE_CONNECTOR_DisplayPort:return "DisplayPort";
    case DRM_MODE_CONNECTOR_HDMIA:      return "HDMIA";
    case DRM_MODE_CONNECTOR_HDMIB:      return "HDMIB";
    case DRM_MODE_CONNECTOR_TV:         return "TV";
    case DRM_MODE_CONNECTOR_eDP:        return "eDP";
    case DRM_MODE_CONNECTOR_VIRTUAL:    return "Virtual";
    case DRM_MODE_CONNECTOR_DSI:        return "DSI";
    case DRM_MODE_CONNECTOR_DPI:        return "DPI";
    case DRM_MODE_CONNECTOR_WRITEBACK:  return "WriteBack";
    case DRM_MODE_CONNECTOR_SPI:        return "SPI";
    case DRM_MODE_CONNECTOR_USB:        return "USB";
    default:                            return "Unknown";
    }
}

/* Fetch a connector's full data (modes + metadata) via the two-pass
   DRM_IOCTL_MODE_GETCONNECTOR ioctl. Caller owns and must free *modes. The
   encoders/props arrays the ioctl also fills are discarded. */
static bool get_connector(int fd, uint32_t id,
                           uint32_t *conn_id, uint32_t *type,
                           uint32_t *encoder_id, uint32_t *connection,
                           uint32_t *count_modes,
                           struct drm_mode_modeinfo **modes)
{
    struct drm_mode_get_connector c;
    memset(&c, 0, sizeof c);
    c.connector_id = id;
    if (ioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &c)) return false;

    struct drm_mode_modeinfo *m =
        calloc(c.count_modes ? c.count_modes : 1, sizeof *m);
    uint32_t *encs    = calloc(c.count_encoders ? c.count_encoders : 1, sizeof *encs);
    uint32_t *props   = calloc(c.count_props   ? c.count_props   : 1, sizeof *props);
    uint64_t *propvals= calloc(c.count_props   ? c.count_props   : 1, sizeof *propvals);

    c.modes_ptr       = (uint64_t)(uintptr_t)m;
    c.encoders_ptr    = (uint64_t)(uintptr_t)encs;
    c.props_ptr       = (uint64_t)(uintptr_t)props;
    c.prop_values_ptr = (uint64_t)(uintptr_t)propvals;
    bool ok = ioctl(fd, DRM_IOCTL_MODE_GETCONNECTOR, &c) == 0;

    if (ok) {
        *conn_id      = c.connector_id;
        *type         = c.connector_type;
        *encoder_id   = c.encoder_id;
        *connection   = c.connection;
        *count_modes  = c.count_modes;
        *modes        = m;
    } else {
        free(m);
    }
    free(encs); free(props); free(propvals);
    return ok;
}

bool display_init(Display *d, const char **conn_name)
{
    /* Scan card0..card3 (a Pi 5 exposes several DRM devices; the PSPi LCD
       shows up as its own card under the pspi-lcd overlay). */
    char card[16];
    d->fd = -1;

    uint32_t connector_id = 0, ctype = 0, encoder_id = 0, crtc_id = 0;
    uint32_t count_modes = 0;
    struct drm_mode_modeinfo *modes = NULL;

    for (int ci = 0; ci < 4 && !connector_id; ci++) {
        snprintf(card, sizeof card, "/dev/dri/card%d", ci);
        int fd = open(card, O_RDWR);
        if (fd < 0) continue;
        if (ioctl(fd, DRM_IOCTL_SET_MASTER, 0) != 0) { close(fd); continue; }

        struct drm_mode_card_res res;
        memset(&res, 0, sizeof res);
        if (ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res)) { close(fd); continue; }

        uint32_t *crtcs = calloc(res.count_crtcs       ? res.count_crtcs       : 1, sizeof *crtcs);
        uint32_t *conns = calloc(res.count_connectors  ? res.count_connectors  : 1, sizeof *conns);
        res.crtc_id_ptr      = (uint64_t)(uintptr_t)crtcs;
        res.connector_id_ptr = (uint64_t)(uintptr_t)conns;
        /* Arrays we provide no pointers for: zero their counts or the kernel
           does put_user() through the NULL pointer and the call faults. */
        res.count_fbs      = 0;
        res.count_encoders = 0;
        if (ioctl(fd, DRM_IOCTL_MODE_GETRESOURCES, &res)) { free(crtcs); free(conns); close(fd); continue; }

        for (uint32_t i = 0; i < res.count_connectors && !connector_id; i++) {
            uint32_t cid, tp, eid, conn, cm;
            struct drm_mode_modeinfo *ms;
            if (!get_connector(fd, conns[i], &cid, &tp, &eid, &conn, &cm, &ms)) continue;
            if (conn == DRM_MODE_CONNECTED && cm > 0) {
                connector_id = cid; ctype = tp; encoder_id = eid;
                count_modes  = cm; modes = ms; d->fd = fd;
            } else {
                free(ms);
            }
        }

        if (connector_id) {
            if (encoder_id) {
                struct drm_mode_get_encoder e;
                memset(&e, 0, sizeof e);
                e.encoder_id = encoder_id;
                if (ioctl(fd, DRM_IOCTL_MODE_GETENCODER, &e) == 0 && e.crtc_id)
                    crtc_id = e.crtc_id;
            }
            if (!crtc_id && res.count_crtcs > 0) crtc_id = crtcs[0];
        }
        free(crtcs); free(conns);
        if (!connector_id) close(fd);
    }

    if (!connector_id) {
        fprintf(stderr, "error: no DRM card with a connected display "
                        "(run with sudo?)\n");
        return false;
    }
    if (conn_name) *conn_name = connector_type_name(ctype);

    struct drm_mode_modeinfo *mode = &modes[0];
    for (uint32_t i = 0; i < count_modes; i++)
        if (modes[i].type & DRM_MODE_TYPE_PREFERRED) { mode = &modes[i]; break; }

    d->crtc_id = crtc_id;
    d->w = mode->hdisplay;
    d->h = mode->vdisplay;
    d->pitch = 0; d->size = 0; d->scan = 0; d->paint = 1; d->flip_ok = true;

    /* create two dumb framebuffers (front/back) */
    for (int i = 0; i < 2; i++) {
        struct drm_mode_create_dumb cd = {
            .width = (uint32_t)d->w, .height = (uint32_t)d->h, .bpp = 32,
        };
        if (ioctl(d->fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd) != 0) { perror("CREATE_DUMB"); free(modes); return false; }

        struct drm_mode_fb_cmd fb;
        memset(&fb, 0, sizeof fb);
        fb.width = cd.width; fb.height = cd.height; fb.pitch = cd.pitch;
        fb.bpp = 32; fb.depth = 24; fb.handle = cd.handle;
        if (ioctl(d->fd, DRM_IOCTL_MODE_ADDFB, &fb) != 0) { perror("drmModeAddFB"); free(modes); return false; }
        d->fb[i] = fb.fb_id;

        struct drm_mode_map_dumb md = { .handle = cd.handle };
        if (ioctl(d->fd, DRM_IOCTL_MODE_MAP_DUMB, &md) != 0) { perror("MAP_DUMB"); free(modes); return false; }
        d->map[i] = mmap(NULL, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, d->fd, md.offset);
        if (d->map[i] == MAP_FAILED) { perror("mmap"); free(modes); return false; }
        d->pitch = cd.pitch / 4;
        d->size = cd.size;
    }
    d->buf = (uint32_t *)d->map[d->paint];

    struct drm_mode_crtc sc;
    memset(&sc, 0, sizeof sc);
    sc.crtc_id = crtc_id; sc.fb_id = d->fb[0]; sc.x = 0; sc.y = 0;
    sc.set_connectors_ptr = (uint64_t)(uintptr_t)&connector_id;
    sc.count_connectors = 1; sc.mode_valid = 1; sc.mode = *mode;
    if (ioctl(d->fd, DRM_IOCTL_MODE_SETCRTC, &sc) != 0) { perror("drmModeSetCrtc"); free(modes); return false; }

    struct drm_mode_cursor cur;
    memset(&cur, 0, sizeof cur);
    cur.crtc_id = crtc_id;            /* handle 0 hides the cursor plane */
    ioctl(d->fd, DRM_IOCTL_MODE_CURSOR, &cur);

    printf("display: %s %dx%d @%dHz\n",
           conn_name ? *conn_name : "?", d->w, d->h, mode->vrefresh);
    free(modes);
    return true;
}

void present(Display *d)
{
    if (!d->flip_ok) return;

    int issued = 0;
    for (int t = 0; t < 3; t++) {
        struct drm_mode_crtc_page_flip pf;
        memset(&pf, 0, sizeof pf);
        pf.crtc_id = d->crtc_id;
        pf.fb_id   = d->fb[d->paint];
        pf.flags   = DRM_MODE_PAGE_FLIP_EVENT;
        if (ioctl(d->fd, DRM_IOCTL_MODE_PAGE_FLIP, &pf) == 0) { issued = 1; break; }
        if (errno != EBUSY) break;
        usleep(30000);              /* CRTC still settling after setcrtc */
    }
    if (!issued) {
        d->flip_ok = false;         /* fall back to in-place painting */
        d->buf = (uint32_t *)d->map[d->scan];
        fprintf(stderr, "warning: page flip failed (%s), painting in place\n",
                strerror(errno));
        return;
    }

    /* block until the flip-complete event so the old buffer is safe to reuse,
       then swap scan/paint. If no completion event arrives within ~2 s (the
       only failure mode the page-flip ioctl itself can't report), the old
       buffer may still be scanned out -- painting on it would tear. Treat a
       silent timeout exactly like an explicit flip failure: fall back to
       painting in place on the scan buffer. */
    bool done = false;
    for (int w = 0; w < 200 && !done; w++) {
        struct pollfd pfd = { .fd = d->fd, .events = POLLIN };
        if (poll(&pfd, 1, 10) > 0) {
            struct drm_event_vblank ev;
            ssize_t n = read(d->fd, &ev, sizeof ev);
            if (n >= (ssize_t)sizeof(struct drm_event) &&
                ev.base.type == DRM_EVENT_FLIP_COMPLETE)
                done = true;
        }
    }
    if (!done) {
        d->flip_ok = false;
        d->buf = (uint32_t *)d->map[d->scan];
        fprintf(stderr, "warning: page flip event timed out, painting in place\n");
        return;
    }

    d->scan = d->paint;
    d->paint ^= 1;                  /* old scanout is now free to draw */
    d->buf = (uint32_t *)d->map[d->paint];
}

/* ------------------------------------------------------------------ */
/* Canvas primitives (32-bit packed RGB, buffers are XRGB8888)         */
/* ------------------------------------------------------------------ */

void px(Canvas *c, int x, int y, uint32_t col)
{
    if (x < 0 || y < 0 || x >= c->d->w || y >= c->d->h) return;
    c->d->buf[(size_t)y * c->d->pitch + x] = col;
}

void clear(Canvas *c)
{
    memset(c->d->buf, 0, c->d->size);
}

void fill_rect(Canvas *c, int x, int y, int w, int h, uint32_t col)
{
    for (int yy = y; yy < y + h; yy++)
        for (int xx = x; xx < x + w; xx++)
            px(c, xx, yy, col);
}

void rect_outline(Canvas *c, int x, int y, int w, int h, int t, uint32_t col)
{
    fill_rect(c, x, y, w, t, col);
    fill_rect(c, x, y + h - t, w, t, col);
    fill_rect(c, x, y, t, h, col);
    fill_rect(c, x + w - t, y, t, h, col);
}

void fill_circle(Canvas *c, int cx, int cy, int r, uint32_t col)
{
    int x0 = cx - r, x1 = cx + r, y0 = cy - r, y1 = cy + r;
    for (int y = y0; y <= y1; y++)
        for (int x = x0; x <= x1; x++) {
            int dx = x - cx, dy = y - cy;
            if (dx * dx + dy * dy <= r * r) px(c, x, y, col);
        }
}

/* ring of thickness t, hugging the inside of radius r */
void ring_circle(Canvas *c, int cx, int cy, int r, int t, uint32_t col)
{
    int r2 = r * r, ri = (r - t) * (r - t);
    for (int y = cy - r; y <= cy + r; y++)
        for (int x = cx - r; x <= cx + r; x++) {
            int dx = x - cx, dy = y - cy, d2 = dx * dx + dy * dy;
            if (d2 >= ri && d2 <= r2) px(c, x, y, col);
        }
}

void draw_line(Canvas *c, int x0, int y0, int x1, int y1, int t, uint32_t col)
{
    int dx = abs(x1 - x0), dy = -abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, err = dx + dy;
    for (;;) {
        fill_rect(c, x0 - t / 2, y0 - t / 2, t, t, col);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

static bool in_triangle(int px_, int py_,
                        int x0, int y0, int x1, int y1, int x2, int y2)
{
    int s1 = (x1 - x0) * (py_ - y0) - (px_ - x0) * (y1 - y0);
    int s2 = (x2 - x1) * (py_ - y1) - (px_ - x1) * (y2 - y1);
    int s3 = (x0 - x2) * (py_ - y2) - (px_ - x2) * (y0 - y2);
    return (s1 >= 0 && s2 >= 0 && s3 >= 0) || (s1 <= 0 && s2 <= 0 && s3 <= 0);
}

void fill_triangle(Canvas *c, int x0, int y0, int x1, int y1, int x2, int y2, uint32_t col)
{
    int minx = x0, maxx = x0, miny = y0, maxy = y0;
    int xs[3] = { x0, x1, x2 }, ys[3] = { y0, y1, y2 };
    for (int i = 1; i < 3; i++) {
        if (xs[i] < minx) minx = xs[i];
        if (xs[i] > maxx) maxx = xs[i];
        if (ys[i] < miny) miny = ys[i];
        if (ys[i] > maxy) maxy = ys[i];
    }
    for (int y = miny; y <= maxy; y++)
        for (int x = minx; x <= maxx; x++)
            if (in_triangle(x, y, x0, y0, x1, y1, x2, y2))
                px(c, x, y, col);
}

/* ------------------------------------------------------------------ */
/* 5x7 bitmap font (41 glyphs: A-Z 0-9 ':' '-' '/' '+' and space)      */
/* ------------------------------------------------------------------ */

static const char F5x7[][7] = {
/*A*/" ### ","#   #","#   #","#####","#   #","#   #","#   #",
/*B*/"#### ","#   #","#   #","#### ","#   #","#   #","#### ",
/*C*/" ####","#    ","#    ","#    ","#    ","#    "," ####",
/*D*/"#### ","#   #","#   #","#   #","#   #","#   #","#### ",
/*E*/"#####","#    ","#    ","#### ","#    ","#    ","#####",
/*F*/"#####","#    ","#    ","#### ","#    ","#    ","#    ",
/*G*/" ####","#    ","#    ","#  ##","#   #","#   #"," ####",
/*H*/"#   #","#   #","#   #","#####","#   #","#   #","#   #",
/*I*/"#####","  #  ","  #  ","  #  ","  #  ","  #  ","#####",
/*J*/"  ###","   # ","   # ","   # ","   # ","#  # "," ##  ",
/*K*/"#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #",
/*L*/"#    ","#    ","#    ","#    ","#    ","#    ","#####",
/*M*/"#   #","## ##","# # #","#   #","#   #","#   #","#   #",
/*N*/"#   #","##  #","# # #","#  ##","#   #","#   #","#   #",
/*O*/" ### ","#   #","#   #","#   #","#   #","#   #"," ### ",
/*P*/"#### ","#   #","#   #","#### ","#    ","#    ","#    ",
/*Q*/" ### ","#   #","#   #","#   #","# # #","#  # "," ## #",
/*R*/"#### ","#   #","#   #","#### ","# #  ","#  # ","#   #",
/*S*/" ####","#    ","#    "," ### ","    #","    #","#### ",
/*T*/"#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  ",
/*U*/"#   #","#   #","#   #","#   #","#   #","#   #"," ### ",
/*V*/"#   #","#   #","#   #","#   #","#   #"," # # ","  #  ",
/*W*/"#   #","#   #","#   #","# # #","# # #","## ##","#   #",
/*X*/"#   #","#   #"," # # ","  #  "," # # ","#   #","#   #",
/*Y*/"#   #","#   #"," # # ","  #  ","  #  ","  #  ","  #  ",
/*Z*/"#####","    #","   # ","  #  "," #   ","#    ","#####",
/*0*/" ### ","#   #","#  ##","# # #","##  #","#   #"," ### ",
/*1*/"  #  "," ##  ","  #  ","  #  ","  #  ","  #  ","#####",
/*2*/" ### ","#   #","    #","   # ","  #  "," #   ","#####",
/*3*/"#####","   # ","  #  ","   # ","    #","#   #"," ### ",
/*4*/"   # ","  ## "," # # ","#  # ","#####","   # ","   # ",
/*5*/"#####","#    ","#### ","    #","    #","#   #"," ### ",
/*6*/" ### ","#    ","#    ","#### ","#   #","#   #"," ### ",
/*7*/"#####","    #","   # ","  #  "," #   "," #   "," #   ",
/*8*/" ### ","#   #","#   #"," ### ","#   #","#   #"," ### ",
/*9*/" ### ","#   #","#   #"," ####","    #","    #"," ### ",
/*:*/"     ","  #  ","  #  ","     ","  #  ","  #  ","     ",
/*-*/"     ","     ","     ","#####","     ","     ","     ",
/*/*/ "    #","   # ","  #  "," #   ","#    ","     ","     ",
/* */"     ","     ","     ","     ","     ","     ","     ",
/*+*/"     ","  #  ","  #  ","#####","  #  ","  #  ","     ",
};

static int glyph_index(char ch)
{
    if (ch >= 'A' && ch <= 'Z') return ch - 'A';
    if (ch >= '0' && ch <= '9') return 26 + (ch - '0');
    if (ch == ':') return 36;
    if (ch == '-') return 37;
    if (ch == '/') return 38;
    if (ch == '+') return 40;
    return 39;                  /* space */
}

int draw_text(Canvas *c, int x, int y, const char *s, int scale, uint32_t col)
{
    for (const char *p = s; *p; p++) {
        int gi = glyph_index(*p);
        for (int r = 0; r < 7; r++)
            for (int cc = 0; cc < 5; cc++)
                if (F5x7[gi * 7 + r][cc] == '#')
                    for (int dy = 0; dy < scale; dy++)
                        for (int dx = 0; dx < scale; dx++)
                            px(c, x + cc * scale + dx, y + r * scale + dy, col);
        x += 6 * scale;
    }
    return x;
}

/* -------------------------------- palette ------------------------------- */
/* Same generic grays/status colors as the troubleshooter; flasher-specific
   colors get added as screens are designed. */

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

/* ------------------------------------------------------------------ */
/* Bootloader / app I2C protocol                                       */
/* ------------------------------------------------------------------ */

#define BL_ADDR                 0x29    /* bootloader slave address    */
#define APP_ADDR                0x10    /* application slave address   */
#define I2C_BUS                 "/dev/i2c-1"   /* bit-banged by the image */

/* Bootloader commands (must match atmega/bootloader/bootloader.c) */
#define CMD_READ_INFO           0x01
#define CMD_WRITE_PAGE          0x03  /* page number byte precedes the 64 data bytes */
#define CMD_FINALIZE            0x05
#define CMD_READ_PINS           0x07

/* ATmega8 factory signature bytes (datasheet section 24.8) */
#define EXPECTED_SIG_0          0x1E
#define EXPECTED_SIG_1          0x93
#define EXPECTED_SIG_2          0x07

#define SPM_PAGESIZE            64
#define FLASH_SIZE              8192
#define BOOTLOADER_START        0x1C00
#define FW_VERSION_ADDR         0x1BFC   /* version byte, last byte before cksum */
#define NUM_PAGES               (FLASH_SIZE / SPM_PAGESIZE)   /* 128 */
#define APP_PAGES               (BOOTLOADER_START / SPM_PAGESIZE) /* 112 */

/* ATmega8 max flash write time is 4.5ms. Sleep 10x that for safety. */
#define FLASH_WRITE_SLEEP_US    45000

/* Verification status codes, must match bootloader.
   0x00 only appears transiently: while pages are being written the
   bootloader zeroes the status byte (and the fingerprint) until finalize. */
#define VERIFY_PENDING          0x00
#define VERIFY_FAILED           0x55
#define VERIFY_PASSED           0xAA

/* How many times to retry a corrupt CMD_READ_INFO response */
#define INFO_READ_RETRIES       10

/* How many times to retry a single page write before giving up */
#define PAGE_WRITE_RETRIES      3

/* CMD_READ_INFO response: 10 info bytes + 3-byte Fletcher+XOR trailer.
   Byte layout:
     [0..2]  ATmega signature (1E 93 07)
     [3]     bootloader version
     [4]     app flash region size in pages (BOOTLOADER_START / 64 = 112)
     [5]     verify status (PASSED / FAILED; 0x00 while flashing)
     [6..8]  fingerprint: Fletcher+XOR over installed app flash bytes
             0x0000..0x1BFC -- compared against the same computation over
             the bundled firmware.hex to detect "same/different version"
     [9]     app firmware version byte (read from app flash at 0x1BFC)
     [10..12] Fletcher+XOR checksum over bytes 0..9 */
#define BL_INFO_LEN             13
#define BL_INFO_TRAILER         10    /* checksum covers first 10 bytes */

typedef struct {
    uint8_t  sig[3];
    uint8_t  version;        /* bootloader version */
    uint8_t  app_pages;
    uint8_t  verify_status;
    uint8_t  fingerprint[3];
    uint8_t  fw_version;     /* app firmware version byte */
} bl_info_t;

/* Raw port registers returned by CMD_READ_PINS. Buttons are active-low
   (pressed = 0). Bits worth watching (from atmega/firmware/config.h):
     PINB.0 = BTN_DISP      PINB.1 = BTN_EXTRA2
     PIND.1 = RPI_DETECT    PIND.2 = BTN_EXTRA1
     PIND.4 = BTN_SHUTDOWN (power key)
     PIND.5 = BTN_HLD      PIND.6 = SWITCH_WIFI
   PINB.2/.3/.6/.7 are outputs (LCD/LED/5V) and read back their driven
   level -- callers must mask them off. */
typedef struct {
    uint8_t pinb;
    uint8_t pind;
} bl_pins_t;

static int i2c_fd = -1;

static int i2c_open(void)
{
    i2c_fd = open(I2C_BUS, O_RDWR);
    if (i2c_fd < 0) {
        fprintf(stderr, "Failed to open I2C device %s: %s\n",
                I2C_BUS, strerror(errno));
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

    if (ioctl(i2c_fd, I2C_RDWR, &data) < 0)
        return -1;
    return 0;
}

static int i2c_write(uint8_t addr, const uint8_t *buf, size_t len)
{
    struct i2c_msg msg = {
        .addr = addr, .flags = 0, .len = (__u16)len, .buf = (uint8_t *)buf,
    };
    struct i2c_rdwr_ioctl_data data = { .msgs = &msg, .nmsgs = 1 };

    if (ioctl(i2c_fd, I2C_RDWR, &data) < 0)
        return -1;
    return 0;
}

static int i2c_probe(uint8_t addr)
{
    /* Plain 1-byte read with I2C_SLAVE rather than a zero-length write via
       I2C_RDWR: the hardware i2c_bcm2835 driver rejects zero-length
       messages, and this works on both it and the bit-banged i2c-gpio bus. */
    uint8_t dummy;
    if (ioctl(i2c_fd, I2C_SLAVE, addr) < 0)
        return -1;
    return read(i2c_fd, &dummy, 1) == 1 ? 0 : -1;
}

/* --- Bootloader checksums (must match bootloader.c exactly) --- */

/* Fletcher+XOR over a byte range: uint8_t accumulators, natural overflow. */
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

/*
 * Reads the 12-byte CMD_READ_INFO response and validates the trailing
 * 3-byte Fletcher+XOR checksum over the first 9 info bytes. Retries on a
 * corrupt read to mitigate I2C unreliability.
 */
static int bl_read_info(bl_info_t *info)
{
    uint8_t cmd = CMD_READ_INFO;
    uint8_t buf[BL_INFO_LEN];
    uint8_t f_a, f_b, xor;
    int     attempt;

    for (attempt = 0; attempt < INFO_READ_RETRIES; attempt++) {
        if (attempt > 0)
            usleep(10000);

        if (i2c_write_then_read(BL_ADDR, &cmd, 1, buf, BL_INFO_LEN) < 0)
            continue;

        /* Validate checksum over bytes 0-8 */
        compute_fletcher_xor(buf, BL_INFO_TRAILER, &f_a, &f_b, &xor);
        if (f_a != buf[BL_INFO_LEN - 3] || f_b != buf[BL_INFO_LEN - 2] ||
            xor != buf[BL_INFO_LEN - 1]) {
            fprintf(stderr, "  CMD_READ_INFO checksum mismatch (attempt %d/%d), retrying...\n",
                    attempt + 1, INFO_READ_RETRIES);
            continue;
        }

        info->sig[0]         = buf[0];
        info->sig[1]         = buf[1];
        info->sig[2]         = buf[2];
        info->version        = buf[3];
        info->app_pages      = buf[4];
        info->verify_status  = buf[5];
        info->fingerprint[0] = buf[6];
        info->fingerprint[1] = buf[7];
        info->fingerprint[2] = buf[8];
        info->fw_version     = buf[9];
        usleep(10000); /* allow bus to settle after read */
        return 0;
    }

    fprintf(stderr, "Failed to read valid info after %d attempts.\n", INFO_READ_RETRIES);
    return -1;
}

/*
 * Reads the 2-byte CMD_READ_PINS response: raw PINB then PIND.
 * Retries once on a short read (the response is 2 bytes, NACK after).
 */
static int bl_read_pins(bl_pins_t *pins)
{
    uint8_t cmd = CMD_READ_PINS;
    uint8_t buf[2];

    if (i2c_write_then_read(BL_ADDR, &cmd, 1, buf, 2) < 0)
        return -1;
    pins->pinb = buf[0];
    pins->pind = buf[1];
    return 0;
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
 * Sends CMD_FINALIZE, prompting the bootloader to verify the checksum
 * already embedded in the final 3 bytes of the app flash region.
 */
static int bl_finalize(void)
{
    uint8_t cmd = CMD_FINALIZE;
    if (i2c_write(BL_ADDR, &cmd, 1) < 0)
        return -1;
    usleep(100000); /* 10x time for compute_flash_checksum to complete */
    return 0;
}

/* ------------------------------------------------------------------ */
/* Application packet protocol (0x10 -- gamepad-style packets)          */
/* ------------------------------------------------------------------ */

/* While the app firmware runs, it exposes the same 11-byte packet the
   gamepad driver reads: CRC-16-CCITT over the first 9 bytes, stored
   high/low in bytes 9/10. We only care about the power-key status bit
   (byte 4, bit 4) for the poweroff shortcut; buttons sit in bytes 0/1. */
#define APP_DATASIZE            11
#define APP_CRC_LEN             9
#define STATUS_PWR              0x10
#define CMD_VERSION             0x25   /* must match firmware config.h */

static uint16_t crc16_table[256];
static void init_crc16_table(void)
{
    for (int i = 0; i < 256; i++) {
        uint16_t crc = (uint16_t)(i << 8);
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000) ? (crc << 1) ^ 0x1021 : (crc << 1);
        crc16_table[i] = crc;
    }
}

static uint16_t crc16_ccitt(const uint8_t *data, uint8_t len)
{
    uint16_t crc = 0xFFFF;
    for (uint8_t i = 0; i < len; i++)
        crc = (crc << 8) ^ crc16_table[((crc >> 8) ^ data[i]) & 0xFF];
    return crc;
}

/* Reads one 11-byte app packet; returns true if CRC valid. */
static bool app_read_packet(uint8_t *pkt)
{
    if (ioctl(i2c_fd, I2C_SLAVE, APP_ADDR) < 0)
        return false;
    if (read(i2c_fd, pkt, APP_DATASIZE) != APP_DATASIZE)
        return false;
    uint16_t crc = crc16_ccitt(pkt, APP_CRC_LEN);
    return (uint8_t)(crc >> 8) == pkt[9] && (uint8_t)crc == pkt[10];
}

/* Asks the app for its firmware version (CMD_VERSION): after this command,
   the app's next read returns a single version byte instead of a packet.
   The app only processes commands in 4-byte frames, so pad the command. */
static int app_read_version(uint8_t *ver)
{
    uint8_t cmd[4] = { CMD_VERSION, 0, 0, 0 };
    if (i2c_write(APP_ADDR, cmd, 4) < 0)
        return -1;
    usleep(10000);  /* app processes commands in its ~1ms main loop */
    if (ioctl(i2c_fd, I2C_SLAVE, APP_ADDR) < 0)
        return -1;
    return read(i2c_fd, ver, 1) == 1 ? 0 : -1;
}

/* ------------------------------------------------------------------ */
/* Firmware image (Intel HEX)                                          */
/* ------------------------------------------------------------------ */

typedef struct {
    uint8_t  data[FLASH_SIZE];
    uint8_t  page_has_data[NUM_PAGES];
    uint16_t num_pages;
    uint8_t  version;          /* firmware version byte (at FW_VERSION_ADDR) */
    uint8_t  fingerprint[3];   /* Fletcher+XOR over bytes 0x0000..0x1BFC,
                                   same range the bootloader computes */
} flash_image_t;

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

    /* Fingerprint over the same byte range the bootloader's
       compute_flash_checksum() covers: app flash minus the trailing
       3 checksum bytes. For a Makefile-built firmware.hex this equals the
       embedded checksum stored at 0x1BFD-0x1BFF. */
    compute_fletcher_xor(image->data, BOOTLOADER_START - 3,
                         &image->fingerprint[0], &image->fingerprint[1],
                         &image->fingerprint[2]);
    image->version = image->data[FW_VERSION_ADDR];

    ret = 0;

    fail:
    fclose(f);
    return ret;
}

/* ------------------------------------------------------------------ */
/* UI state                                                            */
/* ------------------------------------------------------------------ */

typedef enum {
    MODE_NONE = 0,      /* nothing responding on the bus            */
    MODE_APP,           /* app firmware running (0x10 packets)      */
    MODE_BOOTLOADER,    /* bootloader holding at 0x29               */
} ui_mode_t;

typedef struct {
    ui_mode_t mode;
    bool      dirty;                 /* redraw screen next tick  */
    bl_info_t info;                  /* valid when bootloader    */
    bool      bl_found;              /* seen bootloader since last NONE */
    double    next_poll;             /* monotonic time for next probe */
    uint8_t   app_version;           /* app fw version when in MODE_APP */
} ui_state_t;

/* monotonic seconds since some fixed point (CLOCK_MONOTONIC) */
static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

/* --- drawing helpers ------------------------------------------------ */

/* Draws a "tag": filled box with outline and scale-2 text centered in it. */
static void draw_tag_rect(Canvas *c, int x, int y, int w, int h,
                          const char *text, uint32_t fill, uint32_t text_col)
{
    fill_rect(c, x, y, w, h, fill);
    int tw = (int)strlen(text) * 12 - 2;          /* scale-2 text width */
    draw_text(c, x + (w - tw) / 2, y + (h - 14) / 2, text, 2, text_col);
}

/* One row of a panel: label on the left, colored value on the right. */
typedef struct {
    const char *label;
    const char *value;
    uint32_t    col;
} panel_row_t;

/* Draws a titled panel: outlined box, title tag straddling the top edge,
   and rows spread evenly through the remaining space. Values are
   right-aligned so they line up across panels. */
static void draw_panel(Canvas *c, int x, int y, int w, int h,
                       const char *title, const panel_row_t *rows, int nrows)
{
    rect_outline(c, x, y, w, h, 2, C_EDGE);
    int tag_w = (int)strlen(title) * 12 - 2 + 16;
    draw_tag_rect(c, x + 12, y - 14, tag_w, 28, title, C_UNPRESSED, C_VAL);

    int top = y + 24;
    int bot = y + h - 14;
    for (int i = 0; i < nrows; i++) {
        int cy = top + (bot - top) * (i + 1) / (nrows + 1) - 7;
        draw_text(c, x + 16, cy, rows[i].label, 2, C_LABEL);
        int vw = (int)strlen(rows[i].value) * 12 - 2;
        draw_text(c, x + w - 16 - vw, cy, rows[i].value, 2, rows[i].col);
    }
}

/* True if the app flash region is entirely erased (never flashed). */
static bool is_empty_flash(const uint8_t fp[3])
{
    static bool init = false;
    static uint8_t empty_fp[3];
    if (!init) {
        uint8_t *blank = malloc(BOOTLOADER_START - 3);
        memset(blank, 0xFF, BOOTLOADER_START - 3);
        compute_fletcher_xor(blank, BOOTLOADER_START - 3,
                             &empty_fp[0], &empty_fp[1], &empty_fp[2]);
        free(blank);
        init = true;
    }
    return memcmp(fp, empty_fp, 3) == 0;
}

/* ------------------------------------------------------------------ */
/* Status screen                                                       */
/* ------------------------------------------------------------------ */

/* Renders the whole screen for the current ui_state. Rebuilds everything
   from scratch -- called only on state changes (dirty flag). */
static void draw_status_screen(Canvas *c, const ui_state_t *st,
                               const flash_image_t *image, float pwr_frac,
                               float disp_frac)
{
    int w = c->d->w;
    clear(c);

    /* title */
    const char *title = "PSPI FIRMWARE";
    int tw = (int)strlen(title) * 18 - 3;
    draw_text(c, (w - tw) / 2, 14, title, 3, C_WHITE);

    /* mode banner */
    const char *banner = "NO RESPONSE";
    uint32_t bcol = C_RED;
    if (st->mode == MODE_BOOTLOADER) {
        banner = "BOOTLOADER MODE"; bcol = C_GREEN;
    } else if (st->mode == MODE_APP) {
        banner = "FIRMWARE RUNNING"; bcol = C_AMBER;
    }
    fill_rect(c, (w - 600) / 2, 60, 600, 64, C_DZ);
    tw = (int)strlen(banner) * 18 - 3;   /* scale-3 text width */
    draw_text(c, (w - tw) / 2, 60 + (64 - 21) / 2, banner, 3, bcol);

    if (st->mode == MODE_BOOTLOADER) {
        char bufs[4][32];
        panel_row_t inst[3], cand[3];

        /* left panel: what is on the board right now. The bootloader's
           verify byte is only ever PASSED or FAILED (it is written when
           verification runs); an all-0xFF app region reads as EMPTY. */
        const char *state;
        uint32_t state_col;
        if (st->info.verify_status == VERIFY_PASSED) {
            state = "OK";      state_col = C_GREEN;
        } else if (is_empty_flash(st->info.fingerprint)) {
            state = "EMPTY";   state_col = C_WHITE;
        } else {
            state = "CORRUPT"; state_col = C_RED;
        }
        snprintf(bufs[0], sizeof bufs[0], "V%d", st->info.version);
        snprintf(bufs[1], sizeof bufs[1], "V%d", st->info.fw_version);
        inst[0] = (panel_row_t){ "BOOTLOADER", bufs[0], C_VAL };
        inst[1] = (panel_row_t){ "FIRMWARE",   bufs[1], C_VAL };
        inst[2] = (panel_row_t){ "STATE",      state,   state_col };
        draw_panel(c, 20, 150, 360, 180, "INSTALLED", inst, 3);

        /* right panel: the firmware image loaded from the card, compared
           against what is installed. */
        bool same_ver = image->version == st->info.fw_version;
        bool same_ck  = memcmp(image->fingerprint, st->info.fingerprint, 3) == 0;
        snprintf(bufs[2], sizeof bufs[2], "V%d", image->version);
        cand[0] = (panel_row_t){ "VERSION",         bufs[2], C_VAL };
        cand[1] = (panel_row_t){ "VERSION MATCH",
                    same_ver ? "SAME" : "DIFFERENT",
                    same_ver ? C_GREEN : C_AMBER };
        cand[2] = (panel_row_t){ "CHECKSUM MATCH",
                    same_ck ? "SAME" : "DIFFERENT",
                    same_ck ? C_GREEN : C_AMBER };
        draw_panel(c, 420, 150, 360, 180, "CANDIDATE", cand, 3);

        /* flash trigger tag: fills amber as DISP is held */
        const char *act = "HOLD DISPLAY TO FLASH FIRMWARE";
        int fw_ = (int)strlen(act) * 12 - 2 + 24;   /* text + padding */
        int fx = (w - fw_) / 2;
        fill_rect(c, fx, 376, fw_, 36, C_UNPRESSED);
        if (disp_frac > 0)
            fill_rect(c, fx, 376, (int)(fw_ * disp_frac), 36, C_AMBER);
        int ftw = (int)strlen(act) * 12 - 2;
        draw_text(c, fx + (fw_ - ftw) / 2, 376 + (36 - 14) / 2,
                  act, 2, disp_frac > 0 ? C_FRAME : C_WHITE);
    } else {
        char vbuf[24];
        if (st->mode == MODE_APP && st->app_version) {
            snprintf(vbuf, sizeof vbuf, "APP V%d", st->app_version);
            draw_tag_rect(c, (w - 240) / 2, 150, 240, 32, vbuf,
                          C_UNPRESSED, C_VAL);
        }
        /* instructions for app / no-response modes: numbered steps, one
           per line, so the sequence reads clearly */
        const char *steps[3] = {
            "STEP 1: POWER OFF",
            "STEP 2: HOLD DISPLAY BUTTON",
            "STEP 3: POWER ON",
        };
        const char *head = "TO UPDATE FIRMWARE:";
        tw = (int)strlen(head) * 12 - 2;
        draw_text(c, (w - tw) / 2, 240, head, 2, C_LABEL);
        for (int i = 0; i < 3; i++) {
            tw = (int)strlen(steps[i]) * 12 - 2;
            draw_text(c, (w - tw) / 2, 290 + i * 40, steps[i], 2, C_VAL);
        }
    }

    /* power-key hint: fills red as the power button is held, like the
       flash-action tag above fills amber */
    const char *pwr = "HOLD POWER BUTTON TO SHUT DOWN";
    int pw = (int)strlen(pwr) * 12 - 2 + 24;   /* text + padding */
    int px = (w - pw) / 2;
    fill_rect(c, px, 422, pw, 36, C_UNPRESSED);
    if (pwr_frac > 0)
        fill_rect(c, px, 422, (int)(pw * pwr_frac), 36, C_RED);
    int ptw = (int)strlen(pwr) * 12 - 2;
    draw_text(c, px + (pw - ptw) / 2, 422 + (36 - 14) / 2,
              pwr, 2, pwr_frac > 0 ? C_FRAME : C_WHITE);

    present(c->d);
}

/* ------------------------------------------------------------------ */
/* Flash flow                                                          */
/* ------------------------------------------------------------------ */

/* Writes the bundled image to app flash, verifies via the bootloader, and
   shows a full-screen result. Returns when done; caller redraws status. */
static void run_flash_flow(Canvas *c, const flash_image_t *image)
{
    int w = c->d->w;
    int bx = (w - 600) / 2;
    const char *head = "FLASHING FIRMWARE";
    int tw = (int)strlen(head) * 18 - 3;
    int head_x = (w - tw) / 2;

    /* write all app pages that carry data (bar spans all 112 regardless) */
    for (int page = 0; page < APP_PAGES; page++) {
        if (!image->page_has_data[page]) continue;
        if (bl_write_page((uint8_t)page, &image->data[page * SPM_PAGESIZE]) < 0) {
            fprintf(stderr, "page %d write failed: %s\n", page, strerror(errno));
            const char *err = "I2C ERROR - RETRY";
            clear(c);
            tw = (int)strlen(err) * 18 - 3;
            draw_text(c, (w - tw) / 2, 230, err, 3, C_RED);
            present(c->d);
            return;
        }
        /* Redraw the whole progress frame before every present. Incremental
           drawing leaves stale content (e.g. the status screen) in the
           other buffer, which flickers on screen during the page writes. */
        clear(c);
        draw_text(c, head_x, 150, head, 3, C_WHITE);
        rect_outline(c, bx, 220, 600, 40, 2, C_EDGE);
        fill_rect(c, bx + 2, 222, (int)(596 * (page + 1) / (float)APP_PAGES), 36,
                  C_AMBER);
        char lbl[24];
        snprintf(lbl, sizeof lbl, "PAGE %d / %d", page + 1, APP_PAGES);
        tw = (int)strlen(lbl) * 12 - 2;
        draw_text(c, (w - tw) / 2, 290, lbl, 2, C_LABEL);
        present(c->d);
    }

    /* finalize: bootloader computes the flash checksum and updates status */
    bl_finalize();

    /* poll verify status until it leaves PENDING (bootloader zeroes it
       during writes) or time out */
    bl_info_t info;
    bool valid = false;
    for (int i = 0; i < 200; i++) {
        if (bl_read_info(&info) == 0) {
            valid = true;
            if (info.verify_status == VERIFY_PASSED ||
                info.verify_status == VERIFY_FAILED)
                break;
        }
        usleep(10000);
    }

    /* result screen */
    clear(c);
    const char *r1, *r2;
    uint32_t col;
    if (!valid) {
        r1 = "VERIFY TIMEOUT";   r2 = "POWER CYCLE AND RETRY"; col = C_AMBER;
    } else if (info.verify_status == VERIFY_PASSED) {
        r1 = "FLASH SUCCESSFUL"; r2 = "POWER CYCLE WHEN READY";  col = C_GREEN;
    } else {
        r1 = "VERIFICATION FAILED"; r2 = "HOLD DISPLAY TO RETRY"; col = C_RED;
    }
    tw = (int)strlen(r1) * 18 - 3;
    draw_text(c, (w - tw) / 2, 190, r1, 3, col);
    tw = (int)strlen(r2) * 12 - 2;
    draw_text(c, (w - tw) / 2, 260, r2, 2, C_VAL);
    present(c->d);

    /* hold the result on screen until the user leaves bootloader mode */
    sleep(3);
}

/* ------------------------------------------------------------------ */
/* main                                                                */
/* ------------------------------------------------------------------ */

static void usage(const char *prog)
{
    printf("Usage: %s [seconds]            display smoke test (temporary)\n"
           "       %s --hex <firmware.hex> parse hex file, print fingerprint\n"
           "       %s --probe             probe I2C, dump bootloader info/pins\n"
           "       %s --flash <firmware.hex> headless flash + verify\n",
           prog, prog, prog, prog);
}

static int run_hex_mode(const char *path)
{
    flash_image_t image;
    if (parse_hex_file(path, &image) < 0)
        return 1;

    printf("hex: %s\n", path);
    printf("  pages with data:  %u\n", image.num_pages);

    /* data coverage: first/last address carrying non-0xFF data */
    int first = -1, last = -1;
    for (int i = 0; i < FLASH_SIZE; i++)
        if (image.data[i] != 0xFF) {
            if (first < 0) first = i;
            last = i;
        }
    if (first >= 0)
        printf("  data range:       0x%04X - 0x%04X\n", first, last);

    printf("  fingerprint:      %02X %02X %02X (computed over 0x0000-0x%04X)\n",
           image.fingerprint[0], image.fingerprint[1], image.fingerprint[2],
           BOOTLOADER_START - 4);

    /* cross-check: for Makefile-built hex files the last 3 app-flash bytes
       ARE the embedded checksum over the same range -- they must match. */
    uint8_t *emb = &image.data[BOOTLOADER_START - 3];
    bool emb_all_ff = emb[0] == 0xFF && emb[1] == 0xFF && emb[2] == 0xFF;
    bool match = !emb_all_ff &&
                 emb[0] == image.fingerprint[0] &&
                 emb[1] == image.fingerprint[1] &&
                 emb[2] == image.fingerprint[2];
    if (emb_all_ff)
        printf("  embedded cksum:   none (0x1BFD-0x1BFF empty)\n");
    else
        printf("  embedded cksum:   %02X %02X %02X -> %s computed fingerprint\n",
               emb[0], emb[1], emb[2], match ? "MATCHES" : "DOES NOT MATCH");
    return match || emb_all_ff ? 0 : 1;
}

/* Headless flash: same pipeline as the UI flash flow, stdout progress. */
static int run_flash_mode(const char *path)
{
    flash_image_t image;
    if (parse_hex_file(path, &image) < 0)
        return 1;
    if (i2c_open() < 0)
        return 1;
    if (i2c_probe(BL_ADDR) != 0) {
        fprintf(stderr, "bootloader not responding at 0x%02X\n", BL_ADDR);
        return 1;
    }

    bl_info_t info;
    if (bl_read_info(&info) == 0)
        printf("before: fingerprint %02X %02X %02X, verify 0x%02X\n",
               info.fingerprint[0], info.fingerprint[1], info.fingerprint[2],
               info.verify_status);

    printf("flashing %u pages...\n", APP_PAGES);
    for (int page = 0; page < APP_PAGES; page++) {
        if (!image.page_has_data[page])
            continue;
        if (bl_write_page((uint8_t)page, &image.data[page * SPM_PAGESIZE]) < 0) {
            fprintf(stderr, "page %d write failed: %s\n", page, strerror(errno));
            return 1;
        }
        if ((page + 1) % 16 == 0)
            printf("  page %d / %d\n", page + 1, APP_PAGES);
    }

    bl_finalize();
    bool valid = false;
    for (int i = 0; i < 200; i++) {
        if (bl_read_info(&info) == 0) {
            valid = true;
            if (info.verify_status == VERIFY_PASSED ||
                info.verify_status == VERIFY_FAILED)
                break;
        }
        usleep(10000);
    }
    if (!valid) {
        printf("after: verify timed out\n");
        return 1;
    }
    printf("after: fingerprint %02X %02X %02X, verify 0x%02X (%s)\n",
           info.fingerprint[0], info.fingerprint[1], info.fingerprint[2],
           info.verify_status,
           info.verify_status == VERIFY_PASSED ? "PASSED" : "FAILED");
    printf("expected fingerprint %02X %02X %02X -> %s\n",
           image.fingerprint[0], image.fingerprint[1], image.fingerprint[2],
           memcmp(info.fingerprint, image.fingerprint, 3) == 0 ?
           "MATCH" : "MISMATCH");
    return info.verify_status == VERIFY_PASSED ? 0 : 1;
}

static int run_probe_mode(void)
{
    if (i2c_open() < 0)
        return 1;

    bool bl_present = i2c_probe(BL_ADDR) == 0;
    bool app_present = i2c_probe(APP_ADDR) == 0;
    printf("probe %s: bootloader(0x%02X)=%s app(0x%02X)=%s\n",
           I2C_BUS, BL_ADDR, bl_present ? "yes" : "no", APP_ADDR, app_present ? "yes" : "no");

    if (!bl_present) {
        printf("bootloader not responding -- can't read info/pins\n");
        printf("to enter bootloader mode: power off, hold the display button, power on\n");
        return 1;
    }

    bl_info_t info;
    if (bl_read_info(&info) < 0)
        return 1;
    printf("  signature:        %02X %02X %02X\n", info.sig[0], info.sig[1], info.sig[2]);
    printf("  bootloader ver:   0x%02X\n", info.version);
    printf("  app pages:        %u\n", info.app_pages);
    printf("  verify status:    0x%02X (%s)\n", info.verify_status,
           info.verify_status == VERIFY_PASSED ? "PASSED" :
           info.verify_status == VERIFY_FAILED ? "FAILED" : "PENDING");
    printf("  fingerprint:      %02X %02X %02X\n",
           info.fingerprint[0], info.fingerprint[1], info.fingerprint[2]);

    bl_pins_t pins;
    if (bl_read_pins(&pins) == 0)
        printf("  pins:             PINB=%02X PIND=%02X "
               "[DISP=%d X2=%d X1=%d PWR=%d HLD=%d WIFI_SW=%d]\n",
               pins.pinb, pins.pind,
               !(pins.pinb & 0x01), !(pins.pinb & 0x02),
               !(pins.pind & 0x04), !(pins.pind & 0x10),
               !(pins.pind & 0x20), !(pins.pind & 0x40));

    if (app_present)
        printf("NOTE: app is also responding at 0x10 (unexpected while bootloader holds)\n");
    return 0;
}

int main(int argc, char **argv)
{
    const char *hex_path = NULL, *flash_path = NULL;
    bool do_probe = false, do_smoke = false;
    int  run_secs = 5;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "--probe") == 0) {
            do_probe = true;
        } else if (strcmp(argv[i], "--hex") == 0) {
            if (i + 1 >= argc) { usage(argv[0]); return 2; }
            hex_path = argv[++i];
        } else if (strcmp(argv[i], "--flash") == 0) {
        if (i + 1 >= argc) { usage(argv[0]); return 2; }
        flash_path = argv[++i];
    } else if (strcmp(argv[i], "--smoke") == 0) {
        do_smoke = true;
    } else {
            run_secs = atoi(argv[i]);
        }
    }

    if (hex_path)
        return run_hex_mode(hex_path);
    if (flash_path)
        return run_flash_mode(flash_path);
    if (do_probe)
        return run_probe_mode();

    if (do_smoke) {
    /* ---- temporary smoke test: test card on whatever display is connected
       (PSPi LCD on the target image, HDMI on this dev Pi) ---- */
    Display disp;
    const char *cname = NULL;
    if (!display_init(&disp, &cname)) return 1;
    Canvas cv = { .d = &disp };

    clear(&cv);
    rect_outline(&cv, 4, 4, cv.d->w - 8, cv.d->h - 8, 2, C_FRAME);

    const char *title = "FIRMWARE UI";
    int tw = (int)strlen(title) * 18 - 3;         /* scale-3 text width */
    draw_text(&cv, (cv.d->w - tw) / 2, 40, title, 3, C_WHITE);

    const char *sub = "DRM SMOKE TEST";
    tw = (int)strlen(sub) * 12 - 2;               /* scale-2 text width */
    draw_text(&cv, (cv.d->w - tw) / 2, 76, sub, 2, C_LABEL);

    /* R/G/B gradient strips via lerp_rgb */
    for (int i = 0; i < 3; i++) {
        uint32_t c0 = i == 0 ? 0xFF0000 : i == 1 ? 0x00FF00 : 0x0000FF;
        uint32_t c1 = i == 0 ? 0x401010 : i == 1 ? 0x104010 : 0x101040;
        int y0 = 160 + i * 40;
        for (int x = 40; x < cv.d->w - 40; x++)
            fill_rect(&cv, x, y0, 1, 24,
                      lerp_rgb(c0, c1, x - 40, cv.d->w - 80));
    }

    present(&disp);
    sleep(run_secs);
    printf("smoke test done (displayed for %d s)\n", run_secs);
    return 0;
    }

    /* ---- status screen: real UI mode ---- */
    flash_image_t image;
    if (parse_hex_file("firmware.hex", &image) < 0) {
        fprintf(stderr, "firmware.hex not found in current directory\n");
        return 1;
    }
    init_crc16_table();

    if (i2c_open() < 0)
        return 1;
    Display disp;
    const char *cname = NULL;
    if (!display_init(&disp, &cname)) return 1;
    Canvas cv = { .d = &disp };

    ui_state_t st = { .mode = MODE_NONE, .dirty = true, .next_poll = 0 };
    double pwr_hold_start = 0;
    float  pwr_frac = 0, pwr_drawn = -1;
    int    bl_fails = 0, app_fails = 0;
    double disp_hold_start = 0;
    float  disp_frac = 0, disp_drawn = -1;
    bool   disp_armed = false;      /* requires one release first */

    for (;;) {
        double t = now_sec();

        switch (st.mode) {
        case MODE_NONE:
            if (t >= st.next_poll) {
                if (i2c_probe(BL_ADDR) == 0) {
                    st.mode = MODE_BOOTLOADER;
                    st.dirty = true;
                } else if (i2c_probe(APP_ADDR) == 0) {
                    uint8_t v = 0;
                    for (int r = 0; r < 5; r++)
                        if (app_read_version(&v) == 0 && v)
                            break;
                    st.app_version = v;
                    st.mode = MODE_APP;
                    st.dirty = true;
                }
                st.next_poll = t + 0.2;
            }
            pwr_frac = 0;
            break;

        case MODE_BOOTLOADER:
            if (t >= st.next_poll) {
                if (bl_read_info(&st.info) == 0) {
                    static bl_info_t last_info;
                    if (memcmp(&st.info, &last_info, sizeof st.info) != 0) {
                        last_info = st.info;
                        st.dirty = true;
                    }
                    bl_fails = 0;
                } else if (++bl_fails >= 5) {
                    st.mode = MODE_NONE;
                    st.dirty = true;
                }

                /* power key = BTN_SHUTDOWN, PIND.4, active-low.
                   display button = BTN_DISP, PINB.0, active-low.
                   DISP is held at power-on to enter the bootloader, so the
                   flash trigger only arms after one clean release. */
                bl_pins_t pins;
                if (bl_read_pins(&pins) == 0) {
                    if (!(pins.pind & 0x10)) {
                        if (!pwr_hold_start) pwr_hold_start = t;
                        pwr_frac = (float)((t - pwr_hold_start) / 0.5);
                        if (pwr_frac >= 1) {
                            system("poweroff");
                            sleep(10);
                            exit(0);
                        }
                    } else {
                        pwr_hold_start = 0;
                        pwr_frac = 0;
                    }

                    if (pins.pinb & 0x01) {
                        /* released */
                        disp_hold_start = 0;
                        disp_frac = 0;
                        disp_armed = true;
                    } else if (disp_armed) {
                        if (!disp_hold_start) disp_hold_start = t;
                        disp_frac = (float)((t - disp_hold_start) / 1.0);
                        if (disp_frac >= 1) {
                            run_flash_flow(&cv, &image);
                            disp_hold_start = 0;
                            disp_frac = 0;
                            disp_armed = false;
                            st.dirty = true;
                        }
                    }
                } else {
                    pwr_hold_start = 0;
                    pwr_frac = 0;
                }
                st.next_poll = t + 0.008;
            }
            break;

        case MODE_APP:
            if (t >= st.next_poll) {
                uint8_t pkt[APP_DATASIZE];
                if (app_read_packet(pkt)) {
                    app_fails = 0;
                    if (pkt[4] & STATUS_PWR) {
                        if (!pwr_hold_start) pwr_hold_start = t;
                        pwr_frac = (float)((t - pwr_hold_start) / 0.5);
                        if (pwr_frac >= 1) {
                            system("poweroff");
                            sleep(10);
                            exit(0);
                        }
                    } else {
                        pwr_hold_start = 0;
                        pwr_frac = 0;
                    }
                } else if (++app_fails >= 25) {
                    st.mode = MODE_NONE;
                    st.dirty = true;
                }
                st.next_poll = t + 0.008;
            }
            break;
        }

        /* redraw only when something changed */
        if (st.dirty || (pwr_frac != pwr_drawn &&
                         (pwr_frac == 0 || pwr_frac - pwr_drawn > 0.05f ||
                          pwr_frac >= 1)) ||
            (disp_frac != disp_drawn &&
             (disp_frac == 0 || disp_frac - disp_drawn > 0.05f ||
              disp_frac >= 1))) {
            pwr_drawn = pwr_frac;
            disp_drawn = disp_frac;
            st.dirty = false;
            draw_status_screen(&cv, &st, &image, pwr_frac, disp_frac);
        }
    }
}
