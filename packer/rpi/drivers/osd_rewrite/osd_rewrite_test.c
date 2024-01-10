#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <bcm_host.h>

#define whiteColor 0xFFFFFFFF
#define blackColor 0xFF000000
#define greenColor 0xFF00FF00

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

// Assuming a maximum of 10 elements can be drawn at once
#define MAX_ELEMENTS 10
DISPMANX_ELEMENT_HANDLE_T element_handles[MAX_ELEMENTS];
int element_count = 0;

int batteryPercent = 50; // This should be updated with the actual battery percentage

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

    // Reset the element count before drawing new elements
    element_count = 0;

    for (int i = 0; i < num_rects; i++) {
        Rectangle rect = rects[i];
        VC_RECT_T src_rect, dst_rect;
        vc_dispmanx_rect_set(&src_rect, 0, 0, 1 << 16, 1 << 16);
        vc_dispmanx_rect_set(&dst_rect, info.width - rect.x_start - rect.x_size, rect.y_start, rect.x_size, rect.y_size);
        DISPMANX_RESOURCE_HANDLE_T current_resource = create_color_resource(rect.color);
        DISPMANX_ELEMENT_HANDLE_T element = vc_dispmanx_element_add(update, display, 2000 + i, &dst_rect, current_resource, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE);

        // Store the element handle for later removal
        if (element_count < MAX_ELEMENTS) {
            element_handles[element_count++] = element;
        }

        vc_dispmanx_resource_delete(current_resource);
    }
    vc_dispmanx_update_submit_sync(update);
}

void remove_indicator() {
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);

    // Remove each element using the stored handles
    for (int i = 0; i < element_count; i++) {
        vc_dispmanx_element_remove(update, element_handles[i]);
    }
    vc_dispmanx_update_submit_sync(update);

    // Reset the element count after removal
    element_count = 0;
}

void draw_indicator(IndicatorType type, DISPMANX_DISPLAY_HANDLE_T display, DISPMANX_MODEINFO_T info, int batteryPercent) {
    switch (type) {
        case BATTERY: {
            Rectangle battery_segments[] = {
                {0, 0, 30, 15, whiteColor}, // white outline
                {1, 1, 28, 13, blackColor}, // black inner
                {2, 2, (batteryPercent * 28) / 100, 11, greenColor}, // dynamic capacity
            };
            draw_rectangles(display, battery_segments, sizeof(battery_segments) / sizeof(Rectangle), info);
            break;
        }
        case WIFI:
            draw_rectangles(display, WIFI_SEGMENTS, sizeof(WIFI_SEGMENTS) / sizeof(Rectangle), info);
            break;
        case VOLUME:
            draw_rectangles(display, VOLUME_SEGMENTS, sizeof(VOLUME_SEGMENTS) / sizeof(Rectangle), info);
            break;
    }
}

int main() {
    DISPMANX_DISPLAY_HANDLE_T display;
    DISPMANX_MODEINFO_T info;
    initialize_bcm(&display, &info);

    // Drawing all indicators
    draw_indicator(BATTERY, display, info, batteryPercent); // Pass batteryPercent to the function
    draw_indicator(WIFI, display, info, batteryPercent); // Pass batteryPercent for consistency
    //draw_indicator(VOLUME, display, info, batteryPercent); // Pass batteryPercent for consistency

    sleep(1); // Display for 5 seconds
    //remove_indicator();
    batteryPercent = 25;
    remove_indicator();
    //draw_indicator(BATTERY, display, info, batteryPercent); // Pass batteryPercent to the function
    sleep(1); // Display for 5 seconds

    // Removing all indicators
    remove_indicator();

    vc_dispmanx_display_close(display);
    bcm_host_deinit(); // Properly deinitialize the bcm_host library

    return 0;
}
