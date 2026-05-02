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

#define _GNU_SOURCE

#include <png.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "image.h"

//-----------------------------------------------------------------------

bool
pngWriteImageRGB565(
    const IMAGE_T *image,
    png_structp pngPtr,
    png_infop infoPtr)
{
    int32_t rowLength = 3 * image->width;
    uint8_t *imageRow = malloc(rowLength);

    if (imageRow == NULL)
    {
        fprintf(stderr, "savepng: unable to allocated row buffer\n");
        return false;
    }

    int32_t y = 0;
    for (y = 0; y < image->height; y++)
    {
        int32_t x = 0;
        for (x = 0; x < image->width; x++)
        {
            uint16_t pixels = *(uint16_t*)(image->buffer +
                                          (y * image->pitch) +
                                          ((x * image->bitsPerPixel) / 8));
            int32_t index = x * 3;

            uint8_t r5 = (pixels >> 11) & 0x1F;
            uint8_t g6 = (pixels >> 5) & 0x3F;
            uint8_t b5 = (pixels) & 0x1F;

            imageRow[index] =  (r5 << 3) | (r5 >> 2);
            imageRow[index + 1] =  (g6 << 2) | (g6 >> 4);
            imageRow[index + 2] =  (b5 << 3) | (b5 >> 2);
        }
        png_write_row(pngPtr, imageRow);

    }

    free(imageRow);

    return true;
}

//-----------------------------------------------------------------------

bool
pngWriteImageRGB888(
    const IMAGE_T *image,
    png_structp pngPtr,
    png_infop infoPtr)
{
    int32_t y = 0;
    for (y = 0; y < image->height; y++)
    {
        png_write_row(pngPtr, image->buffer + (image->pitch * y));
    }

    return true;
}

//-----------------------------------------------------------------------

bool
pngWriteImageRGBA16(
    const IMAGE_T *image,
    png_structp pngPtr,
    png_infop infoPtr)
{
    int32_t rowLength = 4 * image->width;
    uint8_t *imageRow = malloc(rowLength);

    if (imageRow == NULL)
    {
        fprintf(stderr, "savepng: unable to allocated row buffer\n");
        return false;
    }

    int32_t y = 0;
    for (y = 0; y < image->height; y++)
    {
        int32_t x = 0;
        for (x = 0; x < image->width; x++)
        {
            uint16_t pixels = *(uint16_t*)(image->buffer +
                                           (y * image->pitch) +
                                           ((x * image->bitsPerPixel) / 8));
            int32_t index = x * 4;

            uint8_t r4 = (pixels >> 12) & 0xF;
            uint8_t g4 = (pixels >> 8) & 0xF;
            uint8_t b4 = (pixels >> 4) & 0xF;
            uint8_t a4 = pixels & 0xF;

            imageRow[index] = (r4 << 4) | r4;
            imageRow[index + 1] = (g4 << 4) | g4;
            imageRow[index + 2] = (b4 << 4) | b4;
            imageRow[index + 3] = (a4 << 4) | a4;
        }
        png_write_row(pngPtr, imageRow);

    }

    free(imageRow);

    return true;
}

//-----------------------------------------------------------------------

bool
pngWriteImageRGBA32(
    const IMAGE_T *image,
    png_structp pngPtr,
    png_infop infoPtr)
{
    int32_t y = 0;
    for (y = 0; y < image->height; y++)
    {
        png_write_row(pngPtr, image->buffer + (image->pitch * y));
    }

    return true;
}

//-----------------------------------------------------------------------

bool savePng(const IMAGE_T* image, const char *file)
{
    png_structp pngPtr = png_create_write_struct(PNG_LIBPNG_VER_STRING,
                                                 NULL,
                                                 NULL,
                                                 NULL);

    if (pngPtr == NULL)
    {
        fprintf(stderr,
                "savepng: unable to allocated PNG write structure\n");

        return false;
    }

    png_infop infoPtr = png_create_info_struct(pngPtr);

    if (infoPtr == NULL)
    {
        fprintf(stderr,
                "savepng: unable to allocated PNG info structure\n");

        return false;
    }

    if (setjmp(png_jmpbuf(pngPtr)))
    {
        fprintf(stderr, "savepng: unable to create PNG\n");
        return false;
    }

    FILE *pngfp = fopen(file, "wb");

    if (pngfp == NULL)
    {
        fprintf(stderr,
                "savepng: unable to create %s - %s\n",
                file,
                strerror(errno));

        exit(EXIT_FAILURE);
    }

    png_init_io(pngPtr, pngfp);

    int png_color_type = PNG_COLOR_TYPE_RGB;

    if ((image->type == VC_IMAGE_RGBA16) ||
        (image->type == VC_IMAGE_RGBA32))
    {
        png_color_type = PNG_COLOR_TYPE_RGBA;
    }

    png_set_IHDR(
        pngPtr,
        infoPtr,
        image->width,
        image->height,
        8,
        png_color_type,
        PNG_INTERLACE_NONE,
        PNG_COMPRESSION_TYPE_BASE,
        PNG_FILTER_TYPE_BASE);

    png_write_info(pngPtr, infoPtr);

    bool result = false;

    switch(image->type)
    {
    case VC_IMAGE_RGB565:

        result = pngWriteImageRGB565(image, pngPtr, infoPtr);
        break;

    case VC_IMAGE_RGB888:

        result = pngWriteImageRGB888(image, pngPtr, infoPtr);
        break;

    case VC_IMAGE_RGBA16:

        result = pngWriteImageRGBA16(image, pngPtr, infoPtr);
        break;

    case VC_IMAGE_RGBA32:

        result = pngWriteImageRGBA32(image, pngPtr, infoPtr);
        break;

    default:

        break;
    }

    png_write_end(pngPtr, NULL);
    png_destroy_write_struct(&pngPtr, &infoPtr);
    fclose(pngfp);

    return result;
}
