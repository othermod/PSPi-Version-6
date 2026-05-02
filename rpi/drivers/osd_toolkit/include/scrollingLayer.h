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

#ifndef SCROLLING_LAYER_H
#define SCROLLING_LAYER_H

#include <stdbool.h>

#include "image.h"

#include "bcm_host.h"

//-------------------------------------------------------------------------

typedef struct
{
    IMAGE_T image;
    int32_t viewWidth;
    int32_t viewHeight;
    int32_t xOffsetMax;
    int32_t xOffset;
    int32_t yOffsetMax;
    int32_t yOffset;
    int16_t direction;
    int16_t directionMax;
    int32_t xDirections[8];
    int32_t yDirections[8];
    VC_RECT_T bmpRect;
    VC_RECT_T srcRect;
    VC_RECT_T dstRect;
    int32_t layer;
    DISPMANX_RESOURCE_HANDLE_T frontResource;
    DISPMANX_RESOURCE_HANDLE_T backResource;
    DISPMANX_ELEMENT_HANDLE_T element;
} SCROLLING_LAYER_T;

//-------------------------------------------------------------------------

void
initScrollingLayer(SCROLLING_LAYER_T *sl,
    const char* file,
    int32_t layer);

void
addElementScrollingLayerCentered(
    SCROLLING_LAYER_T *sl,
    DISPMANX_MODEINFO_T *info,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void
addElementScrollingLayer(
    SCROLLING_LAYER_T *sl,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void setDirectionScrollingLayer(SCROLLING_LAYER_T *sl, char c);

void
updatePositionScrollingLayer(
    SCROLLING_LAYER_T *sl,
    DISPMANX_UPDATE_HANDLE_T update);

void destroyScrollingLayer(SCROLLING_LAYER_T *sl);

bool
loadScrollingLayerPng(
    IMAGE_T* image,
    const char *file,
    bool extendX,
    bool extendY);

//-------------------------------------------------------------------------

#endif
