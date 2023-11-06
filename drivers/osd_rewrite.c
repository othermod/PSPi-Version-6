//gcc -o osd_rewrite osd_rewrite.c -lbcm_host -I/opt/vc/include -L/opt/vc/lib
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <bcm_host.h>

#define grayColor 0xFF969696
#define whiteColor 0xFFFFFFFF
#define blackColor 0xFF000000
#define greenColor 0xFF00FF00
#define redColor 0xFF0000FF
#define blueColor 0xFFFF0000

typedef struct {
    int x_start;
    int y_start;
    int x_size;
    int y_size;
    uint32_t color;
} Rectangle;

typedef enum {
    BATTERY,
    WIFI,
    VOLUME
} IndicatorType;

const Rectangle BATTERY_SEGMENTS[] = {
  //{xstart, ystart, xsize, ysize, 0xOpacityGreenBlueRed}
    {0, 0, 30, 15, whiteColor}, //white outline
    {1, 1, 28, 13, blackColor}, //black inner
    {2, 2, 15, 11, greenColor}, // capacity. xsize needs to vary according to charge status
};

const Rectangle WIFI_SEGMENTS[] = {
    {33, 0, 5, 15, whiteColor}, // white outline
    {38, 4, 4, 11, whiteColor},
    {42, 8, 4, 7, whiteColor},

    {34, 1, 3, 13, blackColor}, // black bars
    {38, 5, 3, 9, blackColor},
    {42, 9, 3, 5, blackColor},
};

const Rectangle VOLUME_SEGMENTS[] = {
    {100, 0, 20, 10, whiteColor}
};

void initialize_bcm(DISPMANX_DISPLAY_HANDLE_T* display, DISPMANX_MODEINFO_T* info) {
    bcm_host_init();
    *display = vc_dispmanx_display_open(0);
    vc_dispmanx_display_get_info(*display, info);
}

DISPMANX_RESOURCE_HANDLE_T create_color_resource(uint32_t color) {
    VC_IMAGE_TYPE_T type = VC_IMAGE_RGBA32;
    uint32_t vc_image_ptr;
    uint32_t pixel[1] = {color};
    DISPMANX_RESOURCE_HANDLE_T resource = vc_dispmanx_resource_create(type, 1, 1, &vc_image_ptr);
    VC_RECT_T dst_rect;
    vc_dispmanx_rect_set(&dst_rect, 0, 0, 1, 1);
    vc_dispmanx_resource_write_data(resource, type, sizeof(uint32_t), pixel, &dst_rect);
    return resource;
}

void draw_rectangles(DISPMANX_DISPLAY_HANDLE_T display, const Rectangle* rects, int num_rects, DISPMANX_MODEINFO_T info) {
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    VC_DISPMANX_ALPHA_T alpha = {DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0};
    for (int i = 0; i < num_rects; i++) {
        Rectangle rect = rects[i];
        VC_RECT_T src_rect, dst_rect;
        vc_dispmanx_rect_set(&src_rect, 0, 0, 1 << 16, 1 << 16);
        vc_dispmanx_rect_set(&dst_rect, info.width - rect.x_start - rect.x_size, rect.y_start, rect.x_size, rect.y_size);
        DISPMANX_RESOURCE_HANDLE_T current_resource = create_color_resource(rect.color);
        DISPMANX_ELEMENT_HANDLE_T element = vc_dispmanx_element_add(update, display, 200000 + i, &dst_rect, current_resource, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE);
        vc_dispmanx_resource_delete(current_resource);
    }
    vc_dispmanx_update_submit_sync(update);
}

void remove_rectangles(int num_rects) {
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    for (int i = 0; i < num_rects; i++) {
        vc_dispmanx_element_remove(update, 200000 + i);
    }
    vc_dispmanx_update_submit_sync(update);
}

void draw_indicator(IndicatorType type, DISPMANX_DISPLAY_HANDLE_T display, DISPMANX_MODEINFO_T info) {
    switch (type) {
        case BATTERY:
            draw_rectangles(display, BATTERY_SEGMENTS, sizeof(BATTERY_SEGMENTS) / sizeof(Rectangle), info);
            break;
        case WIFI:
            draw_rectangles(display, WIFI_SEGMENTS, sizeof(WIFI_SEGMENTS) / sizeof(Rectangle), info);
            break;
        case VOLUME:
            draw_rectangles(display, VOLUME_SEGMENTS, sizeof(VOLUME_SEGMENTS) / sizeof(Rectangle), info);
            break;
    }
}

void remove_indicator(IndicatorType type) {
    int num_rects = 0;
    switch (type) {
        case BATTERY:
            num_rects = sizeof(BATTERY_SEGMENTS) / sizeof(Rectangle);
            break;
        case WIFI:
            num_rects = sizeof(WIFI_SEGMENTS) / sizeof(Rectangle);
            break;
        case VOLUME:
            num_rects = sizeof(VOLUME_SEGMENTS) / sizeof(Rectangle);
            break;
    }
    remove_rectangles(num_rects);
}

int main() {
    DISPMANX_DISPLAY_HANDLE_T display;
    DISPMANX_MODEINFO_T info;
    initialize_bcm(&display, &info);

    // Drawing all indicators
    draw_indicator(BATTERY, display, info);
    draw_indicator(WIFI, display, info);
    //draw_indicator(VOLUME, display, info);

    sleep(5); // Display for 5 seconds

    // Removing all indicators
    remove_indicator(BATTERY);
    remove_indicator(WIFI);
    remove_indicator(VOLUME);

    vc_dispmanx_display_close(display);
    return 0;
}
