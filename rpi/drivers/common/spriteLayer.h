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

#ifndef SPRITE_LAYER_H
#define SPRITE_LAYER_H

#include "image.h"

#include "bcm_host.h"

//-------------------------------------------------------------------------

typedef struct
{
    IMAGE_T image;
    int width;
    int height;
    int columns;
    int rows;
    int xOffsetMax;
    int xOffset;
    int yOffsetMax;
    int yOffset;
    VC_RECT_T bmpRect;
    VC_RECT_T srcRect;
    VC_RECT_T dstRect;
    int32_t layer;
    DISPMANX_RESOURCE_HANDLE_T frontResource;
    DISPMANX_RESOURCE_HANDLE_T backResource;
    DISPMANX_ELEMENT_HANDLE_T element;
} SPRITE_LAYER_T;

//-------------------------------------------------------------------------

void
initSpriteLayer(
    SPRITE_LAYER_T *s,
    int columns,
    int rows,
    const char *file,
    int32_t layer);

void
addElementSpriteLayerOffset(
    SPRITE_LAYER_T *s,
    int32_t xOffset,
    int32_t yOffset,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void
addElementSpriteLayerCentered(
    SPRITE_LAYER_T *s,
    DISPMANX_MODEINFO_T *info,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void
addElementSpriteLayer(
    SPRITE_LAYER_T *s,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void
updatePositionSpriteLayer(
    SPRITE_LAYER_T *s,
    DISPMANX_UPDATE_HANDLE_T update);

void destroySpriteLayer(SPRITE_LAYER_T *s);

//-------------------------------------------------------------------------

#endif
