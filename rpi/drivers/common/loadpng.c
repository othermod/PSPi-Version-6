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

#include <png.h>
#include <stdlib.h>

#include "bcm_host.h"

#include "loadpng.h"

//-------------------------------------------------------------------------

#ifndef ALIGN_TO_16
#define ALIGN_TO_16(x) ((x + 15) & ~15)
#endif

//-------------------------------------------------------------------------

bool
loadPng(
    IMAGE_T* image,
    const char *path)
{
    FILE* file = fopen(path, "rb");

    if (file == NULL)
    {
        fprintf(stderr, "loadpng: can't open file for reading\n");
        return false;
    }

    bool result = loadPngFile(image, file);

    fclose(file);

    return result;
}

bool
loadPngFile(
    IMAGE_T* image,
    FILE *file)
{
    png_structp png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING,
                                                 NULL,
                                                 NULL,
                                                 NULL);

    if (png_ptr == NULL)
    {
        return false;
    }

    png_infop info_ptr = png_create_info_struct(png_ptr);

    if (info_ptr == NULL)
    {
        png_destroy_read_struct(&png_ptr, 0, 0);
        return false;
    }

    if (setjmp(png_jmpbuf(png_ptr)))
    {
        png_destroy_read_struct(&png_ptr, &info_ptr, 0);
        return false;
    }

    //---------------------------------------------------------------------

    png_init_io(png_ptr, file);

    png_read_info(png_ptr, info_ptr);

    //---------------------------------------------------------------------

    png_byte colour_type = png_get_color_type(png_ptr, info_ptr);
    png_byte bit_depth = png_get_bit_depth(png_ptr, info_ptr);

    VC_IMAGE_TYPE_T type = VC_IMAGE_RGB888;

    if (colour_type & PNG_COLOR_MASK_ALPHA)
    {
        type = VC_IMAGE_RGBA32;
    }

    initImage(image,
              type,
              png_get_image_width(png_ptr, info_ptr),
              png_get_image_height(png_ptr, info_ptr),
              false);

    //---------------------------------------------------------------------

    double gamma = 0.0;

    if (png_get_gAMA(png_ptr, info_ptr, &gamma))
    {
        png_set_gamma(png_ptr, 2.2, gamma);
    }

    //---------------------------------------------------------------------

    if (colour_type == PNG_COLOR_TYPE_PALETTE) 
    {
        png_set_palette_to_rgb(png_ptr);
    }

    if ((colour_type == PNG_COLOR_TYPE_GRAY) && (bit_depth < 8))
    {
        png_set_expand_gray_1_2_4_to_8(png_ptr);
    }

    if (png_get_valid(png_ptr, info_ptr, PNG_INFO_tRNS))
    {
        png_set_tRNS_to_alpha(png_ptr);
    }

    if (bit_depth == 16)
    {
#ifdef PNG_READ_SCALE_16_TO_8_SUPPORTED
        png_set_scale_16(png_ptr);
#else
        png_set_strip_16(png_ptr);
#endif
    }

    if (colour_type == PNG_COLOR_TYPE_GRAY ||
        colour_type == PNG_COLOR_TYPE_GRAY_ALPHA)
    {
        png_set_gray_to_rgb(png_ptr);
    }

    //---------------------------------------------------------------------

    png_read_update_info(png_ptr, info_ptr);

    //---------------------------------------------------------------------

    png_bytepp row_pointers = malloc(image->height * sizeof(png_bytep));

    png_uint_32 j = 0;
    for (j = 0 ; j < image->height ; ++j)
    {
        row_pointers[j] = image->buffer + (j * image->pitch);
    }

    //---------------------------------------------------------------------

    png_read_image(png_ptr, row_pointers);

    //---------------------------------------------------------------------

    free(row_pointers);

    png_destroy_read_struct(&png_ptr, &info_ptr, 0);

    return true;
}

