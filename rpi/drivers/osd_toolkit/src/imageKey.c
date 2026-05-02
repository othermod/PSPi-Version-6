//-------------------------------------------------------------------------
//
// The MIT License (MIT)
//
// Copyright (c) 2015 Andrew Duncan
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

#include <stdint.h>

#include "font.h"
#include "imageGraphics.h"
#include "imageKey.h"
#include "imageLayer.h"

//-------------------------------------------------------------------------

#define KEY_BORDER_WIDTH 1
#define KEY_LEFT_PADDING 5
#define KEY_RIGHT_PADDING 5
#define KEY_TOP_PADDING 1
#define KEY_BOTTOM_PADDING 1

//-------------------------------------------------------------------------

KEY_DIMENSIONS_T
drawKey(
    IMAGE_LAYER_T *imageLayer,
    int32_t x,
    int32_t y,
    const char *text,
    const char *description)
{
    static RGBA8_T textColour = { 0, 0, 0, 255 };
    static RGBA8_T borderColour = { 191, 191, 191, 255 };
    static RGBA8_T backgroundColour = { 255, 255, 255, 255 };

    size_t textLength = strlen(text);

    int32_t width = (FONT_WIDTH * textLength)
                  + (2 * KEY_BORDER_WIDTH)
                  + KEY_LEFT_PADDING
                  + KEY_RIGHT_PADDING;

    int32_t height = FONT_HEIGHT
                   + (2 * KEY_BORDER_WIDTH)
                   + KEY_TOP_PADDING
                   + KEY_BOTTOM_PADDING;

    IMAGE_T *image = &(imageLayer->image);

    imageBoxFilledRGB(image,
                      x,
                      y,
                      x + width,
                      y + height,
                      &backgroundColour);

    imageBoxRGB(image, x, y, x + width, y + height, &borderColour);

    drawStringRGB(x + KEY_BORDER_WIDTH + KEY_LEFT_PADDING,
                  y + KEY_BORDER_WIDTH + KEY_TOP_PADDING,
                  text,
                  &textColour,
                  image);

    drawStringRGB(x + width + KEY_RIGHT_PADDING,
                  y + KEY_BORDER_WIDTH + KEY_TOP_PADDING,
                  description,
                  &textColour,
                  image);

    KEY_DIMENSIONS_T dimensions = { width, height };

    return dimensions;
}

