import sys
import pytest
import copy
from ctypes import c_int, POINTER, byref, cast, ArgumentError
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_EVERYTHING, SDL_TRUE
from sdl2 import SDL_Color
from sdl2.stdinc import Uint8, Uint16, Uint32

RGBA8888 = [0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF]
RGBX8888 = [0xFF000000, 0x00FF0000, 0x0000FF00, 0]


# Test custom macros

def test_SDL_FOURCC():
    assert sdl2.SDL_FOURCC("0", "0", "0", "0") == 0x30303030
    assert sdl2.SDL_FOURCC("1", "1", "1", "1") == 0x31313131
    assert sdl2.SDL_FOURCC("1", "2", "3", "4") == 0x34333231
    assert sdl2.SDL_FOURCC("4", "3", "2", "1") == 0x31323334
    with pytest.raises(TypeError):
        sdl2.SDL_FOURCC("a", "a", "a", None)
    with pytest.raises(TypeError):
        sdl2.SDL_FOURCC("a", "a", "a", 1)

def test_SDL_DEFINE_PIXELFORMAT():
    fmt = sdl2.SDL_DEFINE_PIXELFORMAT(
        sdl2.SDL_PIXELTYPE_INDEX1, sdl2.SDL_BITMAPORDER_4321, 0, 1, 0
    )
    assert fmt == sdl2.SDL_PIXELFORMAT_INDEX1LSB

    fmt = sdl2.SDL_DEFINE_PIXELFORMAT(
        sdl2.SDL_PIXELTYPE_PACKED16,
        sdl2.SDL_PACKEDORDER_XRGB,
        sdl2.SDL_PACKEDLAYOUT_4444,
        12, 2
    )
    assert fmt == sdl2.SDL_PIXELFORMAT_RGB444

    fmt = sdl2.SDL_DEFINE_PIXELFORMAT(
        sdl2.SDL_PIXELTYPE_PACKED16,
        sdl2.SDL_PACKEDORDER_ABGR,
        sdl2.SDL_PACKEDLAYOUT_1555,
        16, 2
    )
    assert fmt == sdl2.SDL_PIXELFORMAT_ABGR1555

def test_SDL_PIXELTYPE():
    expected = [
        (sdl2.SDL_PIXELFORMAT_INDEX1LSB, sdl2.SDL_PIXELTYPE_INDEX1),
        (sdl2.SDL_PIXELFORMAT_INDEX1MSB, sdl2.SDL_PIXELTYPE_INDEX1),
        (sdl2.SDL_PIXELFORMAT_INDEX4LSB, sdl2.SDL_PIXELTYPE_INDEX4),
        (sdl2.SDL_PIXELFORMAT_ARGB8888, sdl2.SDL_PIXELTYPE_PACKED32)
    ]
    for fmt, pxtype in expected:
        assert sdl2.SDL_PIXELTYPE(fmt) == pxtype

def test_SDL_PIXELORDER():
    expected = [
        (sdl2.SDL_PIXELFORMAT_INDEX1LSB, sdl2.SDL_BITMAPORDER_4321),
        (sdl2.SDL_PIXELFORMAT_INDEX1MSB, sdl2.SDL_BITMAPORDER_1234),
        (sdl2.SDL_PIXELFORMAT_INDEX4LSB, sdl2.SDL_BITMAPORDER_4321),
        (sdl2.SDL_PIXELFORMAT_ARGB8888, sdl2.SDL_PACKEDORDER_ARGB)
    ]
    for fmt, pxorder in expected:
        assert sdl2.SDL_PIXELORDER(fmt) == pxorder

def test_SDL_PIXELLAYOUT():
    expected = [
        (sdl2.SDL_PIXELFORMAT_INDEX1LSB, sdl2.SDL_PACKEDLAYOUT_NONE),
        (sdl2.SDL_PIXELFORMAT_RGB332, sdl2.SDL_PACKEDLAYOUT_332),
        (sdl2.SDL_PIXELFORMAT_ARGB8888, sdl2.SDL_PACKEDLAYOUT_8888)
    ]
    for fmt, pxlayout in expected:
        assert sdl2.SDL_PIXELLAYOUT(fmt) == pxlayout

def test_SDL_BITSPERPIXEL():
    bitspp = sdl2.SDL_BITSPERPIXEL
    assert bitspp(sdl2.SDL_PIXELFORMAT_INDEX1LSB) == 1
    assert bitspp(sdl2.SDL_PIXELFORMAT_INDEX4LSB) == 4
    assert bitspp(sdl2.SDL_PIXELFORMAT_RGB332) == 8
    assert bitspp(sdl2.SDL_PIXELFORMAT_ARGB8888) == 32

def test_SDL_BYTESPERPIXEL():
    bytespp = sdl2.SDL_BYTESPERPIXEL
    assert bytespp(sdl2.SDL_PIXELFORMAT_INDEX1LSB) == 0
    assert bytespp(sdl2.SDL_PIXELFORMAT_INDEX4LSB) == 0
    assert bytespp(sdl2.SDL_PIXELFORMAT_RGB332) == 1
    assert bytespp(sdl2.SDL_PIXELFORMAT_ARGB8888) == 4
    assert bytespp(sdl2.SDL_PIXELFORMAT_YUY2) == 2
    assert bytespp(sdl2.SDL_PIXELFORMAT_IYUV) == 1
    assert bytespp(sdl2.SDL_PIXELFORMAT_UYVY) == 2

def test_SDL_ISPIXELFORMAT_INDEXED():
    isindexed = sdl2.SDL_ISPIXELFORMAT_INDEXED
    assert isindexed(sdl2.SDL_PIXELFORMAT_INDEX1LSB)
    assert isindexed(sdl2.SDL_PIXELFORMAT_INDEX1MSB)
    assert isindexed(sdl2.SDL_PIXELFORMAT_INDEX4LSB)
    assert isindexed(sdl2.SDL_PIXELFORMAT_INDEX4MSB)
    assert isindexed(sdl2.SDL_PIXELFORMAT_INDEX8)
    assert not isindexed(sdl2.SDL_PIXELFORMAT_RGB332)
    assert not isindexed(sdl2.SDL_PIXELFORMAT_ARGB8888)
    assert not isindexed(sdl2.SDL_PIXELFORMAT_YUY2)

def test_SDL_ISPIXELFORMAT_ALPHA():
    isalpha = sdl2.SDL_ISPIXELFORMAT_ALPHA
    assert isalpha(sdl2.SDL_PIXELFORMAT_ARGB8888)
    assert isalpha(sdl2.SDL_PIXELFORMAT_RGBA8888)
    assert isalpha(sdl2.SDL_PIXELFORMAT_RGBA4444)
    assert isalpha(sdl2.SDL_PIXELFORMAT_ABGR1555)
    assert not isalpha(sdl2.SDL_PIXELFORMAT_INDEX1LSB)
    assert not isalpha(sdl2.SDL_PIXELFORMAT_INDEX4MSB)
    assert not isalpha(sdl2.SDL_PIXELFORMAT_RGB332)
    assert not isalpha(sdl2.SDL_PIXELFORMAT_YUY2)
    assert not isalpha(sdl2.SDL_PIXELFORMAT_RGBX8888)

def test_SDL_ISPIXELFORMAT_FOURCC():
    isfourcc = sdl2.SDL_ISPIXELFORMAT_FOURCC
    assert isfourcc(sdl2.SDL_PIXELFORMAT_YV12)
    assert isfourcc(sdl2.SDL_PIXELFORMAT_IYUV)
    assert isfourcc(sdl2.SDL_PIXELFORMAT_YUY2)
    assert isfourcc(sdl2.SDL_PIXELFORMAT_UYVY)
    assert isfourcc(sdl2.SDL_PIXELFORMAT_YVYU)
    assert not isfourcc(sdl2.SDL_PIXELFORMAT_ARGB8888)
    assert not isfourcc(sdl2.SDL_PIXELFORMAT_ARGB4444)
    assert not isfourcc(sdl2.SDL_PIXELFORMAT_INDEX8)


# Test pixel format functions

def test_SDL_GetPixelFormatName():
    expected = [
        (sdl2.SDL_PIXELFORMAT_INDEX1LSB, b"SDL_PIXELFORMAT_INDEX1LSB"),
        (sdl2.SDL_PIXELFORMAT_UNKNOWN, b"SDL_PIXELFORMAT_UNKNOWN"),
        (sdl2.SDL_PIXELFORMAT_UYVY, b"SDL_PIXELFORMAT_UYVY"),
        (99999, b"SDL_PIXELFORMAT_UNKNOWN")
    ]
    for fmt, name in expected:
        assert sdl2.SDL_GetPixelFormatName(fmt) == name

def test_SDL_MasksToPixelFormatEnum():
    formats = [
        (sdl2.SDL_PIXELFORMAT_RGBA8888, [32] + RGBA8888),
        (sdl2.SDL_PIXELFORMAT_RGBX8888, [32] + RGBX8888),
        (sdl2.SDL_PIXELFORMAT_INDEX1MSB, [1, 0, 0, 0, 0]),
    ]
    for fmt, expected in formats:
        bpp, r, g, b, a = expected
        enum = sdl2.SDL_MasksToPixelFormatEnum(bpp, r, g, b, a)
        assert enum == fmt

    enum = sdl2.SDL_MasksToPixelFormatEnum(17, 3, 6, 64, 255)
    assert enum == sdl2.SDL_PIXELFORMAT_UNKNOWN

def test_SDL_PixelFormatEnumToMasks():
    formats = [
        (sdl2.SDL_PIXELFORMAT_RGBA8888, [32] + RGBA8888),
        (sdl2.SDL_PIXELFORMAT_RGBX8888, [32] + RGBX8888),
        (sdl2.SDL_PIXELFORMAT_INDEX1LSB, [1, 0, 0, 0, 0]),
        (sdl2.SDL_PIXELFORMAT_INDEX1MSB, [1, 0, 0, 0, 0]),
        (sdl2.SDL_PIXELFORMAT_UNKNOWN, [0, 0, 0, 0, 0]),
    ]
    bpp = c_int(0)
    r, g, b, a = Uint32(0), Uint32(0), Uint32(0), Uint32(0)
    for fmt, expected in formats:
        ret = sdl2.SDL_PixelFormatEnumToMasks(
            fmt, byref(bpp), byref(r), byref(g), byref(b), byref(a)
        )
        assert sdl2.SDL_GetError() == b""
        assert ret == SDL_TRUE
        assert [x.value for x in (bpp, r, g, b, a)] == expected

def test_SDL_AllocFreeFormat():
    formats = [
        [sdl2.SDL_PIXELFORMAT_RGBA8888, (32, 4)],
        [sdl2.SDL_PIXELFORMAT_INDEX1LSB, (1, 1)],
        [sdl2.SDL_PIXELFORMAT_INDEX4MSB, (4, 1)],
        [sdl2.SDL_PIXELFORMAT_ARGB4444, (16, 2)],
    ]
    for fmt, info in formats:
        bits_pp, bytes_pp = info
        pixfmt = sdl2.SDL_AllocFormat(fmt)
        assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
        assert pixfmt.contents.format == fmt
        assert pixfmt.contents.BitsPerPixel == bits_pp
        assert pixfmt.contents.BytesPerPixel == bytes_pp
        sdl2.SDL_FreeFormat(pixfmt)

def test_SDL_AllocFreePalette():
    palette = sdl2.SDL_AllocPalette(10)
    assert isinstance(palette.contents, sdl2.SDL_Palette)
    assert palette.contents.ncolors == 10

    colors = palette.contents.colors
    for x in range(palette.contents.ncolors):
        assert isinstance(colors[x], SDL_Color)
    colors[3].r = 70
    assert colors[3].r == 70

    # Try modifying the palette
    color = colors[4]
    color.g = 33
    assert color.g == 33
    assert colors[4].g == 33

    sdl2.SDL_FreePalette(palette)

def test_SDL_SetPaletteColors():
    colors = []
    for v in range(20):
        colors.append(SDL_Color(v, v + 10, v + 20))
    col_array = (SDL_Color * len(colors))(*colors)

    palette = sdl2.SDL_AllocPalette(20)
    assert isinstance(palette.contents, sdl2.SDL_Palette)
    assert palette.contents.ncolors == 20
    
    sdl2.SDL_SetPaletteColors(palette, col_array, 0, 20)
    for index in range(20):
        rgb = palette.contents.colors[index]
        assert rgb == colors[index]

    sdl2.SDL_FreePalette(palette)

def test_SDL_SetPixelFormatPalette():
    palette = sdl2.SDL_AllocPalette(2)
    assert isinstance(palette.contents, sdl2.SDL_Palette)
    palette.contents.colors[1].r = 128
    palette.contents.colors[1].g = 64
    palette.contents.colors[1].b = 0

    pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_INDEX1MSB)
    assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
    ret = sdl2.SDL_SetPixelFormatPalette(pixfmt, palette)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0

    fmt_palette = pixfmt.contents.palette.contents
    assert fmt_palette.colors[1].r == 128
    assert fmt_palette.colors[1].g == 64
    assert fmt_palette.colors[1].b == 0

    sdl2.SDL_FreeFormat(pixfmt)
    sdl2.SDL_FreePalette(palette)

def test_SDL_CalculateGammaRamp():
    vals = (Uint16 * 256)()
    sdl2.SDL_CalculateGammaRamp(1.0, cast(vals, POINTER(Uint16)))
    assert len(vals) == 256
    p = 0
    for x in vals:
        assert x == p
        p += 257

    sdl2.SDL_CalculateGammaRamp(0.0, cast(vals, POINTER(Uint16)))
    assert len(vals) == 256
    for x in vals:
        assert x == 0

    gamma = 0.5
    sdl2.SDL_CalculateGammaRamp(gamma, cast(vals, POINTER(Uint16)))
    assert len(vals) == 256
    for i in range(len(vals)):
        expected = int((i / 256.0) ** gamma * 65535 + 0.5)
        vals[i] == expected

    # Test error on negative value
    sdl2.SDL_ClearError()
    sdl2.SDL_CalculateGammaRamp(-1.0, cast(vals, POINTER(Uint16)))
    assert sdl2.SDL_GetError() != b""
    sdl2.SDL_ClearError()

def test_SDL_GetRGB():
    colors = [
        (0xFFAA8811, [0xFF, 0xAA, 0x88]),
        (0x00000000, [0x00, 0x00, 0x00]),
        (0xFFFFFFFF, [0xFF, 0xFF, 0xFF]),
        (0x11223344, [0x11, 0x22, 0x33]),
    ]
    pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_RGBA8888)
    assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
    r, g, b = Uint8(0), Uint8(0), Uint8(0)
    for col, expected in colors:
        sdl2.SDL_GetRGB(col, pixfmt, byref(r), byref(g), byref(b))
        assert [x.value for x in (r, g, b)] == expected
    sdl2.SDL_FreeFormat(pixfmt)

    # With a pallete format, first argument is index of color to retrieve
    palette = sdl2.SDL_AllocPalette(2)
    palette.contents.colors[1].r = 128
    palette.contents.colors[1].g = 64
    palette.contents.colors[1].b = 32
    pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_INDEX1MSB)
    assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
    sdl2.SDL_SetPixelFormatPalette(pixfmt, palette)
    sdl2.SDL_GetRGB(1, pixfmt, byref(r), byref(g), byref(b))
    assert [x.value for x in (r, g, b)] == [128, 64, 32]

    # With a pallete format, missing index returns all zeros
    sdl2.SDL_GetRGB(16, pixfmt, byref(r), byref(g), byref(b))
    assert [x.value for x in (r, g, b)] == [0, 0, 0]
    sdl2.SDL_FreeFormat(pixfmt)
    sdl2.SDL_FreePalette(palette)

def test_SDL_GetRGBA():
    colors = [
        (0xFFAA8811, [0xFF, 0xAA, 0x88, 0x11]),
        (0x00000000, [0x00, 0x00, 0x00, 0x00]),
        (0xFFFFFFFF, [0xFF, 0xFF, 0xFF, 0xFF]),
        (0x11223344, [0x11, 0x22, 0x33, 0x44]),
    ]
    pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_RGBA8888)
    assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
    r, g, b, a = Uint8(0), Uint8(0), Uint8(0), Uint8(0)
    for col, expected in colors:
        sdl2.SDL_GetRGBA(col, pixfmt, byref(r), byref(g), byref(b), byref(a))
        assert [x.value for x in (r, g, b, a)] == expected
    sdl2.SDL_FreeFormat(pixfmt)

    # With a pallete format, first argument is index of color to retrieve
    palette = sdl2.SDL_AllocPalette(2)
    palette.contents.colors[1].r = 128
    palette.contents.colors[1].g = 64
    palette.contents.colors[1].b = 32
    palette.contents.colors[1].a = 96
    pixfmt = sdl2.SDL_AllocFormat(sdl2.SDL_PIXELFORMAT_INDEX1MSB)
    assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
    sdl2.SDL_SetPixelFormatPalette(pixfmt, palette)
    sdl2.SDL_GetRGBA(1, pixfmt, byref(r), byref(g), byref(b), byref(a))
    assert [x.value for x in (r, g, b, a)] == [128, 64, 32, 96]

    # With a pallete format, missing index returns all zeros
    sdl2.SDL_GetRGBA(16, pixfmt, byref(r), byref(g), byref(b), byref(a))
    assert [x.value for x in (r, g, b, a)] == [0, 0, 0, 0]
    sdl2.SDL_FreeFormat(pixfmt)

def test_SDL_MapRGB():
    r, g, b = (0xFF, 0xAA, 0x88)
    formats = [
        (sdl2.SDL_PIXELFORMAT_RGBA8888, 0xFFAA88FF),
        (sdl2.SDL_PIXELFORMAT_BGRA8888, 0x88AAFFFF),
        (sdl2.SDL_PIXELFORMAT_ABGR8888, 0xFF88AAFF),
    ]
    for fmt, expected in formats:
        pixfmt = sdl2.SDL_AllocFormat(fmt)
        assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
        col = sdl2.SDL_MapRGB(pixfmt, r, g, b)
        assert col == expected
        sdl2.SDL_FreeFormat(pixfmt)

def test_SDL_MapRGBA():
    r, g, b, a = (0xFF, 0xAA, 0x88, 0x11)
    formats = [
        (sdl2.SDL_PIXELFORMAT_RGBA8888, 0xFFAA8811),
        (sdl2.SDL_PIXELFORMAT_BGRA8888, 0x88AAFF11),
        (sdl2.SDL_PIXELFORMAT_ABGR8888, 0x1188AAFF),
    ]
    for fmt, expected in formats:
        pixfmt = sdl2.SDL_AllocFormat(fmt)
        assert isinstance(pixfmt.contents, sdl2.SDL_PixelFormat)
        col = sdl2.SDL_MapRGBA(pixfmt, r, g, b, a)
        assert col == expected
        sdl2.SDL_FreeFormat(pixfmt)


# Test structs and objects

def test_SDL_PixelFormat():
    pixfmt = sdl2.SDL_PixelFormat()
    assert isinstance(pixfmt, sdl2.SDL_PixelFormat)

def test_SDL_Palette():
    palette = sdl2.SDL_Palette()
    assert isinstance(palette, sdl2.SDL_Palette)


class TestSDLColor(object):
    __tags__ = ["sdl"]

    def test_init(self):
        col = SDL_Color()

        # Check default values
        assert col.r == 255
        assert col.g == 255
        assert col.b == 255
        assert col.a == 255

        # Test RGB and RGBA inputs
        col_rgb = SDL_Color(128, 128, 128)
        col_rgba = SDL_Color(128, 128, 128, 64)

        # Test errors on bad values
        with pytest.raises(TypeError):
            SDL_Color(0.1, 0, 0)

    def test___repr__(self):
        c1 = SDL_Color()
        assert "SDL_Color(r=255, g=255, b=255, a=255)" == repr(c1)
        c2 = eval(repr(c1))
        assert c2 == c1
        c3 = eval(repr(c2))
        assert c3 == c2

    def test___copy__(self):
        c = SDL_Color(10, 20, 30)
        c2 = copy.copy(c)
        assert c == c2
        c.r = 100
        assert c != c2

    def test___eq__(self):
        assert SDL_Color(255, 0, 0, 0) == SDL_Color(255, 0, 0, 0)
        assert SDL_Color(0, 255, 0, 0) == SDL_Color(0, 255, 0, 0)
        assert SDL_Color(0, 0, 255, 0) == SDL_Color(0, 0, 255, 0)
        assert SDL_Color(0, 0, 0, 255) == SDL_Color(0, 0, 0, 255)
        assert SDL_Color(0, 0, 0, 0) == SDL_Color(0, 0, 0, 0)

        assert not (SDL_Color(0, 0, 0, 0) == SDL_Color(255, 0, 0, 0))
        assert not (SDL_Color(0, 0, 0, 0) == SDL_Color(0, 255, 0, 0))
        assert not (SDL_Color(0, 0, 0, 0) == SDL_Color(0, 0, 255, 0))
        assert not (SDL_Color(0, 0, 0, 0) == SDL_Color(0, 0, 0, 255))

    def test___ne__(self):
        assert SDL_Color(0, 0, 0, 0) != SDL_Color(255, 0, 0, 0)
        assert SDL_Color(0, 0, 0, 0) != SDL_Color(0, 255, 0, 0)
        assert SDL_Color(0, 0, 0, 0) != SDL_Color(0, 0, 255, 0)
        assert SDL_Color(0, 0, 0, 0) != SDL_Color(0, 0, 255, 0)
        assert SDL_Color(0, 0, 0, 0) != SDL_Color(0, 0, 0, 255)

        assert not (SDL_Color(255, 0, 0, 0) != SDL_Color(255, 0, 0, 0))
        assert not (SDL_Color(0, 255, 0, 0) != SDL_Color(0, 255, 0, 0))
        assert not (SDL_Color(0, 0, 255, 0) != SDL_Color(0, 0, 255, 0))
        assert not (SDL_Color(0, 0, 0, 255) != SDL_Color(0, 0, 0, 255))

    def test_colors(self):
        col = SDL_Color()

        # Check getting/setting values
        for x in (0, 16, 32, 64, 128, 255):
            col.r = x
            col.g = x
            col.b = x
            col.a = x
            assert col.r == x
            assert col.g == x
            assert col.b == x
            assert col.a == x

        # Test wrap for out-of-bounds values
        col.r = 256
        assert col.r == 0
        col.g = -1
        assert col.g == 255
