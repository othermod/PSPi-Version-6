import os
import sys
import array
import pytest
from ctypes import c_int, byref, cast, POINTER, c_void_p
import sdl2
from sdl2.ext import CTypesView
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_EVERYTHING
from sdl2.stdinc import Uint8, Uint16, Uint32, SDL_TRUE, SDL_FALSE
from sdl2 import blendmode, endian, pixels, rect, rwops, error


@pytest.fixture
def test_surf_argb(with_sdl):
    w, h = 32, 32
    fmt = pixels.SDL_PIXELFORMAT_ARGB8888
    sf = sdl2.SDL_CreateRGBSurfaceWithFormat(0, w, h, 0, fmt)
    assert sdl2.SDL_GetError() == b""
    assert isinstance(sf.contents, sdl2.SDL_Surface)
    yield sf
    sdl2.SDL_FreeSurface(sf)


def create_pixel_buffer(w, h, fmt):
    bpp = c_int()
    rmask, gmask, bmask, amask = Uint32(0), Uint32(0), Uint32(0), Uint32(0)
    ret = pixels.SDL_PixelFormatEnumToMasks(
        fmt, byref(bpp), byref(rmask), byref(gmask), byref(bmask), byref(amask)
    )
    assert ret == SDL_TRUE
    out = {
        'w': w,
        'h': h,
        'bpp': bpp.value,
        'pitch': w * int(bpp.value / 8),
        'masks': [x.value for x in (rmask, gmask, bmask, amask)],
        'fmt': fmt,
    }
    # NOTE: Currently only supports formats with bpp of 16 or 32
    arrtype = Uint16 if out['bpp'] == 16 else Uint32
    buf = [x << (bpp.value - 8) for x in range(w * h)]
    out['pixels'] = (arrtype * len(buf))(*buf)
    out['ptr'] = cast(out['pixels'], POINTER(Uint8))
    return out


to_ctypes = lambda seq, dtype: (dtype * len(seq))(*seq)

pixel_buffers = {
    'RGBA16': create_pixel_buffer(16, 16, pixels.SDL_PIXELFORMAT_RGBA4444),
    'RGBA32': create_pixel_buffer(16, 16, pixels.SDL_PIXELFORMAT_RGBA8888),
}

bmp_testfile = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "resources", "surfacetest.bmp"
)

indexdepths = [1, 4, 8]
rgbdepths = [8, 12, 15, 16]
rgbadepths = [16, 24, 32]
alldepths = list(set(indexdepths + rgbdepths + rgbadepths))

test_sizes = ((1, 1), (7, 17), (32, 32), (100, 10), (640, 480))

blitsizes = ((2, 2), (5, 5), (10, 10), (20, 20),
             (2, 4), (5, 3), (8, 12), (27, 9),
             )

blitpositions = (
    rect.SDL_Rect(0, 0),
    rect.SDL_Rect(4, 4),
    rect.SDL_Rect(10, 10),
    rect.SDL_Rect(15, 15),
    rect.SDL_Rect(-2, 1),
    rect.SDL_Rect(3, -4),
    rect.SDL_Rect(0, 3),
    rect.SDL_Rect(4, 0),
    rect.SDL_Rect(12, 6),
    rect.SDL_Rect(13, 22),
    )



def test_SDL_Surface():
    sf = sdl2.SDL_Surface()
    assert isinstance(sf, sdl2.SDL_Surface)


def test_SDL_CreateFreeRGBSurface(with_sdl):
    # Test creating surfaces without colour masks
    for w, h in test_sizes:
        for bpp in alldepths:
            sdl2.SDL_ClearError()
            sf = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, 0, 0, 0, 0)
            assert sdl2.SDL_GetError() == b""
            assert isinstance(sf.contents, sdl2.SDL_Surface)
            sdl2.SDL_FreeSurface(sf)

    # Test creating surfaces with colour masks
    bpp = c_int()
    rmask, gmask, bmask, amask = Uint32(0), Uint32(0), Uint32(0), Uint32(0)
    for fmt_name, fmt in pixels.NAME_MAP.items():
        if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
            continue
        ret = pixels.SDL_PixelFormatEnumToMasks(
            fmt, byref(bpp), byref(rmask), byref(gmask), byref(bmask), byref(amask)
        )
        assert sdl2.SDL_GetError() == b""
        assert ret == SDL_TRUE
        sf = sdl2.SDL_CreateRGBSurface(
            0, 16, 16, bpp, rmask, gmask, bmask, amask
        )
        assert sdl2.SDL_GetError() == b""
        assert isinstance(sf.contents, sdl2.SDL_Surface)
        sdl2.SDL_FreeSurface(sf)


def test_SDL_CreateRGBSurfaceWithFormat(with_sdl):
    for w, h in test_sizes:
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            sdl2.SDL_ClearError()
            sf = sdl2.SDL_CreateRGBSurfaceWithFormat(0, w, h, 0, fmt)
            assert sdl2.SDL_GetError() == b""
            assert isinstance(sf.contents, sdl2.SDL_Surface)
            sdl2.SDL_FreeSurface(sf)


def test_SDL_CreateRGBSurfaceFrom(with_sdl):
    for name, buf in pixel_buffers.items():
        rmask, gmask, bmask, amask = buf['masks']
        sdl2.SDL_ClearError()
        sf = sdl2.SDL_CreateRGBSurfaceFrom(
            buf['ptr'], buf['w'], buf['h'], buf['bpp'], buf['pitch'],
            rmask, gmask, bmask, amask
        )
        assert sdl2.SDL_GetError() == b""
        assert isinstance(sf.contents, sdl2.SDL_Surface)
        sdl2.SDL_FreeSurface(sf)


def test_SDL_CreateRGBSurfaceWithFormatFrom(with_sdl):
    for name, buf in pixel_buffers.items():
        sdl2.SDL_ClearError()
        sf = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            buf['ptr'], buf['w'], buf['h'], buf['bpp'], buf['pitch'], buf['fmt']
        )
        assert sdl2.SDL_GetError() == b""
        assert isinstance(sf.contents, sdl2.SDL_Surface)
        sdl2.SDL_FreeSurface(sf)


def test_SDL_ConvertPixels(with_sdl):
    # Test conversion of pixels to surface of same format
    for name, buf in pixel_buffers.items():
        dtype = Uint16 if buf['bpp'] == 16 else Uint32
        dst = (dtype * len(buf['pixels']))()
        dst_ptr = cast(dst, POINTER(Uint8))
        sdl2.SDL_ClearError()
        ret = sdl2.SDL_ConvertPixels(
            buf['w'], buf['h'], buf['fmt'], buf['ptr'], buf['pitch'],
            buf['fmt'], dst_ptr, buf['pitch'],
        )
        assert sdl2.SDL_GetError() == b""
        assert ret == 0
        for index, val in enumerate(dst):
            assert val == buf['pixels'][index]
    
    # Test conversion of pixels to surface of different format
    buf = pixel_buffers['RGBA32']
    dtype = Uint16 if buf['bpp'] == 16 else Uint32
    dst = (dtype * len(buf['pixels']))()
    dst_ptr = cast(dst, POINTER(Uint8))
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_ConvertPixels(
        buf['w'], buf['h'], buf['fmt'], buf['ptr'], buf['pitch'],
        pixels.SDL_PIXELFORMAT_ABGR8888, dst_ptr, buf['pitch'],
    )
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    for index, val in enumerate(dst):
        assert sdl2.SDL_Swap32(val) == buf['pixels'][index]


@pytest.mark.skip("not implemented")
def test_SDL_SetSurfacePalette(with_sdl):
    pass


def test_SDL_LockUnlockSurface(test_surf_argb):
    sf = test_surf_argb
    sdl2.SDL_LockSurface(sf)
    assert sf.contents.locked
    sdl2.SDL_UnlockSurface(sf)
    assert not sf.contents.locked


def test_SDL_LoadBMP_RW(with_sdl):
    with open(bmp_testfile, "rb") as f:
        imgrw = rwops.rw_from_object(f)
        imgsurface = sdl2.SDL_LoadBMP_RW(imgrw, 0)
        assert sdl2.SDL_GetError() == b""
        assert isinstance(imgsurface.contents, sdl2.SDL_Surface)
        sdl2.SDL_FreeSurface(imgsurface)


def test_SDL_LoadBMP(with_sdl):
    imgsurface = sdl2.SDL_LoadBMP(bmp_testfile.encode("utf-8"))
    assert sdl2.SDL_GetError() == b""
    assert isinstance(imgsurface.contents, sdl2.SDL_Surface)
    sdl2.SDL_FreeSurface(imgsurface)


@pytest.mark.skip("not implemented")
def test_SDL_SaveBMP_RW(with_sdl):
    pass


@pytest.mark.skip("not implemented")
def test_SDL_SaveBMP(with_sdl):
    pass


def test_SDL_SetSurfaceRLEMUSTLOCK(test_surf_argb):
    # NOTE: As of SDL 2.0.22, SDL_MUSTLOCK doesn't work properly
    sf = test_surf_argb
    # Test that surface requires locking after RLE set
    ret = sdl2.SDL_SetSurfaceRLE(sf, 1)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    #assert sdl2.SDL_MUSTLOCK(sf)
    # Try disabling RLE
    ret = sdl2.SDL_SetSurfaceRLE(sf, 0)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    #assert not sdl2.SDL_MUSTLOCK(sf)


@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_HasSurfaceRLE(test_surf_argb):
    sf = test_surf_argb
    # Test for success before and after setting RLE
    assert sdl2.SDL_HasSurfaceRLE(sf) == SDL_FALSE
    ret = sdl2.SDL_SetSurfaceRLE(sf, 1)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert sdl2.SDL_HasSurfaceRLE(sf) == SDL_TRUE
    # Disable RLE on surface again
    ret = sdl2.SDL_SetSurfaceRLE(sf, 0)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert sdl2.SDL_HasSurfaceRLE(sf) == SDL_FALSE


def test_SDL_GetSetColorKey(with_sdl):
    # NOTE: Not sure if we really need to test with all pixel formats
    colorkeys = (
        (0, 0, 0),
        (32, 64, 128),
        (1, 2, 4),
        (255, 255, 255),
        (128, 128, 128),
    )
    currentkey = Uint32()
    for fmt in pixels.ALL_PIXELFORMATS:
        if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
            continue
        sdl2.SDL_ClearError()
        sf = sdl2.SDL_CreateRGBSurfaceWithFormat(0, 10, 10, 0, fmt)
        assert sdl2.SDL_GetError() == b""
        assert isinstance(sf.contents, sdl2.SDL_Surface)
        pixfmt = sdl2.SDL_AllocFormat(fmt)
        for r, g, b in colorkeys:
            key = pixels.SDL_MapRGB(pixfmt, r, g, b)
            ret = sdl2.SDL_SetColorKey(sf, 1, key)
            assert sdl2.SDL_GetError() == b""
            assert ret == 0
            ret = sdl2.SDL_GetColorKey(sf, byref(currentkey))
            assert sdl2.SDL_GetError() == b""
            assert ret == 0
        pixels.SDL_FreeFormat(pixfmt)
        sdl2.SDL_FreeSurface(sf)


@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_HasColorKey(test_surf_argb):
    sf = test_surf_argb
    assert sdl2.SDL_HasColorKey(sf) == SDL_FALSE
    key = pixels.SDL_MapRGB(sf.contents.format, 255, 255, 255)
    ret = sdl2.SDL_SetColorKey(sf, 1, key)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert sdl2.SDL_HasColorKey(sf) == SDL_TRUE



# TODO: mostly covers positive tests right now - fix this!
class TestSDLSurface(object):
    __tags__ = ["sdl"]

    @classmethod
    def setup_class(cls):
        SDL_Init(SDL_INIT_EVERYTHING)

    @classmethod
    def teardown_class(cls):
        SDL_Quit()

    def test_SDL_ConvertSurface(self):
        tenbit = [pixels.SDL_PACKEDLAYOUT_2101010, pixels.SDL_PACKEDLAYOUT_1010102]
        for idx in pixels.ALL_PIXELFORMATS:
            pfmt = pixels.SDL_AllocFormat(idx)
            for fmt in pixels.ALL_PIXELFORMATS:
                idx_name = pixels.SDL_GetPixelFormatName(idx).decode('utf-8') # for debug
                fmt_name = pixels.SDL_GetPixelFormatName(fmt).decode('utf-8') # for debug
                # SDL2 doesn't support converting fancier formats (e.g YUV, 10bit)
                if pixels.SDL_ISPIXELFORMAT_FOURCC(idx) or pixels.SDL_PIXELLAYOUT(idx) in tenbit:
                    continue
                if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt) or pixels.SDL_PIXELLAYOUT(fmt) in tenbit:
                    continue
                # SDL2 doesn't support converting to formats w/ less than 8 bpp
                if pixels.SDL_BITSPERPIXEL(idx) < 8:
                    continue
                # SDL2 doesn't support converting from indexed formats w/ 4 bpp
                if pixels.SDL_PIXELTYPE(fmt) == pixels.SDL_PIXELTYPE_INDEX4:
                    continue
                bpp = c_int()
                rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
                ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                        byref(rmask), byref(gmask),
                                                        byref(bmask), byref(amask))
                assert ret == SDL_TRUE
                sf = sdl2.SDL_CreateRGBSurface(0, 10, 20, bpp, rmask, gmask,
                                                  bmask, amask)
                assert isinstance(sf.contents, sdl2.SDL_Surface)
                csf = sdl2.SDL_ConvertSurface(sf, pfmt, 0)
                assert csf, error.SDL_GetError()
                assert isinstance(csf.contents, sdl2.SDL_Surface)
                sdl2.SDL_FreeSurface(sf)
                sdl2.SDL_FreeSurface(csf)
            pixels.SDL_FreeFormat(pfmt)

        #######################################################################
        # sf = sdl2.create_rgb_surface(10, 10, 32, 0, 0, 0)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, None, None, None)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, sf, None, None)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, sf, "Test", 0)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, sf, 12345, 0)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, None, pfmt, 0)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, "Test", pfmt, 0)
        # self.assertRaises((AttributeError, TypeError),
        #                   sdl2.convert_surface, 12345, pfmt, 0)
        # sdl2.free_surface(sf)
        #######################################################################

    def test_SDL_ConvertSurfaceFormat(self):
        tenbit = [pixels.SDL_PACKEDLAYOUT_2101010, pixels.SDL_PACKEDLAYOUT_1010102]
        for pfmt in pixels.ALL_PIXELFORMATS:
            for fmt in pixels.ALL_PIXELFORMATS:
                # SDL2 doesn't support converting fancier formats (e.g YUV, 10bit)
                if pixels.SDL_ISPIXELFORMAT_FOURCC(pfmt) or pixels.SDL_PIXELLAYOUT(pfmt) in tenbit:
                    continue
                if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt) or pixels.SDL_PIXELLAYOUT(fmt) in tenbit:
                    continue
                # SDL2 doesn't support converting to formats w/ less than 8 bpp
                if pixels.SDL_BITSPERPIXEL(pfmt) < 8:
                    continue
                # SDL2 doesn't support converting from indexed formats w/ 4 bpp
                if pixels.SDL_PIXELTYPE(fmt) == pixels.SDL_PIXELTYPE_INDEX4:
                    continue
                bpp = c_int()
                rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
                ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                        byref(rmask), byref(gmask),
                                                        byref(bmask), byref(amask))
                assert ret == SDL_TRUE
                sf = sdl2.SDL_CreateRGBSurface(0, 10, 20, bpp, rmask, gmask,
                                                  bmask, amask)
                assert isinstance(sf.contents, sdl2.SDL_Surface)
                csf = sdl2.SDL_ConvertSurfaceFormat(sf, pfmt, 0)
                assert csf, error.SDL_GetError()
                assert isinstance(csf.contents, sdl2.SDL_Surface)
                sdl2.SDL_FreeSurface(sf)
                sdl2.SDL_FreeSurface(csf)

    @pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
    def test_SDL_PremultiplyAlpha(self):
        # TODO: Add a test for this after the ext updates, when we have
        # _create_surface to help
        pass

    def test_SDL_FillRect(self):
        rectlist = (rect.SDL_Rect(0, 0, 0, 0),
                    rect.SDL_Rect(0, 0, 10, 10),
                    rect.SDL_Rect(0, 0, -10, 10),
                    rect.SDL_Rect(0, 0, -10, -10),
                    rect.SDL_Rect(-10, -10, 10, 10),
                    rect.SDL_Rect(10, -10, 10, 10),
                    rect.SDL_Rect(10, 10, 10, 10),
                    )

        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            if pixels.SDL_BITSPERPIXEL(fmt) < 8:
                continue  # Skip < 8bpp, SDL_FillRect does not work on those

            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            for w in range(1, 100, 5):
                for h in range(1, 100, 5):
                    sf = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, rmask,
                                                      gmask, bmask, amask)
                    for r in rectlist:
                        # TODO: check for changed pixels
                        ret = sdl2.SDL_FillRect(sf, r, 0xff00ff00)
                        assert ret == 0
                    sdl2.SDL_FreeSurface(sf)

    def test_SDL_FillRects(self):
        rectlist = to_ctypes([rect.SDL_Rect(0, 0, 0, 0),
                              rect.SDL_Rect(0, 0, 10, 10),
                              rect.SDL_Rect(0, 0, -10, 10),
                              rect.SDL_Rect(0, 0, -10, -10),
                              rect.SDL_Rect(-10, -10, 10, 10),
                              rect.SDL_Rect(10, -10, 10, 10),
                              rect.SDL_Rect(10, 10, 10, 10)], rect.SDL_Rect)

        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            if pixels.SDL_BITSPERPIXEL(fmt) < 8:
                continue  # Skip < 8bpp, SDL_FillRect does not work on those
            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            for w in range(1, 100, 5):
                for h in range(1, 100, 5):
                    sf = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, rmask,
                                                      gmask, bmask, amask)
                    # TODO: check for changed pixels
                    sdl2.SDL_FillRects(sf, rectlist, 7, 0xff00ff00)
                    sdl2.SDL_FreeSurface(sf)

    def test_SDL_FreeSurface(self):
        formats = (pixels.SDL_PIXELFORMAT_INDEX1LSB,
                   pixels.SDL_PIXELFORMAT_RGB332,
                   pixels.SDL_PIXELFORMAT_RGBA4444,
                   pixels.SDL_PIXELFORMAT_BGR888,
                   pixels.SDL_PIXELFORMAT_ARGB8888,
                   pixels.SDL_PIXELFORMAT_ARGB2101010
                   )
        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in formats:
            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            sf = sdl2.SDL_CreateRGBSurface(0, 5, 5, bpp, rmask, gmask,
                                              bmask, amask)
            sdl2.SDL_FreeSurface(sf)

    def test_SDL_GetSetClipRect(self):
        rectlist = ((rect.SDL_Rect(0, 0, 0, 0), SDL_FALSE, True),
                    (rect.SDL_Rect(2, 2, 0, 0), SDL_FALSE, False),
                    (rect.SDL_Rect(2, 2, 5, 1), SDL_TRUE, True),
                    (rect.SDL_Rect(6, 5, 10, 3), SDL_TRUE, False),
                    (rect.SDL_Rect(0, 0, 10, 10), SDL_TRUE, True),
                    (rect.SDL_Rect(0, 0, -10, 10), SDL_FALSE, False),
                    (rect.SDL_Rect(0, 0, -10, -10), SDL_FALSE, False),
                    (rect.SDL_Rect(-10, -10, 10, 10), SDL_FALSE, False),
                    (rect.SDL_Rect(10, -10, 10, 10), SDL_FALSE, False),
                    (rect.SDL_Rect(10, 10, 10, 10), SDL_TRUE, False)
                    )

        clip = rect.SDL_Rect()
        sf = sdl2.SDL_CreateRGBSurface(0, 15, 15, 32, 0, 0, 0, 0)
        assert isinstance(sf.contents, sdl2.SDL_Surface)
        sdl2.SDL_GetClipRect(sf, byref(clip))
        assert clip == rect.SDL_Rect(0, 0, 15, 15)

        for r, clipsetval, cmpval in rectlist:
            retval = sdl2.SDL_SetClipRect(sf, r)
            sdl2.SDL_GetClipRect(sf, byref(clip))
            err = "Could not set clip rect %s" % r
            assert retval == clipsetval, "retval: " + err
            assert (clip == r) == cmpval, "clip: " + err
        sdl2.SDL_FreeSurface(sf)

    def test_SDL_GetSetSurfaceAlphaMod(self):
        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            sf = sdl2.SDL_CreateRGBSurface(0, 10, 10, bpp, rmask, gmask,
                                              bmask, amask)
            salpha = Uint8()
            ret = sdl2.SDL_GetSurfaceAlphaMod(sf, byref(salpha))
            assert ret == 0
            assert salpha.value == 255
            for alpha in range(0, 255):
                ret = sdl2.SDL_SetSurfaceAlphaMod(sf, alpha)
                assert ret == 0
                ret = sdl2.SDL_GetSurfaceAlphaMod(sf, byref(salpha))
                assert ret == 0
                assert salpha.value == alpha
            sdl2.SDL_FreeSurface(sf)

    def test_SDL_GetSetSurfaceBlendMode(self):
        modes = (blendmode.SDL_BLENDMODE_NONE,
                 blendmode.SDL_BLENDMODE_BLEND,
                 blendmode.SDL_BLENDMODE_ADD,
                 blendmode.SDL_BLENDMODE_MOD
                 )
        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            sf = sdl2.SDL_CreateRGBSurface(0, 10, 10, bpp, rmask, gmask,
                                              bmask, amask)
            for mode in modes:
                smode = blendmode.SDL_BlendMode()
                ret = sdl2.SDL_SetSurfaceBlendMode(sf, mode)
                assert ret == 0
                sdl2.SDL_GetSurfaceBlendMode(sf, byref(smode))
                assert smode.value == mode
            sdl2.SDL_FreeSurface(sf)

    def test_SDL_GetSetSurfaceColorMod(self):
        colormods = ((0, 0, 0),
                     (32, 64, 128),
                     (10, 20, 30),
                     (1, 2, 4),
                     (255, 255, 255),
                     (128, 128, 128),
                     (127, 127, 127),
                     )
        bpp = c_int()
        rmask, gmask, bmask, amask = Uint32(), Uint32(), Uint32(), Uint32()
        for fmt in pixels.ALL_PIXELFORMATS:
            if pixels.SDL_ISPIXELFORMAT_FOURCC(fmt):
                continue
            ret = pixels.SDL_PixelFormatEnumToMasks(fmt, byref(bpp),
                                                    byref(rmask), byref(gmask),
                                                    byref(bmask), byref(amask))
            assert ret == SDL_TRUE
            sf = sdl2.SDL_CreateRGBSurface(0, 10, 10, bpp, rmask, gmask,
                                              bmask, amask)
            for r, g, b in colormods:
                sr, sg, sb = Uint8(), Uint8(), Uint8()
                sdl2.SDL_SetSurfaceColorMod(sf, r, g, b)
                ret = sdl2.SDL_GetSurfaceColorMod(sf, byref(sr), byref(sg),
                                                     byref(sb))
                assert ret == 0
                assert (sr.value, sg.value, sb.value) == (r, g, b)
            sdl2.SDL_FreeSurface(sf)

    def test_SDL_LowerBlit(self):
        bpp = 32
        w, h = 10, 10
        # no alpha to prevent blending
        masks = (0xFF000000, 0x00FF0000, 0x0000FF00, 0x00000000)
        dest = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, masks[0], masks[1],
                                            masks[2], masks[3])
        pixelsize = h * dest.contents.pitch
        rowlen = dest.contents.pitch // 4

        sources = []
        for width, height in blitsizes:
            src = sdl2.SDL_CreateRGBSurface(0, width, height, bpp, masks[0],
                                               masks[1], masks[2], masks[3])
            sdl2.SDL_FillRect(src, None, 0xFFFFFFFF)  # fill with white
            sources.append(src)

        for src in sources:
            for pos in blitpositions:
                drect = pos.__copy__()
                sdl2.SDL_FillRect(dest, None, 0x0)  # fill with black
                sdl2.SDL_LowerBlit(src, src.contents.clip_rect, dest, drect)
                buf = cast(dest.contents.pixels, POINTER(Uint8 * pixelsize))
                pbuf = CTypesView(buf.contents, itemsize=1, objsize=pixelsize)
                iview = pbuf.to_uint32()
                pw = drect.x + drect.w
                ph = drect.y + drect.h
                e = "color mismatch at %d,%d for %s: %d != %d"
                for y in range(dest.contents.h):
                    for x in range(dest.contents.w):
                        col = iview[y * rowlen + x]
                        if y >= drect.y and y < ph and x >= drect.x and x < pw:
                            assert col == 0xFFFFFFFF, \
                                   e % (y, x, pos, col, 0xFFFFFFFF)
                        else:
                            assert col == 0x0, e % (y, x, pos, col, 0x0)

        while len(sources) > 0:
            sf = sources.pop()
            sdl2.SDL_FreeSurface(sf)
        sdl2.SDL_FreeSurface(dest)

    @pytest.mark.skip("not implemented")
    def test_SDL_LowerBlitScaled(self):
        pass

    def test_SDL_UpperBlit(self):
        bpp = 32
        w, h = 10, 10
        # no alpha to prevent blending
        masks = (0xFF000000, 0x00FF0000, 0x0000FF00, 0x00000000)
        dest = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, masks[0], masks[1],
                                            masks[2], masks[3])
        pixelsize = h * dest.contents.pitch
        rowlen = dest.contents.pitch // 4

        sources = []
        for width, height in blitsizes:
            src = sdl2.SDL_CreateRGBSurface(0, width, height, bpp, masks[0],
                                               masks[1], masks[2], masks[3])
            sdl2.SDL_FillRect(src, None, 0xFFFFFFFF)  # fill with white
            sources.append(src)

        for src in sources:
            for pos in blitpositions:
                drect = pos.__copy__()
                sdl2.SDL_FillRect(dest, None, 0x0)  # fill with black
                sdl2.SDL_UpperBlit(src, None, dest, drect)
                buf = cast(dest.contents.pixels, POINTER(Uint8 * pixelsize))
                pbuf = CTypesView(buf.contents, itemsize=1, objsize=pixelsize)
                iview = pbuf.to_uint32()
                pw = drect.x + drect.w
                ph = drect.y + drect.h
                e = "color mismatch at %d,%d for %s: %d != %d"
                for y in range(dest.contents.h):
                    for x in range(dest.contents.w):
                        col = iview[y * rowlen + x]
                        if y >= drect.y and y < ph and x >= drect.x and x < pw:
                            assert col == 0xFFFFFFFF, \
                                   e % (x, y, pos, col, 0xFFFFFFFF)
                        else:
                            assert col == 0x0, e % (x, y, pos, col, 0x0)

        while len(sources) > 0:
            sf = sources.pop()
            sdl2.SDL_FreeSurface(sf)
        sdl2.SDL_FreeSurface(dest)

    def test_SDL_BlitSurface(self):
        bpp = 32
        w, h = 10, 10
        # no alpha to prevent blending
        masks = (0xFF000000, 0x00FF0000, 0x0000FF00, 0x00000000)
        dest = sdl2.SDL_CreateRGBSurface(0, w, h, bpp, masks[0], masks[1],
                                            masks[2], masks[3])
        pixelsize = h * dest.contents.pitch
        rowlen = dest.contents.pitch // 4

        sources = []
        for width, height in blitsizes:
            src = sdl2.SDL_CreateRGBSurface(0, width, height, bpp, masks[0],
                                               masks[1], masks[2], masks[3])
            sdl2.SDL_FillRect(src, None, 0xFFFFFFFF)  # fill with white
            sources.append(src)

        for src in sources:
            for pos in blitpositions:
                drect = pos.__copy__()
                sdl2.SDL_FillRect(dest, None, 0x0)  # fill with black
                sdl2.SDL_BlitSurface(src, None, dest, drect)
                buf = cast(dest.contents.pixels, POINTER(Uint8 * pixelsize))
                pbuf = CTypesView(buf.contents, itemsize=1, objsize=pixelsize)
                iview = pbuf.to_uint32()
                pw = drect.x + drect.w
                ph = drect.y + drect.h
                e = "color mismatch at %d,%d for %s: %d != %d"
                for y in range(dest.contents.h):
                    for x in range(dest.contents.w):
                        col = iview[y * rowlen + x]
                        if y >= drect.y and y < ph and x >= drect.x and x < pw:
                            assert col == 0xFFFFFFFF, \
                                   e % (y, x, pos, col, 0xFFFFFFFF)
                        else:
                            assert col == 0x0, e % (y, x, pos, col, 0x0)

        while len(sources) > 0:
            sf = sources.pop()
            sdl2.SDL_FreeSurface(sf)
        sdl2.SDL_FreeSurface(dest)

    @pytest.mark.skip("not implemented")
    def test_SDL_UpperBlitScaled(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_SoftStretch(self):
        pass

    @pytest.mark.skip("not implemented")
    @pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
    def test_SDL_SoftStretchLinear(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_GetSetYUVConversionMode(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_GetYUVConversionModeForResolution(self):
        pass
