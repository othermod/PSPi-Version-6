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

#ifndef IMAGE_GRAPHICS_H
#define IMAGE_GRAPHICS_H

#include "image.h"

//-------------------------------------------------------------------------

void
imageBoxIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index);

void
imageBoxRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb);

void
imageBoxFilledIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index);

void
imageBoxFilledRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb);

void
imageLineIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index);

void
imageLineRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb);

void
imageHorizontalLineIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t x2,
    int32_t y,
    int8_t index);

void
imageHorizontalLineRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t x2,
    int32_t y,
    const RGBA8_T *rgb);

void
imageVerticalLineIndexed(
    IMAGE_T *image,
    int32_t x,
    int32_t y1,
    int32_t y2,
    int8_t index);

void
imageVerticalLineRGB(
    IMAGE_T *image,
    int32_t x,
    int32_t y1,
    int32_t y2,
    const RGBA8_T *rgb);

//-------------------------------------------------------------------------

#endif
