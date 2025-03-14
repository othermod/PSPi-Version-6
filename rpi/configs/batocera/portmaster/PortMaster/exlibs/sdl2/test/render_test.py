import sys
import copy
import pytest
import ctypes
from ctypes import byref, POINTER, c_int, c_float, sizeof
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_EVERYTHING, SDL_GetError
import itertools
from sdl2.stdinc import Uint8, Uint32, SDL_TRUE, SDL_FALSE
from sdl2.rect import SDL_FPoint
from sdl2.pixels import SDL_Color
from sdl2 import video, surface, pixels, blendmode, rect
from sdl2.ext.compat import byteify, stringify
from sdl2.ext.pixelaccess import PixelView

# TODO: Write tests for more functions

def _create_window(pos, size, flags=video.SDL_WINDOW_HIDDEN):
    # Convenience function to create renderer and window for tests
    sdl2.SDL_ClearError()
    window = video.SDL_CreateWindow(
        b"Test", pos[0], pos[1], size[0], size[1], video.SDL_WINDOW_HIDDEN
    )
    if not isinstance(window.contents, video.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(window.contents, video.SDL_Window)
    sdl2.SDL_ClearError()
    return window

def _get_renderflags():
    flags = sdl2.SDL_RENDERER_ACCELERATED
    if video.SDL_GetCurrentVideoDriver() == b"dummy":
        flags = sdl2.SDL_RENDERER_SOFTWARE
    return flags

@pytest.fixture(scope="module")
def supported_renderers(with_sdl):
    supported = []
    flags = _get_renderflags()
    for i in range(sdl2.SDL_GetNumRenderDrivers()):
        window = _create_window((30, 30), (100, 100))
        try:
            renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        except OSError:
            renderer = None
        if (renderer and renderer.contents):
            supported.append(i)
            sdl2.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)
    if not len(supported):
        raise RuntimeError("Unable to create a renderer with any backend")
    sdl2.SDL_ClearError()
    yield supported

@pytest.fixture
def testsurf(with_sdl):
    # Create a solid black surface for tests
    sf = surface.SDL_CreateRGBSurface(
        0, 100, 100, 32, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF
    )
    assert SDL_GetError() == b""
    pixfmt = sf.contents.format.contents
    fill = pixels.SDL_MapRGBA(pixfmt, 0, 0, 0, 255)
    surface.SDL_FillRect(sf, None, fill)
    assert SDL_GetError() == b""
    yield sf
    surface.SDL_FreeSurface(sf)

@pytest.fixture
def sw_renderer(testsurf):
    renderer = sdl2.SDL_CreateSoftwareRenderer(testsurf)
    assert SDL_GetError() == b""
    assert isinstance(renderer.contents, sdl2.SDL_Renderer)
    yield (renderer, testsurf)
    sdl2.SDL_DestroyRenderer(renderer)

@pytest.fixture
def with_renderer(with_sdl):
    flags = _get_renderflags()
    sdl2.SDL_ClearError()
    window = video.SDL_CreateWindow(
        b"Test", 30, 30, 100, 100, video.SDL_WINDOW_HIDDEN
    )
    if not isinstance(window.contents, sdl2.SDL_Window):
        assert sdl2.SDL_GetError() == b""
        assert isinstance(window.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    renderer = sdl2.SDL_CreateRenderer(window, -1, flags)
    assert SDL_GetError() == b""
    yield (renderer, window)
    sdl2.SDL_DestroyRenderer(renderer)
    video.SDL_DestroyWindow(window)

@pytest.fixture
def texture(with_renderer):
    renderer, win = with_renderer
    fmt = pixels.SDL_PIXELFORMAT_ARGB8888
    access = sdl2.SDL_TEXTUREACCESS_STREAMING
    tx = sdl2.SDL_CreateTexture(renderer, fmt, access, 16, 16)
    assert SDL_GetError() == b""
    assert isinstance(tx.contents, sdl2.SDL_Texture)
    yield tx
    sdl2.SDL_DestroyTexture(tx)


# Test structs and classes

def test_SDL_RendererInfo():
    # Tested extensively in SDL_GetRenderDriverInfo
    info = sdl2.SDL_RendererInfo()
    assert isinstance(info, sdl2.SDL_RendererInfo)

def test_SDL_Renderer():
    val = sdl2.SDL_Renderer()
    assert isinstance(val, sdl2.SDL_Renderer)

def test_SDL_Texture():
    val = sdl2.SDL_Texture()
    assert isinstance(val, sdl2.SDL_Texture)


class TestSDLVertex(object):
    __tags__ = ["sdl"]

    def test_init(self):
        # Test creating an SDL vertex without any args
        vtx = sdl2.SDL_Vertex()
        assert type(vtx.position) == rect.SDL_FPoint
        assert type(vtx.color) == pixels.SDL_Color
        assert type(vtx.tex_coord) == rect.SDL_FPoint

        # Test creating a vertex with a custom position and color
        pos = rect.SDL_FPoint(20, 30)
        col = pixels.SDL_Color(255, 0, 0, 255)
        vtx2 = sdl2.SDL_Vertex(pos, col)
        assert vtx2.position.x == 20 and vtx2.position.y == 30
        assert vtx2.color.r == 255 and vtx2.color.g == 0

        # Test creating an SDL vertex using Python types
        vtx3 = sdl2.SDL_Vertex([15, 25], [128, 127, 126], [5, 5])
        assert vtx3.position.x == 15 and vtx3.position.y == 25
        assert vtx3.color.r == 128 and vtx3.color.g == 127
        assert vtx3.color.a == 255
        assert vtx3.tex_coord.x == 5

        # Test exceptions on bad input
        with pytest.raises(ValueError):
            sdl2.SDL_Vertex(10)
        with pytest.raises(ValueError):
            sdl2.SDL_Vertex(color="red")

    def test_repr(self):
        vtx = sdl2.SDL_Vertex([1.5, 4], [0, 0, 0, 255])
        assert repr(vtx) == "SDL_Vertex(x=1.5, y=4.0, color=[0, 0, 0, 255])"

    def test_copy(self):
        vtx = sdl2.SDL_Vertex([15, 25], [128, 127, 126], [5, 5])
        vtx2 = copy.copy(vtx)
        assert vtx.position == vtx2.position
        assert vtx.color == vtx2.color
        assert vtx.tex_coord == vtx2.tex_coord
        # Make sure editing the new copy doesn't affect the original
        vtx2.position.x = 7
        vtx2.color.r = 200
        vtx2.tex_coord.y = 7
        assert vtx.position != vtx2.position
        assert vtx.color != vtx2.color
        assert vtx.tex_coord != vtx2.tex_coord


# Test SDL2 renderer bindings

def test_SDL_GetNumRenderDrivers(with_sdl):
    val = sdl2.SDL_GetNumRenderDrivers()
    assert val >= 1

def test_SDL_GetRenderDriverInfo(with_sdl):
    renderers = []
    errs = []
    pxformats = {}
    drivers = sdl2.SDL_GetNumRenderDrivers()
    for x in range(drivers):
        sdl2.SDL_ClearError()
        info = sdl2.SDL_RendererInfo()
        ret = sdl2.SDL_GetRenderDriverInfo(x, info)
        if ret != 0:
            err = stringify(sdl2.SDL_GetError())
            errs.append("Renderer {0} error: {1}".format(x, err))
            continue
        rname = stringify(info.name)
        renderers.append(rname)
        pxformats[rname] = []
        for i in range(info.num_texture_formats):
            fmt_name = pixels.SDL_GetPixelFormatName(info.texture_formats[i])
            pxformats[rname].append(stringify(fmt_name).split("_")[-1])
    assert len(renderers)
    assert "software" in renderers
    print("Render drivers supported by current SDL2 binary:")
    print(renderers)
    print("\nTexture formats supported by each renderer:")
    for rname in renderers:
        print(rname)
        print(" - " + " ".join(pxformats[rname]))

def test_SDL_CreateWindowAndRenderer(with_sdl):
    window = POINTER(video.SDL_Window)()
    renderer = POINTER(sdl2.SDL_Renderer)()
    ret = sdl2.SDL_CreateWindowAndRenderer(
        10, 10, video.SDL_WINDOW_HIDDEN, byref(window), byref(renderer)
    )
    sdl2.SDL_DestroyRenderer(renderer)
    video.SDL_DestroyWindow(window)
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0

def test_SDL_CreateDestroyRenderer(supported_renderers):
    flags = _get_renderflags()
    errs = {}
    rcount = sdl2.SDL_GetNumRenderDrivers()
    for i in range(rcount):
        window = _create_window((30, 30), (100, 100))
        try:
            renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        except OSError:
            renderer = None
        if (renderer and renderer.contents):
            assert isinstance(renderer.contents, sdl2.SDL_Renderer)
            sdl2.SDL_DestroyRenderer(renderer)
        else:
            name = "Renderer {0}".format(i)
            errs[name] = stringify(sdl2.SDL_GetError())
        video.SDL_DestroyWindow(window)
    assert rcount > len(errs.keys()) # Make sure at least one working renderer

def test_SDL_CreateSoftwareRenderer(with_sdl):
    sf = surface.SDL_CreateRGBSurface(
        0, 100, 100, 32, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF
    )
    renderer = sdl2.SDL_CreateSoftwareRenderer(sf)
    assert SDL_GetError() == b""
    assert isinstance(renderer.contents, sdl2.SDL_Renderer)
    sdl2.SDL_DestroyRenderer(renderer)
    surface.SDL_FreeSurface(sf)

def test_SDL_GetRenderer(supported_renderers):
    flags = _get_renderflags()
    usable = 0
    for i in supported_renderers:
        window = _create_window((30, 30), (100, 100))
        renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        if (renderer and renderer.contents):
            usable += 1
            ren = sdl2.SDL_GetRenderer(window)
            assert SDL_GetError() == b""
            assert isinstance(ren.contents, sdl2.SDL_Renderer)
            sdl2.SDL_DestroyRenderer(renderer)
            assert not sdl2.SDL_GetRenderer(window)
        video.SDL_DestroyWindow(window)
    assert usable > 0

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_RenderGetWindow(supported_renderers):
    flags = _get_renderflags()
    for i in supported_renderers:
        window = _create_window((30, 30), (100, 100))
        renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        if (renderer and renderer.contents):
            win = sdl2.SDL_RenderGetWindow(renderer)
            assert SDL_GetError() == b""
            assert isinstance(win.contents, sdl2.SDL_Window)
            assert sdl2.SDL_GetWindowID(window) == sdl2.SDL_GetWindowID(win)
            sdl2.SDL_DestroyRenderer(renderer)
            assert not sdl2.SDL_GetRenderer(win)
        video.SDL_DestroyWindow(window)


def test_SDL_GetRendererInfo(with_sdl):
    renderers = []
    max_sizes = {}
    errs = []
    flags = _get_renderflags()
    rcount = sdl2.SDL_GetNumRenderDrivers()
    for i in range(rcount):
        sdl2.SDL_ClearError()
        window = _create_window((30, 30), (100, 100))
        try:
            renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        except OSError:
            renderer = None
        if not (renderer and renderer.contents):
            err = stringify(sdl2.SDL_GetError())
            errs.append("Unable to create renderer {0}: {1}".format(i, err))
            video.SDL_DestroyWindow(window)
            continue
        assert isinstance(renderer.contents, sdl2.SDL_Renderer)
        info = sdl2.SDL_RendererInfo()
        ret = sdl2.SDL_GetRendererInfo(renderer, byref(info))
        if ret == 0:
            rname = stringify(info.name)
            max_size = (info.max_texture_width, info.max_texture_height)
            renderers.append(rname)
            max_sizes[rname] = max_size
        else:
            err = stringify(sdl2.SDL_GetError())
            errs.append("Renderer {0} error: {1}".format(i, err))
        sdl2.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)
    assert len(renderers)
    assert "software" in renderers
    print("Render drivers loadable on the current system:")
    for rname in renderers:
        w, h = max_sizes[rname]
        print(" - " + rname + " (max texture size: {0}x{1})".format(w, h))

@pytest.mark.skip("not implemented")
def test_SDL_GetRendererOutputSize(self):
    pass

def test_SDL_CreateDestroyTexture(with_renderer):
    renderer, win = with_renderer
    formats = (
        pixels.SDL_PIXELFORMAT_ARGB8888,
        pixels.SDL_PIXELFORMAT_RGB555,
        pixels.SDL_PIXELFORMAT_RGBA4444,
        pixels.SDL_PIXELFORMAT_RGBA8888,
        pixels.SDL_PIXELFORMAT_ARGB2101010,
        pixels.SDL_PIXELFORMAT_YUY2,
    )
    access = (
        sdl2.SDL_TEXTUREACCESS_STATIC,
        sdl2.SDL_TEXTUREACCESS_STREAMING,
        sdl2.SDL_TEXTUREACCESS_TARGET,
    )
    sizes = [(4, 4), (7, 7), (64, 32), (256, 256), (512, 512)]
    for fmt in formats:
        for acc in access:
            for w, h in sizes:
                tx = sdl2.SDL_CreateTexture(renderer, fmt, acc, w, h)
                assert SDL_GetError() == b""
                assert isinstance(tx.contents, sdl2.SDL_Texture)
                sdl2.SDL_DestroyTexture(tx)
    # Test SDL error on bad input
    sdl2.SDL_CreateTexture(
        renderer, pixels.SDL_PIXELFORMAT_RGB555, 1, -8, 8
    )
    assert len(SDL_GetError()) > 0

def test_SDL_CreateTextureFromSurface(with_renderer, testsurf):
    renderer, win = with_renderer
    tx = sdl2.SDL_CreateTextureFromSurface(renderer, testsurf)
    if sdl2.dll.version != 2008: # Weird non-fatal colorkey error on 2.0.8
        assert SDL_GetError() == b"" 
    assert isinstance(tx.contents, sdl2.SDL_Texture)
    sdl2.SDL_DestroyTexture(tx)

def test_SDL_QueryTexture(with_renderer):
    renderer, win = with_renderer
    formats = (
        pixels.SDL_PIXELFORMAT_ARGB8888,
        pixels.SDL_PIXELFORMAT_RGB555,
        pixels.SDL_PIXELFORMAT_RGBA4444,
        pixels.SDL_PIXELFORMAT_RGBA8888,
        pixels.SDL_PIXELFORMAT_ARGB2101010,
        pixels.SDL_PIXELFORMAT_YUY2,
    )
    access = (
        sdl2.SDL_TEXTUREACCESS_STATIC,
        sdl2.SDL_TEXTUREACCESS_STREAMING,
        sdl2.SDL_TEXTUREACCESS_TARGET,
    )
    sizes = [(4, 4), (7, 7), (64, 32), (256, 256), (512, 512)]
    for fmt in formats:
        for acc in access:
            for w, h in sizes:
                tx = sdl2.SDL_CreateTexture(renderer, fmt, acc, w, h)
                assert isinstance(tx.contents, sdl2.SDL_Texture)
                txf, txa, txw, txh = Uint32(0), c_int(0), c_int(0), c_int(0)
                ret = sdl2.SDL_QueryTexture(
                    tx, byref(txf), byref(txa), byref(txw), byref(txh)
                )
                assert SDL_GetError() == b""
                assert ret == 0
                assert txf.value == fmt
                assert txa.value == acc
                assert txw.value == w
                assert txh.value == h
                sdl2.SDL_DestroyTexture(tx)

def test_SDL_GetSetTextureColorMod(texture):
    colors = [
        (16, 22, 185),
        (32, 64, 128),
        (64, 32, 128),
        (64, 32, 255),
        (255, 32, 128),
        (255, 255, 255),
        (128, 128, 128),
        (0, 0, 0),
    ]
    for r, g, b in colors:
        ret = sdl2.SDL_SetTextureColorMod(texture, r, g, b)
        assert SDL_GetError() == b""
        assert ret == 0
        tr, tg, tb = Uint8(0), Uint8(0), Uint8(0)
        ret = sdl2.SDL_GetTextureColorMod(
            texture, byref(tr), byref(tg), byref(tb)
        )
        assert SDL_GetError() == b""
        assert ret == 0
        assert (tr.value, tg.value, tb.value) == (r, g, b)

def test_SDL_GetSetTextureAlphaMod(texture):
    for alpha in range(0, 255, 7):
        ret = sdl2.SDL_SetTextureAlphaMod(texture, alpha)
        assert SDL_GetError() == b""
        assert ret == 0
        talpha = Uint8(0)
        ret = sdl2.SDL_GetTextureAlphaMod(texture, byref(talpha))
        assert SDL_GetError() == b""
        assert ret == 0
        assert talpha.value == alpha

def test_SDL_GetSetTextureBlendMode(texture):
    modes = (
        blendmode.SDL_BLENDMODE_NONE,
        blendmode.SDL_BLENDMODE_ADD,
        blendmode.SDL_BLENDMODE_BLEND,
        blendmode.SDL_BLENDMODE_MOD,
    )
    for mode in modes:
        ret = sdl2.SDL_SetTextureBlendMode(texture, mode)
        assert SDL_GetError() == b""
        assert ret == 0
        tmode = blendmode.SDL_BlendMode()
        ret = sdl2.SDL_GetTextureBlendMode(texture, byref(tmode))
        assert SDL_GetError() == b""
        assert ret == 0
        assert tmode.value == mode

@pytest.mark.skipif(sdl2.dll.version < 2012, reason="not available")
def test_SDL_GetSetTextureScaleMode(texture):
    modes = (
        sdl2.SDL_ScaleModeNearest,
        sdl2.SDL_ScaleModeLinear,
        sdl2.SDL_ScaleModeBest,
    )
    for mode in modes:
        ret = sdl2.SDL_SetTextureScaleMode(texture, mode)
        assert SDL_GetError() == b""
        assert ret == 0
        tmode = sdl2.SDL_ScaleMode()
        ret = sdl2.SDL_GetTextureScaleMode(texture, byref(tmode))
        assert SDL_GetError() == b""
        assert ret == 0
        assert tmode.value == mode

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_GetSetTextureUserData(texture):
    # Create some user data and add it to the texture
    dat_raw = ctypes.c_char_p(b"hello!")
    dat = ctypes.cast(dat_raw, ctypes.c_void_p)
    ret = sdl2.SDL_SetTextureUserData(texture, dat)
    assert SDL_GetError() == b""
    assert ret == 0
    # Try retrieving the user data
    dat_ptr = sdl2.SDL_GetTextureUserData(texture)
    assert SDL_GetError() == b""
    assert dat_ptr != None
    dat_out = ctypes.cast(dat_ptr, ctypes.c_char_p)
    assert dat_raw.value == dat_out.value

@pytest.mark.skip("not implemented")
def test_SDL_UpdateTexture(texture):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_UpdateYUVTexture(with_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_UpdateNVTexture(with_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_LockUnlockTexture(texture):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2012, reason="not available")
def test_SDL_LockTextureToSurface(texture):
    pass

def test_SDL_RenderTargetSupported(supported_renderers):
    flags = _get_renderflags()
    usable = 0
    for i in supported_renderers:
        window = _create_window((30, 30), (100, 100))
        renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        if (renderer and renderer.contents):
            usable += 1
            assert isinstance(renderer.contents, sdl2.SDL_Renderer)
            val = sdl2.SDL_RenderTargetSupported(renderer)
            assert SDL_GetError() == b""
            assert val in (SDL_TRUE, SDL_FALSE)
            sdl2.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)
    assert usable > 0

def test_SDL_GetSetRenderTarget(supported_renderers):
    # First, determine which renderers support render targets
    flags = _get_renderflags()
    usable = 0
    supports_targets = []
    for i in supported_renderers:
        window = _create_window((30, 30), (100, 100))
        renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        if (renderer and renderer.contents):
            usable += 1
            assert isinstance(renderer.contents, sdl2.SDL_Renderer)
            if sdl2.SDL_RenderTargetSupported(renderer) == SDL_TRUE:
                supports_targets.append(i)
            sdl2.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)
    assert usable > 0
    if len(supports_targets) == 0:
        pytest.skip("No available renderer supports targets")

    # For renderers that support render targets, try setting/getting one
    pixfmt = pixels.SDL_PIXELFORMAT_ARGB8888
    for i in supports_targets:
        window = _create_window((30, 30), (100, 100))
        renderer = sdl2.SDL_CreateRenderer(window, i, flags)
        # Try setting a texture as the render target
        tex = sdl2.SDL_CreateTexture(
            renderer, pixfmt, sdl2.SDL_TEXTUREACCESS_TARGET, 10, 10
        )
        ret = sdl2.SDL_SetRenderTarget(renderer, tex)
        assert SDL_GetError() == b""
        assert ret == 0
        tgt = sdl2.SDL_GetRenderTarget(renderer)
        assert SDL_GetError() == b""
        assert isinstance(tgt.contents, sdl2.SDL_Texture)
        # Try setting NULL as the render target (resets target to window)
        ret = sdl2.SDL_SetRenderTarget(renderer, None)
        assert ret == 0
        assert not sdl2.SDL_GetRenderTarget(renderer)
        # Clean up before the next renderer
        sdl2.SDL_DestroyTexture(tex)
        sdl2.SDL_DestroyRenderer(renderer)
        video.SDL_DestroyWindow(window)

def test_SDL_RenderGetSetLogicalSize(sw_renderer):
    renderer, sf = sw_renderer
    BLACK_RGBA = 0x000000FF
    GREEN_RGBA = 0x00FF00FF

    # Try setting the logical size to 1/10 of normal
    ret = sdl2.SDL_RenderSetLogicalSize(renderer, 10, 10)
    assert SDL_GetError() == b""
    assert ret == 0
    lw, lh = c_int(0), c_int(0)
    sdl2.SDL_RenderGetLogicalSize(renderer, byref(lw), byref(lh))
    assert [lw.value, lh.value] == [10, 10]

    # Try drawing a single pixel to the renderer and see if fills 10x10
    ret = sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255)
    assert ret == 0
    sdl2.SDL_RenderDrawPoint(renderer, 1, 1)
    view = PixelView(sf)
    assert view[1][1] == BLACK_RGBA
    assert view[10][10] == GREEN_RGBA
    assert view[19][19] == GREEN_RGBA
    assert view[9][9] == BLACK_RGBA
    assert view[20][20] == BLACK_RGBA

    # Reset the logical size back to its original values and try drawing again
    ret = sdl2.SDL_RenderSetLogicalSize(renderer, 0, 0)
    assert ret == 0
    sdl2.SDL_RenderDrawPoint(renderer, 1, 1)
    assert view[1][1] == GREEN_RGBA
    assert view[0][0] == BLACK_RGBA
    assert view[2][2] == BLACK_RGBA
    del view

def test_SDL_RenderGetSetViewport(sw_renderer):
    renderer, sf = sw_renderer
    rects = (
        rect.SDL_Rect(1, 1, 1, 1),
        rect.SDL_Rect(0, 0, 10, 10),
        rect.SDL_Rect(3, 3, 5, 5),
        rect.SDL_Rect(-5, -5, 10, 10),
        rect.SDL_Rect(10, 10, 20, 20),
        rect.SDL_Rect(50, 50, 20, 30),
        rect.SDL_Rect(0, -10, 10, 10),
    )
    # First, try setting viewport to whole window
    ret = sdl2.SDL_RenderSetViewport(renderer, None)
    assert SDL_GetError() == b""
    assert ret == 0
    vport = rect.SDL_Rect()
    sdl2.SDL_RenderGetViewport(renderer, byref(vport))
    assert vport == rect.SDL_Rect(0, 0, 100, 100)
    # Then, try setting it to different sizes
    for r in rects:
        ret = sdl2.SDL_RenderSetViewport(renderer, r)
        assert SDL_GetError() == b""
        assert ret == 0
        sdl2.SDL_RenderGetViewport(renderer, byref(vport))
        assert vport == r

@pytest.mark.skip("not implemented")
def test_SDL_RenderGetSetClipRect(with_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderIsClipEnabled(with_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderGetSetScale(with_renderer):
    pass

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_RenderWindowToLogical(with_renderer):
    renderer, win = with_renderer
    wx, wy = (c_int(0), c_int(0))  # window coords
    lx, ly = (c_float(0), c_float(0))  # renderer coords
    # Test without resizing
    sdl2.SDL_RenderWindowToLogical(renderer, 50, 50, byref(lx), byref(ly))
    assert lx.value == 50
    assert ly.value == 50
    sdl2.SDL_RenderLogicalToWindow(renderer, 50, 50, byref(wx), byref(wy))
    assert wx.value == 50
    assert wy.value == 50
    # Set custom scaling on the renderer
    ret = sdl2.SDL_RenderSetScale(renderer, 2.0, 0.5)
    assert SDL_GetError() == b""
    assert ret == 0
    # Test again after resizing
    sdl2.SDL_RenderWindowToLogical(renderer, 50, 50, byref(lx), byref(ly))
    assert lx.value == 25
    assert ly.value == 100
    sdl2.SDL_RenderLogicalToWindow(renderer, 50, 50, byref(wx), byref(wy))
    assert wx.value == 100
    assert wy.value == 25

def test_SDL_RenderGetSetIntegerScale(with_renderer):
    renderer, win = with_renderer
    assert sdl2.SDL_RenderGetIntegerScale(renderer) == SDL_FALSE
    assert sdl2.SDL_RenderSetIntegerScale(renderer, SDL_FALSE) == 0
    assert sdl2.SDL_RenderGetIntegerScale(renderer) == SDL_FALSE
    assert sdl2.SDL_RenderSetIntegerScale(renderer, SDL_TRUE) == 0
    assert sdl2.SDL_RenderGetIntegerScale(renderer) == SDL_TRUE
    assert sdl2.SDL_RenderSetIntegerScale(renderer, SDL_FALSE) == 0
    assert sdl2.SDL_RenderGetIntegerScale(renderer) == SDL_FALSE

def test_SDL_GetSetRenderDrawColor(with_renderer):
    renderer, win = with_renderer
    colors = (
        (16, 22, 185, 217),
        (32, 64, 128, 255),
        (64, 32, 128, 255),
        (255, 32, 64, 128),
        (255, 255, 255, 255),
        (128, 128, 128, 255),
        (0, 0, 0, 0),
    )
    for r, g, b, a in colors:
        ret = sdl2.SDL_SetRenderDrawColor(renderer, r, g, b, a)
        assert SDL_GetError() == b""
        assert ret == 0
        rr, rg, rb, ra = Uint8(0), Uint8(0), Uint8(0), Uint8(0)
        ret = sdl2.SDL_GetRenderDrawColor(
            renderer, byref(rr), byref(rg), byref(rb), byref(ra)
        )
        assert ret == 0
        assert [v.value for v in (rr, rg, rb, ra)] == [r, g, b, a]

def test_SDL_GetSetRenderDrawBlendMode(with_renderer):
    renderer, win = with_renderer
    modes = [
        blendmode.SDL_BLENDMODE_NONE,
        blendmode.SDL_BLENDMODE_ADD,
        blendmode.SDL_BLENDMODE_BLEND,
        blendmode.SDL_BLENDMODE_MOD,
    ]
    for mode in modes:
        ret = sdl2.SDL_SetRenderDrawBlendMode(renderer, mode)
        assert SDL_GetError() == b""
        assert ret == 0
        bmode = blendmode.SDL_BlendMode()
        ret = sdl2.SDL_GetRenderDrawBlendMode(renderer, byref(bmode))
        assert ret == 0
        assert bmode.value == mode

def test_SDL_RenderClear(sw_renderer):
    renderer, sf = sw_renderer
    # Create a pixel view for the target surface and verify it's black
    view = PixelView(sf)
    assert view[0][0] == 0x000000FF
    # Set renderer draw color to white and then clear the renderer
    ret = sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
    assert ret == 0
    ret = sdl2.SDL_RenderClear(renderer)
    assert ret == 0
    # Check whether the target surface is now white
    assert view[0][0] == 0xFFFFFFFF
    del view

def test_SDL_RenderDrawPoint(sw_renderer):
    renderer, sf = sw_renderer
    points = (
        (1, 1), (4, 6), (10, 10), (96, 92),
        (4, 22), (57, 88), (45, 15)
    )
    r, g, b, a = 0xAA, 0xBB, 0xCC, 0xDD
    color = pixels.SDL_MapRGBA(sf.contents.format, r, g, b, a)
    ret = sdl2.SDL_SetRenderDrawColor(renderer, r, g, b, a)
    assert ret == 0
    for x, y in points:
        ret = sdl2.SDL_RenderDrawPoint(renderer, x, y)
        assert ret == 0
    sdl2.SDL_RenderPresent(renderer)
    # Check whether the points were actually drawn
    view = PixelView(sf)
    for x, y in points:
        # NOTE: Assumes no points are adjacent or on surface edge 
        assert hex(view[y][x]) == hex(color)
        assert hex(view[y+1][x+1]) != hex(color)
        assert hex(view[y-1][x-1]) != hex(color)
    del view

@pytest.mark.skip("not implemented")
def test_SDL_RenderDrawPoints(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderDrawLine(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderDrawLines(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderDrawRect(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderDrawRects(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderFillRect(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderFillRects(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderCopy(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderCopyEx(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawPointF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawPointsF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawLineF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawLinesF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawRectF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderDrawRectsF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderFillRectF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderFillRectsF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderCopyF(sw_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderCopyExF(sw_renderer):
    pass

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_RenderGeometry(sw_renderer):
    renderer, target = sw_renderer
    # Create vertices for rendering
    RED = (255, 0, 0, 255)
    vertices = [
        sdl2.SDL_Vertex((0, 0), RED),
        sdl2.SDL_Vertex((0, 50), RED),
        sdl2.SDL_Vertex((50, 50), RED)
    ]
    # Try rendering the vertices
    vtx = (sdl2.SDL_Vertex * len(vertices))(*vertices)
    ret = sdl2.SDL_RenderGeometry(
        renderer, None, vtx, len(vertices), None, 0
    )
    assert SDL_GetError() == b""
    assert ret == 0
    # TODO: Actually check the surface for the rendered triangle

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_RenderGeometryRaw(sw_renderer):
    renderer, target = sw_renderer
    # Create vertices for rendering
    RED = SDL_Color(255, 0, 0, 255)
    points = [0, 0, 0, 50, 50, 50]
    colors = [RED, RED, RED]
    tex_coords = [0, 0, 0, 0, 0, 0]
    # Convert vertices to ctypes-friendly format
    xy_size = sizeof(c_float) * 2
    col_size = sizeof(SDL_Color)
    xy = (c_float * len(points))(*points)
    col = (SDL_Color * len(colors))(*colors)
    uv = (c_float * len(tex_coords))(*tex_coords)
    # Try rendering the vertices
    ret = sdl2.SDL_RenderGeometryRaw(
        renderer, None,
        xy, xy_size,
        col, col_size,
        uv, xy_size,
        3, None, 0, 1
    )
    assert SDL_GetError() == b""
    assert ret == 0
    # Check the surface for the rendered triangle
    RED_RGBA = 0xFF0000FF
    BLACK_RGBA = 0x000000FF
    view = PixelView(target)
    assert view[25][5] == RED_RGBA
    assert view[99][99] == BLACK_RGBA
    del view

@pytest.mark.skip("not implemented")
def test_SDL_RenderReadPixels(with_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_RenderPresent(with_renderer):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_RenderFlush(with_renderer):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_GL_BindTexture(with_sdl):
    # NOTE: Needs OpenGL renderer
    pass

@pytest.mark.skip("not implemented")
def test_SDL_GL_UnbindTexture(with_sdl):
    # NOTE: Needs OpenGL renderer
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2008, reason="not available")
def test_SDL_RendererGetMetalLayer(with_renderer):
    # NOTE: Needs metal renderer
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2008, reason="not available")
def test_SDL_RendererGetMetalCommandEncoder(with_renderer):
    # NOTE: Needs metal renderer
    pass

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_RenderSetVSync(with_renderer):
    renderer, win = with_renderer
    # Not super thorough, but hard to test more extensively
    ret = sdl2.SDL_RenderSetVSync(renderer, 1)
    assert ret <= 0
    ret = sdl2.SDL_RenderSetVSync(renderer, 0)
    assert ret <= 0
