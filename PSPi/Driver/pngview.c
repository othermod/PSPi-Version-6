#define _GNU_SOURCE

#include <assert.h>
#include <ctype.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "backgroundLayer.h"
#include "imageLayer.h"
#include "key.h"
#include "loadpng.h"

#include "bcm_host.h"

#define NDEBUG

const char *program = NULL;
volatile bool run = true;
static void
signalHandler(int signalNumber){
    switch (signalNumber) {
    case SIGINT:
    case SIGTERM:
        run = false;
        break;
    };
}

void usage(void)
{
    fprintf(stderr, "Usage: %s ", program);
    fprintf(stderr, "[-x <offset>] [-y <offset>] <file.png>\n");
    fprintf(stderr, "    -d - Raspberry Pi display number\n");
    fprintf(stderr, "    -x - offset (pixels from the left)\n");
    fprintf(stderr, "    -y - offset (pixels from the top)\n");
    exit(EXIT_FAILURE);
}

int main(int argc, char *argv[]){
    uint16_t background = 0; // no background
    int32_t layer = 100000; // specified high layer
    uint32_t displayNumber = 0; // specified display
    int32_t xOffset = 0;
    int32_t yOffset = 0;

    bool xOffsetSet = false;
    bool yOffsetSet = false;

    program = basename(argv[0]);

    int opt = 0;

    while ((opt = getopt(argc, argv, "x:y")) != -1) {
        switch(opt) {
        case 'x':
            xOffset = strtol(optarg, NULL, 10);
            xOffsetSet = true;
            break;
        case 'y':
            yOffset = strtol(optarg, NULL, 10);
            yOffsetSet = true;
            break;
        default:
            usage();
            break;
        }
    }

    if (optind >= argc) {usage(); }

    IMAGE_LAYER_T imageLayer;

    char *imagePath = argv[optind];

    if(strcmp(imagePath, "-") == 0) {
		printf("stdin\n");
        if (loadPngFile(&(imageLayer.image), stdin) == false) { // Use stdin
            fprintf(stderr, "unable to stdin load %s\n", imagePath);
            exit(EXIT_FAILURE);
        }
    } else {
		printf("path\n");
        if (loadPng(&(imageLayer.image), imagePath) == false) { // Load image from path
            fprintf(stderr, "unable to path load %s\n", imagePath);
            exit(EXIT_FAILURE);
        }
    }

    if (signal(SIGINT, signalHandler) == SIG_ERR) {
        perror("installing SIGINT signal handler");
        exit(EXIT_FAILURE);
    }
    if (signal(SIGTERM, signalHandler) == SIG_ERR) {
        perror("installing SIGTERM signal handler");
        exit(EXIT_FAILURE);
    }

    bcm_host_init();

    DISPMANX_DISPLAY_HANDLE_T display
        = vc_dispmanx_display_open(displayNumber);
    assert(display != 0);

    DISPMANX_MODEINFO_T info;
    int result = vc_dispmanx_display_get_info(display, &info);
    assert(result == 0);

    BACKGROUND_LAYER_T backgroundLayer;

    if (background > 0) {initBackgroundLayer(&backgroundLayer, background, 0);} //does nothing now

    createResourceImageLayer(&imageLayer, layer);

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    if (background > 0) {addElementBackgroundLayer(&backgroundLayer, display, update); }
    if (xOffsetSet == false) {xOffset = (info.width - imageLayer.image.width) / 2;}
    if (yOffsetSet == false) {yOffset = (info.height - imageLayer.image.height) / 2;}

    addElementImageLayerOffset(&imageLayer,
                               xOffset,
                               yOffset,
                               display,
                               update);

    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

    while (run) {
        pause();
	}
    keyboardReset();
    if (background > 0) {destroyBackgroundLayer(&backgroundLayer);}
    destroyImageLayer(&imageLayer);
    result = vc_dispmanx_display_close(display);
    assert(result == 0);
    return 0;
}