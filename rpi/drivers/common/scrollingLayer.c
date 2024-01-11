//-------------------------------------------------------------------------
//
// The MIT License (MIT)
//
// Copyright (c) 2013 Andrew Duncan
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so, subject to
// the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
// CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
// TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//
//-------------------------------------------------------------------------

#include <assert.h>
#include <ctype.h>
#include <stdbool.h>

#include "element_change.h"
#include "image.h"
#include "loadpng.h"
#include "scrollingLayer.h"

#include "bcm_host.h"

//-------------------------------------------------------------------------

void
initScrollingLayer(SCROLLING_LAYER_T *sl,
    const char* file,
    int32_t layer)
{
    int result = 0;

    //---------------------------------------------------------------------
    if (loadScrollingLayerPng(&sl->image, file, true, true) == false)
    {
        fprintf(stderr, "scrollingBgLayer: unable to load %s\n", file);
        exit(EXIT_FAILURE);
    }

    sl->direction = 0;
    sl->directionMax = 7;

    sl->xDirections[0] = 0;
    sl->xDirections[1] = 3;
    sl->xDirections[2] = 4;
    sl->xDirections[3] = 3;
    sl->xDirections[4] = 0;
    sl->xDirections[5] = -3;
    sl->xDirections[6] = -4;
    sl->xDirections[7] = -3;

    sl->yDirections[0] = 4;
    sl->yDirections[1] = 3;
    sl->yDirections[2] = 0;
    sl->yDirections[3] = -3;
    sl->yDirections[4] = -4;
    sl->yDirections[5] = -3;
    sl->yDirections[6] = 0;
    sl->yDirections[7] = 3;

    //---------------------------------------------------------------------

    uint32_t vc_image_ptr;

    sl->layer = layer;

    sl->frontResource =
        vc_dispmanx_resource_create(
            sl->image.type,
            sl->image.width | (sl->image.pitch << 16),
            sl->image.height | (sl->image.alignedHeight << 16),
            &vc_image_ptr);
    assert(sl->frontResource != 0);

    sl->backResource =
        vc_dispmanx_resource_create(
            sl->image.type,
            sl->image.width | (sl->image.pitch << 16),
            sl->image.height | (sl->image.alignedHeight << 16),
            &vc_image_ptr);
    assert(sl->backResource != 0);

    //---------------------------------------------------------------------

    vc_dispmanx_rect_set(&(sl->bmpRect),
                         0,
                         0,
                         sl->image.width,
                         sl->image.height);

    result = vc_dispmanx_resource_write_data(sl->frontResource,
                                             sl->image.type,
                                             sl->image.pitch,
                                             sl->image.buffer,
                                             &(sl->bmpRect));
    assert(result == 0);

    result = vc_dispmanx_resource_write_data(sl->backResource,
                                             sl->image.type,
                                             sl->image.pitch,
                                             sl->image.buffer,
                                             &(sl->bmpRect));
    assert(result == 0);
}

//-------------------------------------------------------------------------

void
addElementScrollingLayerCentered(
    SCROLLING_LAYER_T *sl,
    DISPMANX_MODEINFO_T *info,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    sl->viewWidth = sl->image.width / 2;
    sl->viewHeight = sl->image.height / 2;

    sl->xOffsetMax = sl->viewWidth - 1;
    sl->xOffset = sl->xOffsetMax / 2;

    sl->yOffsetMax = sl->viewHeight - 1;
    sl->yOffset = sl->yOffsetMax / 2;

    if (sl->viewWidth > info->width)
    {
        sl->viewWidth = info->width;
    }

    if (sl->viewHeight > info->height)
    {
        sl->viewHeight = info->height;
    }

    vc_dispmanx_rect_set(&sl->srcRect,
                         sl->xOffset << 16,
                         sl->yOffset << 16,
                         sl->viewWidth << 16,
                         sl->viewHeight << 16);

    vc_dispmanx_rect_set(&(sl->dstRect),
                         (info->width - sl->viewWidth) / 2,
                         (info->height - sl->viewHeight) / 2,
                         sl->viewWidth,
                         sl->viewHeight);

    addElementScrollingLayer(sl, display, update);
}

//-------------------------------------------------------------------------

void
addElementScrollingLayer(
    SCROLLING_LAYER_T *sl,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    VC_DISPMANX_ALPHA_T alpha =
    {
        DISPMANX_FLAGS_ALPHA_FROM_SOURCE, 
        255,
        0
    };

    sl->element = vc_dispmanx_element_add(update,
                                          display,
                                          sl->layer,
                                          &(sl->dstRect),
                                          sl->frontResource,
                                          &(sl->srcRect),
                                          DISPMANX_PROTECTION_NONE,
                                          &alpha,
                                          NULL,
                                          DISPMANX_NO_ROTATE);
    assert(sl->element != 0);
}

//-------------------------------------------------------------------------

void
setDirectionScrollingLayer(
    SCROLLING_LAYER_T *sl,
    char c)
{
    switch (tolower(c))
    {
    case ',':
    case '<':

        --(sl->direction);
        if (sl->direction < 0)
        {
            sl->direction = sl->directionMax;
        }

        break;

    case '.':
    case '>':

        ++(sl->direction);

        if (sl->direction > sl->directionMax)
        {
            sl->direction = 0;
        }

        break;

    default:

        // do nothing

        break;
    }
}

//-------------------------------------------------------------------------

void
updatePositionScrollingLayer(
    SCROLLING_LAYER_T *sl,
    DISPMANX_UPDATE_HANDLE_T update)
{
    int result = 0;

    //---------------------------------------------------------------------

    sl->xOffset += sl->xDirections[sl->direction];

    if (sl->xOffset < 0)
    {
        sl->xOffset = sl->xOffsetMax;
    }
    else if (sl->xOffset > sl->xOffsetMax)
    {
        sl->xOffset = 0;
    }

    sl->yOffset -= sl->yDirections[sl->direction];

    if (sl->yOffset < 0)
    {
        sl->yOffset = sl->yOffsetMax;
    }
    else if (sl->yOffset > sl->yOffsetMax)
    {
        sl->yOffset = 0;
    }

    //---------------------------------------------------------------------

    result = vc_dispmanx_element_change_source(update,
                                               sl->element,
                                               sl->backResource);
    assert(result == 0);

    vc_dispmanx_rect_set(&(sl->srcRect),
                         sl->xOffset << 16,
                         sl->yOffset << 16,
                         sl->viewWidth << 16,
                         sl->viewHeight << 16);

    result = 
    vc_dispmanx_element_change_attributes(update,
                                          sl->element,
                                          ELEMENT_CHANGE_SRC_RECT,
                                          0,
                                          255,
                                          &(sl->dstRect),
                                          &(sl->srcRect),
                                          0,
                                          DISPMANX_NO_ROTATE);
    assert(result == 0);

    //---------------------------------------------------------------------

    DISPMANX_RESOURCE_HANDLE_T tmp = sl->frontResource;
    sl->frontResource = sl->backResource;
    sl->backResource = tmp;
}

//-------------------------------------------------------------------------

void
destroyScrollingLayer(
    SCROLLING_LAYER_T *sl)
{
    int result = 0;

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);
    result = vc_dispmanx_element_remove(update, sl->element);
    assert(result == 0);
    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

    //---------------------------------------------------------------------

    result = vc_dispmanx_resource_delete(sl->frontResource);
    assert(result == 0);
    result = vc_dispmanx_resource_delete(sl->backResource);
    assert(result == 0);

    //---------------------------------------------------------------------

    destroyImage(&(sl->image));
}

//-------------------------------------------------------------------------

bool
loadScrollingLayerPng(
    IMAGE_T* image,
    const char *file,
    bool extendX,
    bool extendY)
{
    IMAGE_T baseImage;
    bool loaded = loadPng(&baseImage, file);

    if (loaded)
    {
        int32_t width = (extendX) ? baseImage.width*2 : baseImage.width;
        int32_t height = (extendY) ? baseImage.height*2 : baseImage.height;

        initImage(image, baseImage.type, width, height, false);

        if (extendX)
        {
            int32_t rowLength = (baseImage.width*baseImage.bitsPerPixel)/8;

            int32_t baseOffset = 0;
            int32_t offset = 0;

            int32_t y = 0;
            for (y = 0 ; y < baseImage.width ; y++)
            {
                baseOffset = y * baseImage.pitch;
                offset = y * image->pitch;

                memcpy(image->buffer + offset,
                       baseImage.buffer + baseOffset,
                       rowLength);

                memcpy(image->buffer + offset + rowLength,
                       baseImage.buffer + baseOffset,
                       rowLength);
            }
        }
        else
        {
            memcpy(image->buffer, baseImage.buffer, baseImage.size);
        }

        if (extendY)
        {
            int32_t size = image->pitch * baseImage.height;

            memcpy(image->buffer + size, image->buffer, size);
        }
    }

    return loaded;
}

