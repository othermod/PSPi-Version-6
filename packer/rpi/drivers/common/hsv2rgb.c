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

#include "hsv2rgb.h"
#include "image.h"

//-------------------------------------------------------------------------

void
hsv2rgb(
    int16_t hue,
    int16_t saturation,
    int16_t value,
    RGBA8_T *rgb)
{
    //---------------------------------------------------------------------
    // convert hue, saturation and value (HSV) to red, green and blue.
    //
    // hue = 0 to 3600 (i.e. 1/10 of a degree).
    // saturation = 0 to 1000
    // value = 0 to 1000
    //---------------------------------------------------------------------

    rgb->red = 0;
    rgb->green = 0;
    rgb->blue = 0;

    if (saturation == 0)
    {
        rgb->red = (uint8_t)((255 * value) / 1000);
        rgb->green = rgb->red;
        rgb->blue = rgb->red;
    }
    else
    {
        int16_t h = hue/600;
        int16_t f = ((hue%600)*1000)/600;
        int16_t p = (value*(1000-saturation))/1000;
        int16_t q = (value*(1000-((saturation*f)/1000)))/1000;
        int16_t t = (value*(1000-((saturation*(1000-f))/1000)))/1000;

        switch (h)
        {
        case 0:

            rgb->red = (uint8_t)((255 * value) / 1000);
            rgb->green = (uint8_t)((255 * t) / 1000);
            rgb->blue = (uint8_t)((255 * p) / 1000);
            break;

        case 1:

            rgb->red = (uint8_t)((255 * q) / 1000);
            rgb->green = (uint8_t)((255 * value) / 1000);
            rgb->blue = (uint8_t)((255 * p) / 1000);
            break;

        case 2:

            rgb->red = (uint8_t)((255 * p) / 1000);
            rgb->green = (uint8_t)((255 * value) / 1000);
            rgb->blue = (uint8_t)((255 * t) / 1000);
            break;

        case 3:

            rgb->red = (uint8_t)((255 * p) / 1000);
            rgb->green = (uint8_t)((255 * q) / 1000);
            rgb->blue = (uint8_t)((255 * value) / 1000);
            break;

        case 4:

            rgb->red = (uint8_t)((255 * t) / 1000);
            rgb->green = (uint8_t)((255 * p) / 1000);
            rgb->blue = (uint8_t)((255 * value) / 1000);
            break;

        case 5:

            rgb->red = (uint8_t)((255 * value) / 1000);
            rgb->green = (uint8_t)((255 * p) / 1000);
            rgb->blue = (uint8_t)((255 * q) / 1000);
            break;

        }
    }
}

