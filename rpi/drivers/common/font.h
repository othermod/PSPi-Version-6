
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

#ifndef FONT_H
#define FONT_H

//-------------------------------------------------------------------------

#include "image.h"

//-------------------------------------------------------------------------

#define FONT_WIDTH 8
#define FONT_HEIGHT 16

//-------------------------------------------------------------------------

void
drawCharIndexed(
    int x,
    int y,
    uint8_t c,
    int8_t index,
    IMAGE_T *image);

void
drawCharRGB(
    int x,
    int y,
    uint8_t c,
    const RGBA8_T *rgb,
    IMAGE_T *image);

void
drawStringIndexed(
    int x,
    int y,
    const char *string,
    int8_t index,
    IMAGE_T *image);

void
drawStringRGB(
    int x,
    int y,
    const char *string,
    const RGBA8_T *rgb,
    IMAGE_T *image);

//-------------------------------------------------------------------------

#endif
