#include <stdlib.h>
#include <unistd.h>
#include <bcm_host.h>

#define whiteColor 0xFFFFFFFF
#define blackColor 0xFF000000

typedef struct {
    int x_start;
    int y_start;
    int x_size;
    int y_size;
    uint32_t color;
} Rectangle;

// WiFi Indicator Segments
const Rectangle WIFI_SEGMENTS[] = {
    {33, 0, 5, 15, whiteColor}, // white outline
    {38, 4, 4, 11, whiteColor},
    {42, 8, 4, 7, whiteColor},
    {34, 1, 3, 13, blackColor}, // black bars
    {38, 5, 3, 9, blackColor},
    {42, 9, 3, 5, blackColor},
};

// Array to store element handles
#define MAX_WIFI_ELEMENTS 6
DISPMANX_ELEMENT_HANDLE_T wifi_elements[MAX_WIFI_ELEMENTS];

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

void draw_wifi_indicator(DISPMANX_DISPLAY_HANDLE_T display, DISPMANX_MODEINFO_T info) {
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    VC_DISPMANX_ALPHA_T alpha = {DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0};

    for (int i = 0; i < sizeof(WIFI_SEGMENTS) / sizeof(Rectangle); i++) {
        Rectangle rect = WIFI_SEGMENTS[i];
        VC_RECT_T src_rect, dst_rect;
        vc_dispmanx_rect_set(&src_rect, 0, 0, 1 << 16, 1 << 16);
        vc_dispmanx_rect_set(&dst_rect, info.width - rect.x_start - rect.x_size, rect.y_start, rect.x_size, rect.y_size);
        DISPMANX_RESOURCE_HANDLE_T resource = create_color_resource(rect.color);
        DISPMANX_ELEMENT_HANDLE_T element = vc_dispmanx_element_add(update, display, 2000 + i, &dst_rect, resource, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE);
        wifi_elements[i] = element;
        vc_dispmanx_resource_delete(resource);
    }
    vc_dispmanx_update_submit_sync(update);
}

void remove_wifi_indicator(DISPMANX_DISPLAY_HANDLE_T display) {
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);

    for (int i = 0; i < sizeof(WIFI_SEGMENTS) / sizeof(Rectangle); i++) {
        vc_dispmanx_element_remove(update, wifi_elements[i]);
    }
    vc_dispmanx_update_submit_sync(update);
}

int main() {
    DISPMANX_DISPLAY_HANDLE_T display;
    DISPMANX_MODEINFO_T info;
    initialize_bcm(&display, &info);
    while (1) {
      // Drawing the WiFi indicator
      draw_wifi_indicator(display, info);
      sleep(1); // Display for a period of time
      remove_wifi_indicator(display);
      sleep(1); // Display for a period of time
    }

    vc_dispmanx_display_close(display);
    bcm_host_deinit(); // Properly deinitialize the bcm_host library

    return 0;
}
