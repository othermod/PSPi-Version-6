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

#ifndef BACKGROUND_LAYER_H
#define BACKGROUND_LAYER_H

//-------------------------------------------------------------------------

#include "bcm_host.h"

//-------------------------------------------------------------------------

typedef struct
{
    int32_t layer;
    DISPMANX_RESOURCE_HANDLE_T resource;
    DISPMANX_ELEMENT_HANDLE_T element;
} BACKGROUND_LAYER_T;

//-------------------------------------------------------------------------

void
initBackgroundLayer(
    BACKGROUND_LAYER_T *bg,
    uint16_t colour,
    int32_t layer);

void
addElementBackgroundLayer(
    BACKGROUND_LAYER_T *bg,
    DISPMANX_DISPLAY_HANDLE_T display,
    DISPMANX_UPDATE_HANDLE_T update);

void destroyBackgroundLayer(BACKGROUND_LAYER_T *bg);


//-------------------------------------------------------------------------

#endif

