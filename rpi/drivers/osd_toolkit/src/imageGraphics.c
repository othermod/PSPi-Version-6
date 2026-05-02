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

#include <stdlib.h>

#include "image.h"
#include "imageGraphics.h"

//-------------------------------------------------------------------------

void
imageBoxIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index)
{
    imageVerticalLineIndexed(image, x1, y1, y2, index);
    imageHorizontalLineIndexed(image, x1, x2, y1, index);
    imageVerticalLineIndexed(image, x2, y1, y2, index);
    imageHorizontalLineIndexed(image, x1, x2, y2, index);
}

//-------------------------------------------------------------------------

void
imageBoxRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb)
{
    imageVerticalLineRGB(image, x1, y1, y2, rgb);
    imageHorizontalLineRGB(image, x1, x2, y1, rgb);
    imageVerticalLineRGB(image, x2, y1, y2, rgb);
    imageHorizontalLineRGB(image, x1, x2, y2, rgb);
}

//-------------------------------------------------------------------------

void
imageBoxFilledIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index)
{
    int32_t sign_y = (y1 <= y2) ? 1 : -1;
    int32_t y = y1;

    imageHorizontalLineIndexed(image, x1, x2, y, index);

    while (y != y2)
    {
        y += sign_y;
        imageHorizontalLineIndexed(image, x1, x2, y, index);
    }
}

//-------------------------------------------------------------------------

void
imageBoxFilledRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb)
{
    int32_t sign_y = (y1 <= y2) ? 1 : -1;
    int32_t y = y1;

    imageHorizontalLineRGB(image, x1, x2, y, rgb);

    while (y != y2)
    {
        y += sign_y;
        imageHorizontalLineRGB(image, x1, x2, y, rgb);
    }
}

//-------------------------------------------------------------------------

void
imageLineIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    int8_t index)
{
    if (y1 == y2)
    {
        imageHorizontalLineIndexed(image, x1, x2, y1, index);
    }
    else if (x1 == x2)
    {
        imageVerticalLineIndexed(image, x1, y1, y2, index);
    }
    else
    {
        int32_t dx = abs(x2 - x1);
        int32_t dy = abs(y2 - y1);

        int32_t sign_x = (x1 <= x2) ? 1 : -1;
        int32_t sign_y = (y1 <= y2) ? 1 : -1;

        int32_t x = x1;
        int32_t y = y1;

        setPixelIndexed(image, x, y, index);

        if (dx > dy)
        {
            int32_t d = 2 * dy - dx;
            int32_t incrE = 2 * dy;
            int32_t incrNE = 2 * (dy - dx);

            while (x != x2)
            {
                x += sign_x;

                if (d <= 0)
                {
                    d += incrE;
                }
                else
                {
                    d += incrNE;
                    y += sign_y;
                }

                setPixelIndexed(image, x, y, index);
            }
        }
        else
        {
            int32_t d = 2 * dx - dy;
            int32_t incrN = 2 * dx;
            int32_t incrNE = 2 * (dx - dy);

            while (y != y2)
            {
                y += sign_y;

                if (d <= 0)
                {
                    d += incrN;
                }
                else
                {
                    d += incrNE;
                    x += sign_x;
                }

                setPixelIndexed(image, x, y, index);
            }
        }
    }
}

//-------------------------------------------------------------------------

void
imageLineRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t y1,
    int32_t x2,
    int32_t y2,
    const RGBA8_T *rgb)
{
    if (y1 == y2)
    {
        imageHorizontalLineRGB(image, x1, x2, y1, rgb);
    }
    else if (x1 == x2)
    {
        imageVerticalLineRGB(image, x1, y1, y2, rgb);
    }
    else
    {
        int32_t dx = abs(x2 - x1);
        int32_t dy = abs(y2 - y1);

        int32_t sign_x = (x1 <= x2) ? 1 : -1;
        int32_t sign_y = (y1 <= y2) ? 1 : -1;

        int32_t x = x1;
        int32_t y = y1;

        setPixelRGB(image, x, y, rgb);

        if (dx > dy)
        {
            int32_t d = 2 * dy - dx;
            int32_t incrE = 2 * dy;
            int32_t incrNE = 2 * (dy - dx);

            while (x != x2)
            {
                x += sign_x;

                if (d <= 0)
                {
                    d += incrE;
                }
                else
                {
                    d += incrNE;
                    y += sign_y;
                }

                setPixelRGB(image, x, y, rgb);
            }
        }
        else
        {
            int32_t d = 2 * dx - dy;
            int32_t incrN = 2 * dx;
            int32_t incrNE = 2 * (dx - dy);

            while (y != y2)
            {
                y += sign_y;

                if (d <= 0)
                {
                    d += incrN;
                }
                else
                {
                    d += incrNE;
                    x += sign_x;
                }

                setPixelRGB(image, x, y, rgb);
            }
        }
    }
}

//-------------------------------------------------------------------------

void
imageHorizontalLineIndexed(
    IMAGE_T *image,
    int32_t x1,
    int32_t x2,
    int32_t y,
    int8_t index)
{
    int32_t sign_x = (x1 <= x2) ? 1 : -1;
    int32_t x = x1;

    setPixelIndexed(image, x, y, index);

    while (x != x2)
    {
        x += sign_x;
        setPixelIndexed(image, x, y, index);
    }
}

//-------------------------------------------------------------------------

void
imageHorizontalLineRGB(
    IMAGE_T *image,
    int32_t x1,
    int32_t x2,
    int32_t y,
    const RGBA8_T *rgb)
{
    int32_t sign_x = (x1 <= x2) ? 1 : -1;
    int32_t x = x1;

    setPixelRGB(image, x, y, rgb);

    while (x != x2)
    {
        x += sign_x;
        setPixelRGB(image, x, y, rgb);
    }
}

//-------------------------------------------------------------------------

void
imageVerticalLineIndexed(
    IMAGE_T *image,
    int32_t x,
    int32_t y1,
    int32_t y2,
    int8_t index)
{
    int32_t sign_y = (y1 <= y2) ? 1 : -1;
    int32_t y = y1;

    setPixelIndexed(image, x, y, index);

    while (y != y2)
    {
        y += sign_y;
        setPixelIndexed(image, x, y, index);
    }
}

//-------------------------------------------------------------------------

void
imageVerticalLineRGB(
    IMAGE_T *image,
    int32_t x,
    int32_t y1,
    int32_t y2,
    const RGBA8_T *rgb)
{
    int32_t sign_y = (y1 <= y2) ? 1 : -1;
    int32_t y = y1;

    setPixelRGB(image, x, y, rgb);

    while (y != y2)
    {
        y += sign_y;
        setPixelRGB(image, x, y, rgb);
    }
}

