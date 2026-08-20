/*
 * gfx_util.h — minimal KMS/DRM display + drawing primitives for the Pi
 *
 * Part of the PSPi gamepad display tools. Provides:
 *   - scan over /dev/dri/card{0,1} for a connected display (card numbering
 *     can change between boots), CRTC setup, hidden cursor plane
 *   - double buffering with vblank-synchronized page flips (no flicker/tear)
 *   - a few 32-bit RGB canvas primitives: rects, circles, rings, lines,
 *     triangles, and a small 5x7 bitmap font
 */
#ifndef GFX_UTIL_H
#define GFX_UTIL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Double-buffered DRM display */
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

/* Take over the first card that has a connected display. Returns false and
   prints the reason if nothing usable is found. conn_name (optional) gets
   the connector type name (e.g. "DPI"). */
bool display_init(Display *d, const char **conn_name);

/* Swap the painted back buffer in at the next vblank; the buffer that was
   scanned out becomes the new paint target. */
void present(Display *d);

typedef struct { Display *d; } Canvas;

void px(Canvas *c, int x, int y, uint32_t col);
void clear(Canvas *c);
void fill_rect(Canvas *c, int x, int y, int w, int h, uint32_t col);
void rect_outline(Canvas *c, int x, int y, int w, int h, int t, uint32_t col);
void fill_circle(Canvas *c, int cx, int cy, int r, uint32_t col);
void ring_circle(Canvas *c, int cx, int cy, int r, int t, uint32_t col);
void draw_line(Canvas *c, int x0, int y0, int x1, int y1, int t, uint32_t col);
void fill_triangle(Canvas *c, int x0, int y0, int x1, int y1, int x2, int y2, uint32_t col);

/* 5x7 bitmap text (A-Z 0-9 ':' '-' '/' '+' ' '), scaled by `scale`; returns x
   after the last glyph. */
int draw_text(Canvas *c, int x, int y, const char *s, int scale, uint32_t col);

#endif /* GFX_UTIL_H */