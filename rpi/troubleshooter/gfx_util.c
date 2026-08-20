/*
 * gfx_util.c — KMS/DRM display + drawing primitives (see gfx_util.h)
 *
 * Compile: gcc -O2 -Wall -I/usr/include/libdrm -c gfx_util.c
 * Link:   ... -ldrm -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <poll.h>
#include <sys/mman.h>

#include <drm.h>
#include <drm_mode.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

#include "gfx_util.h"

/* ------------------------------------------------------------------ */
/* DRM display                                                        */
/* ------------------------------------------------------------------ */

static volatile int flip_done = 0;
static void on_flip(int fd, unsigned seq, unsigned s, unsigned u, void *ud)
{ (void)fd; (void)seq; (void)s; (void)u; (void)ud; flip_done = 1; }

void present(Display *d)
{
    if (!d->flip_ok) return;

    int issued = 0;
    for (int t = 0; t < 3; t++) {
        if (drmModePageFlip(d->fd, d->crtc_id, d->fb[d->paint],
                            DRM_MODE_PAGE_FLIP_EVENT, NULL) == 0) { issued = 1; break; }
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
       only failure mode drmModePageFlip itself can't report), the old buffer
       may still be scanned out -- painting on it would tear. Treat a silent
       timeout exactly like an explicit flip failure: fall back to painting in
       place on the scan buffer. */
    flip_done = 0;
    for (int w = 0; w < 200 && !flip_done; w++) {
        struct pollfd pfd = { .fd = d->fd, .events = POLLIN };
        if (poll(&pfd, 1, 10) > 0) {
            drmEventContext ev = {
                .version = DRM_EVENT_CONTEXT_VERSION,
                .page_flip_handler = on_flip,
            };
            drmHandleEvent(d->fd, &ev);
        }
    }
    if (!flip_done) {
        d->flip_ok = false;
        d->buf = (uint32_t *)d->map[d->scan];
        fprintf(stderr, "warning: page flip event timed out, painting in place\n");
        return;
    }

    d->scan = d->paint;
    d->paint ^= 1;                  /* old scanout is now free to draw */
    d->buf = (uint32_t *)d->map[d->paint];
}

bool display_init(Display *d, const char **conn_name)
{
    const char *cards[] = { "/dev/dri/card0", "/dev/dri/card1" };
    drmModeRes *res = NULL;
    drmModeConnector *conn = NULL;

    d->fd = -1;
    /* pick the first card that has a connected display; card numbering can
       change between boots (e.g. DPI panel ended up on card1) so scan both */
    for (size_t ci = 0; ci < sizeof(cards) / sizeof(cards[0]) && !conn; ci++) {
        int fd = open(cards[ci], O_RDWR);
        if (fd < 0) continue;
        if (drmSetMaster(fd) != 0) { close(fd); continue; }
        res = drmModeGetResources(fd);
        if (!res) { close(fd); continue; }
        for (int i = 0; i < res->count_connectors; i++) {
            drmModeConnector *c = drmModeGetConnector(fd, res->connectors[i]);
            if (c && c->connection == DRM_MODE_CONNECTED && c->count_modes > 0) {
                conn = c;
                break;
            }
            if (c) drmModeFreeConnector(c);
        }
        if (conn) { d->fd = fd; break; }
        drmModeFreeResources(res);
        res = NULL;
        close(fd);
    }

    if (!conn) {
        fprintf(stderr, "error: no DRM card with a connected display "
                        "(run with sudo?)\n");
        return false;
    }
    if (conn_name) *conn_name = drmModeGetConnectorTypeName(conn->connector_type);

    drmModeModeInfo *mode = &conn->modes[0];
    for (int i = 0; i < conn->count_modes; i++)
        if (conn->modes[i].type & DRM_MODE_TYPE_PREFERRED) { mode = &conn->modes[i]; break; }

    uint32_t crtc_id = 0;
    if (conn->encoder_id) {
        drmModeEncoder *enc = drmModeGetEncoder(d->fd, conn->encoder_id);
        if (enc) {
            crtc_id = (enc->crtc_id) ? enc->crtc_id : res->crtcs[0];
            drmModeFreeEncoder(enc);
        }
    }
    if (!crtc_id && res->count_crtcs > 0) crtc_id = res->crtcs[0];

    d->crtc_id = crtc_id;
    d->w = mode->hdisplay;
    d->h = mode->vdisplay;
    d->pitch = 0;
    d->size = 0;
    d->scan = 0;
    d->paint = 1;
    d->flip_ok = true;

    /* create two dumb framebuffers (front/back) */
    for (int i = 0; i < 2; i++) {
        struct drm_mode_create_dumb cd = {
            .width = (uint32_t)d->w, .height = (uint32_t)d->h, .bpp = 32,
        };
        if (drmIoctl(d->fd, DRM_IOCTL_MODE_CREATE_DUMB, &cd) != 0) { perror("CREATE_DUMB"); return false; }
        if (drmModeAddFB(d->fd, cd.width, cd.height, 24, 32, cd.pitch, cd.handle, &d->fb[i]) != 0) { perror("drmModeAddFB"); return false; }

        struct drm_mode_map_dumb md = { .handle = cd.handle };
        if (drmIoctl(d->fd, DRM_IOCTL_MODE_MAP_DUMB, &md) != 0) { perror("MAP_DUMB"); return false; }

        d->map[i] = mmap(NULL, cd.size, PROT_READ | PROT_WRITE, MAP_SHARED, d->fd, md.offset);
        if (d->map[i] == MAP_FAILED) { perror("mmap"); return false; }
        d->pitch = cd.pitch / 4;
        d->size = cd.size;
    }
    d->buf = (uint32_t *)d->map[d->paint];

    if (drmModeSetCrtc(d->fd, crtc_id, d->fb[0], 0, 0, &conn->connector_id, 1, mode) != 0) {
        perror("drmModeSetCrtc");
        return false;
    }
    (void)drmModeSetCursor(d->fd, crtc_id, 0, 0, 0);   /* hide cursor plane */

    printf("display: %s %dx%d @%dHz\n",
           conn_name ? *conn_name : "?", d->w, d->h, mode->vrefresh);
    drmModeFreeConnector(conn);
    drmModeFreeResources(res);
    return true;
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
/* 5x7 bitmap font (41 glyphs: A-Z 0-9 ':' '-' '/' '+' and space)                */
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