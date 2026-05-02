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
#include <stdbool.h>

#include "element_change.h"
#include "image.h"
#include "loadpng.h"
#include "spriteLayer.h"

//-------------------------------------------------------------------------

void initSpriteLayer(
    SPRITE_LAYER_T *s,
    int columns,
    int rows,
    const char *file,
    int32_t layer)
{
    int result = 0;

    bool loaded = loadPng(&(s->image), file);

    if (loaded == false)
    {
        fprintf(stderr, "sprite: unable to load %s\n", file);
        exit(EXIT_FAILURE);
    }

    s->columns = columns;
    s->rows = rows;
    s->width = s->image.width / s->columns;
    s->height = s->image.height / s->rows;
    s->xOffsetMax = (s->columns - 1) * s->width;
    s->xOffset = 0;
    s->yOffsetMax = (s->rows - 1) * s->height;
    s->yOffset = 0;

    //---------------------------------------------------------------------

    uint32_t vc_image_ptr;

    s->layer = layer;

    s->frontResource =
        vc_dispmanx_resource_create(
            s->image.type,
            s->image.width | (s->image.pitch << 16),
            s->image.height | (s->image.alignedHeight << 16),
            &vc_image_ptr);
    assert(s->frontResource != 0);

    s->backResource =
        vc_dispmanx_resource_create(
            s->image.type,
            s->image.width | (s->image.pitch << 16),
            s->image.height | (s->image.alignedHeight << 16),
            &vc_image_ptr);
    assert(s->backResource != 0);

    //---------------------------------------------------------------------

    vc_dispmanx_rect_set(&(s->bmpRect),
                         0,
                         0,
                         s->image.width,
                         s->image.height);

    result = vc_dispmanx_resource_write_data(s->frontResource,
                                             s->image.type,
                                             s->image.pitch,
                                             s->image.buffer,
                                             &(s->bmpRect));
    assert(result == 0);

    result = vc_dispmanx_resource_write_data(s->backResource,
                                             s->image.type,
                                             s->image.pitch,
                                             s->image.buffer,
                                             &(s->bmpRect));
    assert(result == 0);
}

//-------------------------------------------------------------------------

void
addElementSpriteLayerOffset(
    SPRITE_LAYER_T *s,
    int32_t xOffset,
    int32_t yOffset,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    vc_dispmanx_rect_set(&(s->srcRect),
                         0 << 16,
                         0 << 16,
                         s->image.width << 16,
                         s->image.height << 16);

    vc_dispmanx_rect_set(&(s->dstRect),
                         xOffset,
                         yOffset,
                         s->width,
                         s->height);

    addElementSpriteLayer(s, display, update);
}

//-------------------------------------------------------------------------

void
addElementSpriteLayerCentered(
    SPRITE_LAYER_T *s,
    DISPMANX_MODEINFO_T *info,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    vc_dispmanx_rect_set(&(s->srcRect),
                         s->xOffset << 16,
                         s->yOffset << 16,
                         s->width << 16,
                         s->height << 16);

    vc_dispmanx_rect_set(&(s->dstRect),
                         (info->width - s->width) / 2,
                         (info->height - s->height) / 2,
                         s->width,
                         s->height);

    addElementSpriteLayer(s, display, update);
}

//-------------------------------------------------------------------------

void
addElementSpriteLayer(
    SPRITE_LAYER_T *s,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    VC_DISPMANX_ALPHA_T alpha =
    {
        DISPMANX_FLAGS_ALPHA_FROM_SOURCE, 
        255, /*alpha 0->255*/
        0
    };

    //---------------------------------------------------------------------

    s->element =
        vc_dispmanx_element_add(update,
                                display,
                                s->layer,
                                &(s->dstRect),
                                s->frontResource,
                                &(s->srcRect),
                                DISPMANX_PROTECTION_NONE,
                                &alpha,
                                NULL, // clamp
                                DISPMANX_NO_ROTATE);
    assert(s->element != 0);
}

//-------------------------------------------------------------------------

void
updatePositionSpriteLayer(
    SPRITE_LAYER_T *s,
    DISPMANX_UPDATE_HANDLE_T update)
{
    int result = 0;

    //---------------------------------------------------------------------

    s->xOffset += s->width;

    if (s->xOffset > s->xOffsetMax)
    {
        s->xOffset = 0;
        s->yOffset += s->height;

        if (s->yOffset > s->yOffsetMax)
        {
            s->yOffset = 0;
        }
    }

    //---------------------------------------------------------------------

    vc_dispmanx_rect_set(&(s->srcRect),
                         s->xOffset << 16,
                         s->yOffset << 16,
                         s->width << 16,
                         s->height << 16);

    result = 
    vc_dispmanx_element_change_attributes(update,
                                          s->element,
                                          ELEMENT_CHANGE_SRC_RECT,
                                          0,
                                          255,
                                          &(s->dstRect),
                                          &(s->srcRect),
                                          0,
                                          DISPMANX_NO_ROTATE);
    assert(result == 0);

    //---------------------------------------------------------------------

    DISPMANX_RESOURCE_HANDLE_T tmp = s->frontResource;
    s->frontResource = s->backResource;
    s->backResource = tmp;
}

//-------------------------------------------------------------------------

void
destroySpriteLayer(
    SPRITE_LAYER_T *s)
{
    int result = 0;

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);
    result = vc_dispmanx_element_remove(update, s->element);
    assert(result == 0);
    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

    //---------------------------------------------------------------------

    result = vc_dispmanx_resource_delete(s->frontResource);
    assert(result == 0);
    result = vc_dispmanx_resource_delete(s->backResource);
    assert(result == 0);

    //---------------------------------------------------------------------

    destroyImage(&(s->image));
}

