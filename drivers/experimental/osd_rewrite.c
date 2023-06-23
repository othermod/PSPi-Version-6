// compile w/ gcc -o drawsquare drawsquare.c -lbcm_host -I/opt/vc/include -L/opt/vc/lib
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <bcm_host.h>

// Define a struct to hold the rectangle data
typedef struct {
    int x_start;
    int y_start;
    int x_size;
    int y_size;
} Rectangle;

int main() {
    uint32_t displayNumber = 0;
    VC_IMAGE_TYPE_T type = VC_IMAGE_RGBA32;
    bcm_host_init();
    DISPMANX_DISPLAY_HANDLE_T display = vc_dispmanx_display_open(displayNumber);
    DISPMANX_MODEINFO_T info;
    vc_dispmanx_display_get_info(display, &info);
    uint32_t vc_image_ptr;

    // Create an array of charge_indicator
    Rectangle charge_indicator[] = {
        {15,3,1,8},
        {12,4,2,2},
        {10,6,1,2},
        {7,7,2,1},
        {17,8,2,2},
        {20,7,1,1},
        {22,6,2,1}
    };

    // Create a single pixel image for orange color
    uint32_t orange_pixel[1];
    orange_pixel[0] = 0xFF00A5FF; // orange color

    // Create a resource for the orange pixel
    DISPMANX_RESOURCE_HANDLE_T orange_resource = vc_dispmanx_resource_create(type, 1, 1, &vc_image_ptr);

    // Write the orange pixel data to the resource
    VC_RECT_T dst_rect;
    vc_dispmanx_rect_set(&dst_rect, 0, 0, 1, 1);
    vc_dispmanx_resource_write_data(orange_resource, type, sizeof(uint32_t), orange_pixel, &dst_rect);

    // Start an update
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);

    // Set alpha to opaque
    VC_DISPMANX_ALPHA_T alpha = {DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0};

    // Loop over the array of charge_indicator
    for (int i = 0; i < sizeof(charge_indicator) / sizeof(Rectangle); i++) {
        Rectangle rect = charge_indicator[i];
        // Add the rectangle to the display
        VC_RECT_T src_rect;
        uint16_t charge_start_position_x = info.width - 40;
        uint16_t charge_start_position_y = 5;
        vc_dispmanx_rect_set(&src_rect, 0, 0, 1 << 16, 1 << 16);
        vc_dispmanx_rect_set(&dst_rect, rect.x_start + charge_start_position_x, rect.y_start + charge_start_position_y, rect.x_size, rect.y_size);
        DISPMANX_ELEMENT_HANDLE_T element = vc_dispmanx_element_add(update, display, 2000 + i, &dst_rect, orange_resource, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE);
    }

    // Submit the update
    vc_dispmanx_update_submit_sync(update);

    // Pause to let the user see the charge_indicator
    sleep(5);

    // Start a new update to remove the charge_indicator
    update = vc_dispmanx_update_start(0);
    for (int i = 0; i < sizeof(charge_indicator) / sizeof(Rectangle); i++) {
        vc_dispmanx_element_remove(update, 2000 + i);
    }
    vc_dispmanx_update_submit_sync(update);

    // Delete the resources and close the display
    vc_dispmanx_resource_delete(orange_resource);
    vc_dispmanx_display_close(display);

    return 0;
}
