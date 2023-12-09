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

#include <stdio.h>
#include <stdlib.h>

#include "imagePalette.h"

//-------------------------------------------------------------------------

#ifndef ALIGN_TO_16
#define ALIGN_TO_16(x)  ((x + 15) & ~15)
#endif

//-------------------------------------------------------------------------

bool
initImagePalette16(
    IMAGE_PALETTE16_T *palette,
    int16_t length)
{
    palette->palette = calloc(1, length * sizeof(uint16_t));
    palette->length = length;

    if (palette->palette == NULL)
    {
        fprintf(stderr, "imagePalette16: memory exhausted\n");
        exit(EXIT_FAILURE);
    }

    return true;
}

//-------------------------------------------------------------------------

bool
setPalette16EntryRgb(
    IMAGE_PALETTE16_T *palette,
    int16_t index,
    const RGBA8_T *rgb)
{
    bool result = false;

    if ((index >= 0) && (index < palette->length))
    {
        palette->palette[index] = rgbToPalette16Entry(rgb);
        result = true;
    }

    return result;
}

//-------------------------------------------------------------------------

bool
getPalette16EntryRgb(
    IMAGE_PALETTE16_T *palette,
    int16_t index,
    RGBA8_T *rgb)
{
    bool result = false;

    if ((index >= 0) && (index < palette->length))
    {
        palette16EntryToRgb(palette->palette[index], rgb);
        result = true;
    }

    return result;
}

//-------------------------------------------------------------------------

void
palette16EntryToRgb(
    uint16_t entry,
    RGBA8_T *rgb)
{
    uint8_t r5 = (entry >> 11) & 0x1F;
    uint8_t g6 = (entry >> 5) & 0x3F;
    uint8_t b5 = entry & 0x1F;

    rgb->red = (r5 << 3) | (r5 >> 2);
    rgb->green = (g6 << 2) | (g6 >> 4);
    rgb->blue = (b5 << 3) | (b5 >> 2);
    rgb->alpha = 255;
}

//-------------------------------------------------------------------------

uint16_t
rgbToPalette16Entry(
    const RGBA8_T *rgb)
{
    return ((rgb->red>>3)<<11) | ((rgb->green>>2)<<5) | (rgb->blue>>3);
}

//-------------------------------------------------------------------------

bool
setResourcePalette16(
    const IMAGE_PALETTE16_T *palette,
    int16_t offset,
    DISPMANX_RESOURCE_HANDLE_T resource,
    int16_t first,
    int16_t last)
{
    bool result = false;

    if ((first >= 0) && (last + offset < palette->length))
    {
        int status =
            vc_dispmanx_resource_set_palette(resource,
                                             &(palette->palette[offset]),
                                             first * sizeof(uint16_t),
                                             last * sizeof(uint16_t));
        result = (status == 0);
    }

    return result;
}

//-------------------------------------------------------------------------

void
destroyImagePalette16(
    IMAGE_PALETTE16_T *palette)
{
    if (palette->palette != NULL)
    {
        free(palette->palette);
        palette->palette = NULL;
    }

    palette->length = 0;
}

//-------------------------------------------------------------------------

bool
initImagePalette32(
    IMAGE_PALETTE32_T *palette,
    int16_t length)
{
    palette->palette = calloc(1, length * sizeof(uint32_t));
    palette->length = length;

    if (palette->palette == NULL)
    {
        fprintf(stderr, "imagePalette32: memory exhausted\n");
        exit(EXIT_FAILURE);
    }

    return true;
}

//-------------------------------------------------------------------------

bool
setPalette32EntryRgba(
    IMAGE_PALETTE32_T *palette,
    int16_t index,
    const RGBA8_T *rgba)
{
    bool result = false;

    if ((index >= 0) && (index < palette->length))
    {
        palette->palette[index] = rgbaToPalette32Entry(rgba);
        result = true;
    }

    return result;
}

//-------------------------------------------------------------------------

bool
getPalette32EntryRgba(
    IMAGE_PALETTE32_T *palette,
    int16_t index,
    RGBA8_T *rgba)
{
    bool result = false;

    if ((index >= 0) && (index < palette->length))
    {
        palette32EntryToRgba(palette->palette[index], rgba);
        result = true;
    }

    return result;
}

//-------------------------------------------------------------------------

void
palette32EntryToRgba(
    uint32_t entry,
    RGBA8_T *rgba)
{
    rgba->alpha = (entry >> 24) & 0xFF;
    rgba->red = (entry >> 16) & 0xFF;
    rgba->green = (entry >> 8) & 0xFF;
    rgba->blue = entry & 0xFF;
}

//-------------------------------------------------------------------------

uint32_t
rgbaToPalette32Entry(
    const RGBA8_T *rgba)
{
    return (rgba->alpha << 24) |
           (rgba->red << 16) |
           (rgba->green << 8) |
           rgba->blue;
}

//-------------------------------------------------------------------------

bool
setResourcePalette32(
    const IMAGE_PALETTE32_T *palette,
    int16_t offset,
    DISPMANX_RESOURCE_HANDLE_T resource,
    int16_t first,
    int16_t last)
{
    bool result = false;

    if ((first >= 0) && (last + offset < palette->length))
    {
        int status =
            vc_dispmanx_resource_set_palette(resource,
                                             &(palette->palette[offset]),
                                             first * sizeof(uint32_t),
                                             last * sizeof(uint32_t));
        result = (status == 0);
    }

    return result;
}

//-------------------------------------------------------------------------

void
destroyImagePalette32(
    IMAGE_PALETTE32_T *palette)
{
    if (palette->palette != NULL)
    {
        free(palette->palette);
        palette->palette = NULL;
    }

    palette->length = 0;
}

//-------------------------------------------------------------------------
