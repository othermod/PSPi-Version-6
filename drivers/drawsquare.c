// compile w/ gcc -o drawsquare drawsquare.c -lbcm_host -I/opt/vc/include -L/opt/vc/lib
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <bcm_host.h>

int main(){
    uint32_t displayNumber = 0;
    VC_IMAGE_TYPE_T type = VC_IMAGE_RGBA32;
    bcm_host_init();
    DISPMANX_DISPLAY_HANDLE_T display = vc_dispmanx_display_open(displayNumber);
    DISPMANX_MODEINFO_T info;
    vc_dispmanx_display_get_info(display, &info);
    uint32_t vc_image_ptr;
    DISPMANX_RESOURCE_HANDLE_T resource = vc_dispmanx_resource_create(type, 100, 100, &vc_image_ptr);
    VC_RECT_T src_rect;
    VC_RECT_T dst_rect;
    uint32_t image[100*100];
    for (int i = 0; i < 100*100; i++) image[i] = 0xFFFFFFFF; // white color
    vc_dispmanx_rect_set(&dst_rect, 0, 0, 100, 100);
    vc_dispmanx_resource_write_data(resource, type, 100 * sizeof(uint32_t), image, &dst_rect);
    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    VC_DISPMANX_ALPHA_T alpha = {DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0};
    vc_dispmanx_rect_set(&src_rect, 0, 0, 100 << 16, 100 << 16);
    vc_dispmanx_rect_set(&dst_rect, (info.width - 100) / 2, (info.height - 100) / 2, 100, 100);
    DISPMANX_ELEMENT_HANDLE_T element = vc_dispmanx_element_add(update, display, 2000, &dst_rect, resource, &src_rect, DISPMANX_PROTECTION_NONE, &alpha, NULL, DISPMANX_NO_ROTATE);
    vc_dispmanx_update_submit_sync(update);
    sleep(5);
    update = vc_dispmanx_update_start(0);
    vc_dispmanx_element_remove(update, element);
    vc_dispmanx_update_submit_sync(update);
    vc_dispmanx_resource_delete(resource);
    vc_dispmanx_display_close(display);
    return 0;
}
