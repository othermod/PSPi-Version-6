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
#include "imageLayer.h"

//-------------------------------------------------------------------------

void
initImageLayer(
    IMAGE_LAYER_T *il,
    int32_t width,
    int32_t height,
    VC_IMAGE_TYPE_T type)
{
    initImage(&(il->image), type, width, height, false);
}

//-------------------------------------------------------------------------

void
createResourceImageLayer(
    IMAGE_LAYER_T *il,
    int32_t layer)
{
    uint32_t vc_image_ptr;
    int result = 0;

    il->layer = layer;

    il->resource =
        vc_dispmanx_resource_create(
            il->image.type,
            il->image.width | (il->image.pitch << 16),
            il->image.height | (il->image.alignedHeight << 16),
            &vc_image_ptr);
    assert(il->resource != 0);

    //---------------------------------------------------------------------

    vc_dispmanx_rect_set(&(il->bmpRect),
                         0,
                         0,
                         il->image.width,
                         il->image.height);

    result = vc_dispmanx_resource_write_data(il->resource,
                                             il->image.type,
                                             il->image.pitch,
                                             il->image.buffer,
                                             &(il->bmpRect));
    assert(result == 0);
}

//-------------------------------------------------------------------------

void
addElementImageLayerOffset(
    IMAGE_LAYER_T *il,
    int32_t xOffset,
    int32_t yOffset,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    vc_dispmanx_rect_set(&(il->srcRect),
                         0 << 16,
                         0 << 16,
                         il->image.width << 16,
                         il->image.height << 16);

    vc_dispmanx_rect_set(&(il->dstRect),
                         xOffset,
                         yOffset,
                         il->image.width,
                         il->image.height);

    addElementImageLayer(il, display, update);
}

//-------------------------------------------------------------------------

void
addElementImageLayerCentered(
    IMAGE_LAYER_T *il,
    DISPMANX_MODEINFO_T *info,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    vc_dispmanx_rect_set(&(il->srcRect),
                         0 << 16,
                         0 << 16,
                         il->image.width << 16,
                         il->image.height << 16);

    vc_dispmanx_rect_set(&(il->dstRect),
                         (info->width - il->image.width) / 2,
                         (info->height - il->image.height) / 2,
                         il->image.width,
                         il->image.height);

    addElementImageLayer(il, display, update);
}

//-------------------------------------------------------------------------

void
addElementImageLayer(
    IMAGE_LAYER_T *il,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update)
{
    VC_DISPMANX_ALPHA_T alpha =
    {
        DISPMANX_FLAGS_ALPHA_FROM_SOURCE, 
        255, /*alpha 0->255*/
        0
    };

    il->element =
        vc_dispmanx_element_add(update,
                                display,
                                il->layer,
                                &(il->dstRect),
                                il->resource,
                                &(il->srcRect),
                                DISPMANX_PROTECTION_NONE,
                                &alpha,
                                NULL, // clamp
                                DISPMANX_NO_ROTATE);
    assert(il->element != 0);
}

//-------------------------------------------------------------------------

void
changeSourceImageLayer(
    IMAGE_LAYER_T *il,
    DISPMANX_UPDATE_HANDLE_T update)
{
    int result = vc_dispmanx_resource_write_data(il->resource,
                                                 il->image.type,
                                                 il->image.pitch,
                                                 il->image.buffer,
                                                 &(il->bmpRect));
    assert(result == 0);

    result = vc_dispmanx_element_change_source(update,
                                               il->element,
                                               il->resource);
    assert(result == 0);

}

//-------------------------------------------------------------------------

void
changeSourceAndUpdateImageLayer(
    IMAGE_LAYER_T *il)
{
    int result = vc_dispmanx_resource_write_data(il->resource,
                                                 il->image.type,
                                                 il->image.pitch,
                                                 il->image.buffer,
                                                 &(il->bmpRect));
    assert(result == 0);

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);

    result = vc_dispmanx_element_change_source(update,
                                               il->element,
                                               il->resource);
    assert(result == 0);

    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

}

//-------------------------------------------------------------------------

void
moveImageLayer(
    IMAGE_LAYER_T *il,
    int32_t xOffset,
    int32_t yOffset,
    DISPMANX_UPDATE_HANDLE_T update)
{
    vc_dispmanx_rect_set(&(il->dstRect),
                         xOffset,
                         yOffset,
                         il->image.width,
                         il->image.height);

    int result =
    vc_dispmanx_element_change_attributes(update,
                                          il->element,
                                          ELEMENT_CHANGE_DEST_RECT,
                                          0,
                                          255,
                                          &(il->dstRect),
                                          &(il->srcRect),
                                          0,
                                          DISPMANX_NO_ROTATE);
    assert(result == 0);
}

//-------------------------------------------------------------------------

void
destroyImageLayer(
    IMAGE_LAYER_T *il)
{
    int result = 0;

    DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
    assert(update != 0);
    result = vc_dispmanx_element_remove(update, il->element);
    assert(result == 0);
    result = vc_dispmanx_update_submit_sync(update);
    assert(result == 0);

    //---------------------------------------------------------------------

    result = vc_dispmanx_resource_delete(il->resource);
    assert(result == 0);

    //---------------------------------------------------------------------

    destroyImage(&(il->image));
}

