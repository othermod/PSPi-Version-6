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

#ifndef IMAGE_PALETTE_H
#define IMAGE_PALETTE_H

//-------------------------------------------------------------------------

#include <stdbool.h>
#include <stdint.h>

#include "bcm_host.h"

#include "image.h"

//-------------------------------------------------------------------------

typedef struct 
{
    uint16_t *palette;
    int16_t length;
} IMAGE_PALETTE16_T;

typedef struct 
{
    uint32_t *palette;
    int16_t length;
} IMAGE_PALETTE32_T;

//-------------------------------------------------------------------------

bool
initImagePalette16(
    IMAGE_PALETTE16_T *palette,
    int16_t length);

bool
setPalette16EntryRgb(
    IMAGE_PALETTE16_T *palette,
    int16_t index,
    const RGBA8_T *rgb);

bool
getPalette16EntryRgb(
    IMAGE_PALETTE16_T *palette,
    int16_t index,
    RGBA8_T *rgb);

void
palette16EntryToRgb(
    uint16_t entry,
    RGBA8_T *rgb);

uint16_t
rgbToPalette16Entry(
    const RGBA8_T *rgb);

bool
setResourcePalette16(
    const IMAGE_PALETTE16_T *palette,
    int16_t offset,
    DISPMANX_RESOURCE_HANDLE_T resource,
    int16_t first,
    int16_t last);

void
destroyImagePalette16(
    IMAGE_PALETTE16_T *palette);

//-------------------------------------------------------------------------

bool
initImagePalette32(
    IMAGE_PALETTE32_T *palette,
    int16_t length);

bool
setPalette32EntryRgba(
    IMAGE_PALETTE32_T *palette,
    int16_t index,
    const RGBA8_T *rgba);

bool
getPalette32EntryRgba(
    IMAGE_PALETTE32_T *palette,
    int16_t index,
    RGBA8_T *rgba);

void
palette32EntryToRgba(
    uint32_t entry,
    RGBA8_T *rgba);

uint32_t
rgbaToPalette32Entry(
    const RGBA8_T *rgba);

bool
setResourcePalette32(
    const IMAGE_PALETTE32_T *palette,
    int16_t offset,
    DISPMANX_RESOURCE_HANDLE_T resource,
    int16_t first,
    int16_t last);

void
destroyImagePalette32(
    IMAGE_PALETTE32_T *palette);

//-------------------------------------------------------------------------

#endif
