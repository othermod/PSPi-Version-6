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
#include <string.h>

#include "image.h"

//-------------------------------------------------------------------------

#ifndef ALIGN_TO_16
#define ALIGN_TO_16(x)  ((x + 15) & ~15)
#endif

//-------------------------------------------------------------------------

void setPixel4BPP(IMAGE_T *image, int32_t x, int32_t y, int8_t index);
void setPixel8BPP(IMAGE_T *image, int32_t x, int32_t y, int8_t index);
void setPixelRGB565(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);
void setPixelDitheredRGB565(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);
void setPixelRGB888(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);
void setPixelRGBA16(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);
void setPixelDitheredRGBA16(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);
void setPixelRGBA32(IMAGE_T *image, int32_t x, int32_t y, const RGBA8_T *rgba);

void getPixel4BPP(IMAGE_T *image, int32_t x, int32_t y, int8_t *index);
void getPixel8BPP(IMAGE_T *image, int32_t x, int32_t y, int8_t *index);
void getPixelRGB565(IMAGE_T *image, int32_t x, int32_t y, RGBA8_T *rgba);
void getPixelRGB888(IMAGE_T *image, int32_t x, int32_t y, RGBA8_T *rgba);
void getPixelRGBA16(IMAGE_T *image, int32_t x, int32_t y, RGBA8_T *rgba);
void getPixelRGBA32(IMAGE_T *image, int32_t x, int32_t y, RGBA8_T *rgba);

//-------------------------------------------------------------------------

bool initImage(
    IMAGE_T *image,
    VC_IMAGE_TYPE_T type,
    int32_t width,
    int32_t height,
    bool dither)
{
    switch (type)
    {
    case VC_IMAGE_4BPP:

        image->bitsPerPixel = 4;
        image->setPixelDirect = NULL;
        image->getPixelDirect = NULL;
        image->setPixelIndexed = setPixel4BPP;
        image->getPixelIndexed = getPixel4BPP;

        break;

    case VC_IMAGE_8BPP:

        image->bitsPerPixel = 8;
        image->setPixelDirect = NULL;
        image->getPixelDirect = NULL;
        image->setPixelIndexed = setPixel8BPP;
        image->getPixelIndexed = getPixel8BPP;

        break;

    case VC_IMAGE_RGB565:

        image->bitsPerPixel = 16;

        if (dither)
        {
            image->setPixelDirect = setPixelDitheredRGB565;
        }
        else
        {
            image->setPixelDirect = setPixelRGB565;
        }
        image->getPixelDirect = getPixelRGB565;
        image->setPixelIndexed = NULL;
        image->getPixelIndexed = NULL;

        break;

    case VC_IMAGE_RGB888:

        image->bitsPerPixel = 24;
        image->setPixelDirect = setPixelRGB888;
        image->getPixelDirect = getPixelRGB888;
        image->setPixelIndexed = NULL;
        image->getPixelIndexed = NULL;

        break;

    case VC_IMAGE_RGBA16:

        image->bitsPerPixel = 16;
        if (dither)
        {
            image->setPixelDirect = setPixelDitheredRGBA16;
        }
        else
        {
            image->setPixelDirect = setPixelRGBA16;
        }
        image->getPixelDirect = getPixelRGBA16;
        image->setPixelIndexed = NULL;
        image->getPixelIndexed = NULL;

        break;

    case VC_IMAGE_RGBA32:

        image->bitsPerPixel = 32;
        image->setPixelDirect = setPixelRGBA32;
        image->getPixelDirect = getPixelRGBA32;
        image->setPixelIndexed = NULL;
        image->getPixelIndexed = NULL;

        break;

    default:

        fprintf(stderr, "image: unknown type (%d)\n", type);
        return false;

        break;
    }

    image->type = type;
    image->width = width;
    image->height = height;
    image->pitch = (ALIGN_TO_16(width) * image->bitsPerPixel) / 8;
    image->alignedHeight = ALIGN_TO_16(height);
    image->size = image->pitch * image->alignedHeight;

    image->buffer = calloc(1, image->size);

    if (image->buffer == NULL)
    {
        fprintf(stderr, "image: memory exhausted\n");
        exit(EXIT_FAILURE);
    }

    return true;
}

//-------------------------------------------------------------------------

void
clearImageIndexed(
    IMAGE_T *image,
    int8_t index)
{
    if (image->setPixelIndexed != NULL)
    {
        int j;
        for (j = 0 ; j < image->height ; j++)
        {
            int i;
            for (i = 0 ; i < image->width ; i++)
            {
                image->setPixelIndexed(image, i, j, index);
            }
        }
    }
}

//-------------------------------------------------------------------------

void
clearImageRGB(
    IMAGE_T *image,
    const RGBA8_T *rgb)
{
    if (image->setPixelDirect != NULL)
    {
        int j;
        for (j = 0 ; j < image->height ; j++)
        {
            int i;
            for (i = 0 ; i < image->width ; i++)
            {
                image->setPixelDirect(image, i, j, rgb);
            }
        }
    }
}

//-------------------------------------------------------------------------

bool
setPixelIndexed(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t index)
{
    bool result = false;

    if ((image->setPixelIndexed != NULL) &&
        (x >= 0) && (x < image->width) &&
        (y >= 0) && (y < image->height))
    {
        result = true;
        image->setPixelIndexed(image, x, y, index);
    }

    return result;
}

//-------------------------------------------------------------------------

bool
setPixelRGB(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgb)
{
    bool result = false;

    if ((image->setPixelDirect != NULL) &&
        (x >= 0) && (x < image->width) &&
        (y >= 0) && (y < image->height))
    {
        result = true;
        image->setPixelDirect(image, x, y, rgb);
    }

    return result;
}

//-------------------------------------------------------------------------

bool
getPixelIndexed(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t *index)
{
    bool result = false;

    if ((image->getPixelIndexed != NULL) && 
        (x >= 0) && (x < image->width) &&
        (y >= 0) && (y < image->height))
    {
        result = true;
        image->getPixelIndexed(image, x, y, index);
    }

    return result;
}

//-------------------------------------------------------------------------

bool
getPixelRGB(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    RGBA8_T *rgb)
{
    bool result = false;

    if ((image->getPixelDirect != NULL) &&
        (x >= 0) && (x < image->width) &&
        (y >= 0) && (y < image->height))
    {
        result = true;
        image->getPixelDirect(image, x, y, rgb);
    }

    return result;
}

//-------------------------------------------------------------------------

void
destroyImage(
    IMAGE_T *image)
{
    if (image->buffer)
    {
        free(image->buffer);
    }

    image->type = VC_IMAGE_MIN;
    image->width = 0;
    image->height = 0;
    image->pitch = 0;
    image->alignedHeight = 0;
    image->bitsPerPixel = 0;
    image->size = 0;
    image->buffer = NULL;
    image->setPixelDirect = NULL;
    image->getPixelDirect = NULL;
    image->setPixelIndexed = NULL;
    image->getPixelIndexed = NULL;
}

//-----------------------------------------------------------------------

void
setPixel4BPP(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t index)
{
    index &= 0x0F;

    uint8_t *value = (uint8_t*)(image->buffer + (x/2) + (y *image->pitch));

    if (x % 2)
    {
        *value = (*value & 0xF0) | (index);
    }
    else
    {
        *value = (*value & 0x0F) | (index << 4);
    }
}

//-----------------------------------------------------------------------

void
setPixel8BPP(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t index)
{
    *(uint8_t*)(image->buffer + x + (y * image->pitch)) = index;
}

//-----------------------------------------------------------------------

void
setPixelRGB565(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    uint8_t r5 = rgba->red >> 3;
    uint8_t g6 = rgba->green >> 2;
    uint8_t b5 = rgba->blue >> 3;

    uint16_t pixel = (r5 << 11) | (g6 << 5) | b5;
    *(uint16_t*)(image->buffer + (x * 2) + (y *image->pitch)) = pixel;
}

//-----------------------------------------------------------------------

void
setPixelDitheredRGB565(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    static int16_t dither8[64] =
    {
        1, 6, 2, 7, 1, 6, 2, 7,
        4, 2, 5, 4, 4, 3, 6, 4,
        1, 7, 1, 6, 2, 7, 1, 7,
        5, 3, 5, 3, 5, 4, 5, 3,
        1, 6, 2, 7, 1, 6, 2, 7,
        4, 3, 6, 4, 4, 2, 6, 4,
        2, 7, 1, 7, 2, 7, 1, 6,
        5, 3, 5, 3, 5, 3, 5, 3,
    };

    static int16_t dither4[64] =
    {
        1, 3, 1, 3, 1, 3, 1, 3,
        2, 1, 3, 2, 2, 1, 3, 2,
        1, 3, 1, 3, 1, 3, 1, 3,
        2, 2, 2, 1, 3, 2, 2, 2,
        1, 3, 1, 3, 1, 3, 1, 3,
        2, 1, 3, 2, 2, 1, 3, 2,
        1, 3, 1, 3, 1, 3, 1, 3,
        3, 2, 2, 2, 2, 2, 2, 2,
    };

    int32_t index = (x & 7) | ((y & 7) << 3);

    int16_t r = rgba->red + dither8[index];

    if (r > 255)
    {
        r = 255;
    }

    int16_t g = rgba->green + dither4[index];

    if (g > 255)
    {
        g = 255;
    }

    int16_t b = rgba->blue + dither8[index];

    if (b > 255)
    {
        b = 255;
    }

    RGBA8_T dithered = { r, g, b, rgba->alpha };

    setPixelRGB565(image, x, y, &dithered);
}

//-------------------------------------------------------------------------

void
setPixelRGB888(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    uint8_t *line = (uint8_t *)(image->buffer) + (y*image->pitch) + (3*x);
    line[0] = rgba->red;
    line[1] = rgba->green;
    line[2] = rgba->blue;
}

//-----------------------------------------------------------------------

void
setPixelRGBA16(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    uint8_t r4 = rgba->red  >> 4;
    uint8_t g4 = rgba->green >> 4;
    uint8_t b4 = rgba->blue >> 4;
    uint8_t a4 = rgba->alpha >> 4;

    uint16_t pixel = (r4 << 12) | (g4 << 8) | (b4 << 4) | a4;
    *(uint16_t*)(image->buffer + (x * 2) + (y *image->pitch)) = pixel;
}

//-----------------------------------------------------------------------

void
setPixelDitheredRGBA16(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    static int16_t dither16[64] =
    {
         1,  12,   4,  15,   1,  13,   4,  15,
         8,   4,  11,   7,   9,   5,  12,   8,
         3,  14,   2,  13,   3,  15,   2,  14,
        10,   6,   9,   5,  11,   7,  10,   6,
         1,  12,   4,  15,   1,  12,   4,  15,
         9,   5,  12,   8,   8,   5,  11,   8,
         3,  14,   2,  13,   3,  14,   2,  13,
        11,   7,  10,   6,  10,   7,   9,   6,
    };

    int32_t index = (x & 7) | ((y & 7) << 3);

    int16_t r = rgba->red + dither16[index];

    if (r > 255)
    {
        r = 255;
    }

    int16_t g = rgba->green + dither16[index];

    if (g > 255)
    {
        g = 255;
    }

    int16_t b = rgba->blue + dither16[index];

    if (b > 255)
    {
        b = 255;
    }

    int16_t a = rgba->alpha + dither16[index];

    if (b > 255)
    {
        b = 255;
    }

    RGBA8_T dithered = { r, g, b, a };

    setPixelRGBA16(image, x, y, &dithered);
}

//-----------------------------------------------------------------------

void
setPixelRGBA32(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    const RGBA8_T *rgba)
{
    uint8_t *line = (uint8_t *)(image->buffer) + (y*image->pitch) + (4*x);

    line[0] = rgba->red;
    line[1] = rgba->green;
    line[2] = rgba->blue;
    line[3] = rgba->alpha;
}

//-----------------------------------------------------------------------

void
getPixel4BPP(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t *index)
{
    uint8_t *value = (uint8_t*)(image->buffer + (x/2) + (y *image->pitch));

    if (x % 2)
    {
        *index = (*value) & 0x0F;
    }
    else
    {
        *index = (*value) >> 4;
    }
}

//-----------------------------------------------------------------------

void
getPixel8BPP(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    int8_t *index)
{
    *index = *(uint8_t*)(image->buffer + x + (y * image->pitch));
}

//-----------------------------------------------------------------------

void
getPixelRGB565(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    RGBA8_T *rgba)
{
    uint16_t pixel = *(uint16_t*)(image->buffer + (x * 2) + (y * image->pitch));

    uint8_t r5 = (pixel >> 11) & 0x1F;
    uint8_t g6 = (pixel >> 5) & 0x3F;
    uint8_t b5 = pixel & 0x1F;

    rgba->red = (r5 << 3) | (r5 >> 2);
    rgba->green = (g6 << 2) | (g6 >> 4);
    rgba->blue = (b5 << 3) | (b5 >> 2);
    rgba->alpha = 255;
}

//-------------------------------------------------------------------------

void
getPixelRGB888(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    RGBA8_T *rgba)
{
    uint8_t *line = (uint8_t *)(image->buffer) + (y*image->pitch) + (3*x);
    rgba->red = line[0];
    rgba->green = line[1];
    rgba->blue = line[2];
    rgba->alpha = 255;
}

//-----------------------------------------------------------------------

void
getPixelRGBA16(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    RGBA8_T *rgba)
{
    uint16_t pixel = *(uint16_t*)(image->buffer+(x*2)+(y*image->pitch));
    uint8_t r4 = (pixel >> 12) & 0xF;
    uint8_t g4 = (pixel >> 8) & 0xF;
    uint8_t b4 = (pixel >> 4) & 0xF;
    uint8_t a4 = (pixel & 0xF);

    rgba->red = (r4 << 4) | r4;
    rgba->green = (g4 << 4) | g4;
    rgba->blue = (b4 << 4) | b4;
    rgba->alpha = (a4 << 4) | a4;
}

//-----------------------------------------------------------------------

void
getPixelRGBA32(
    IMAGE_T *image,
    int32_t x,
    int32_t y,
    RGBA8_T *rgba)
{
    uint8_t *line = (uint8_t *)(image->buffer) + (y*image->pitch) + (4*x);

    rgba->red = line[0];
    rgba->green = line[1];
    rgba->blue = line[2];
    rgba->alpha = line[3];
}

//-----------------------------------------------------------------------

#define IMAGE_INFO_ENTRY(t, ha, ii) \
    { .name=(#t), \
      .type=(VC_IMAGE_ ## t), \
      .hasAlpha=(ha), \
      .isIndexed=(ii) }

IMAGE_TYPE_INFO_T imageTypeInfo[] =
{
    IMAGE_INFO_ENTRY(4BPP, false, true),
    IMAGE_INFO_ENTRY(8BPP, false, true),
    IMAGE_INFO_ENTRY(RGB565, false, false),
    IMAGE_INFO_ENTRY(RGB888, false, false),
    IMAGE_INFO_ENTRY(RGBA16, true, false),
    IMAGE_INFO_ENTRY(RGBA32, true, false)
};

static size_t imageTypeInfoEntries = sizeof(imageTypeInfo)/
                                     sizeof(imageTypeInfo[0]);

//-----------------------------------------------------------------------

bool
findImageType(
    IMAGE_TYPE_INFO_T *typeInfo,
    const char *name,
    IMAGE_TYPE_SELECTOR_T selector)
{
    IMAGE_TYPE_INFO_T *entry = NULL;
    bool found = false;

    size_t i = 0;
    for (i = 0 ; i < imageTypeInfoEntries ; i++)
    {
        if (strcasecmp(name, imageTypeInfo[i].name) == 0)
        {
            entry = &(imageTypeInfo[i]);
            break;
        }
    }

    if (entry != NULL)
    {
        bool matchedAlpha = false;
        bool matchedColour = false;

        if ((selector & IMAGE_TYPES_WITH_ALPHA) &&
            (entry->hasAlpha == true))
        {
            matchedAlpha = true;
        }
        else if ((selector & IMAGE_TYPES_WITHOUT_ALPHA) &&
                 (entry->hasAlpha == false))
        {
            matchedAlpha = true;
        }

        if ((selector & IMAGE_TYPES_DIRECT_COLOUR) &&
                 (entry->isIndexed == false))
        {
            matchedColour = true;
        }
        else if ((selector & IMAGE_TYPES_INDEXED_COLOUR) &&
                 (entry->isIndexed == true))
        {
            matchedColour = true;
        }

        if (matchedAlpha && matchedColour)
        {
            found = true;
            memcpy(typeInfo, entry, sizeof(IMAGE_TYPE_INFO_T));
        }
    }

    return found;
}

//-----------------------------------------------------------------------

void
printImageTypes(
    FILE *fp,
    const char *before,
    const char *after,
    IMAGE_TYPE_SELECTOR_T selector)
{
    IMAGE_TYPE_INFO_T *entry = NULL;

    size_t i = 0;
    for (i = 0 ; i < imageTypeInfoEntries ; i++)
    {
        entry = &(imageTypeInfo[i]);
        bool matchedAlpha = false;
        bool matchedColour = false;

        if ((selector & IMAGE_TYPES_WITH_ALPHA) &&
            (entry->hasAlpha == true))
        {
            matchedAlpha = true;
        }
        else if ((selector & IMAGE_TYPES_WITHOUT_ALPHA) &&
                 (entry->hasAlpha == false))
        {
            matchedAlpha = true;
        }

        if ((selector & IMAGE_TYPES_DIRECT_COLOUR) &&
                 (entry->isIndexed == false))
        {
            matchedColour = true;
        }
        else if ((selector & IMAGE_TYPES_INDEXED_COLOUR) &&
                 (entry->isIndexed == true))
        {
            matchedColour = true;
        }

        if (matchedAlpha && matchedColour)
        {
            fprintf(fp, "%s%s%s", before, entry->name, after);
        }
    }
}

