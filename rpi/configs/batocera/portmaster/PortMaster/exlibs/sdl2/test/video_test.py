import os
import sys
import ctypes
from ctypes.util import find_library
from ctypes import c_int, c_ubyte, c_float, byref, cast, POINTER, py_object
import pytest
import sdl2
from sdl2.stdinc import SDL_FALSE, SDL_TRUE, Uint16
from sdl2 import rect, pixels, surface, SDL_GetError
from .conftest import SKIP_ANNOYING

# Some tests don't work properly with some video drivers, so check the name
DRIVER_DUMMY = False
DRIVER_X11 = False
try:
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    driver_name = sdl2.SDL_GetCurrentVideoDriver()
    sdl2.SDL_Quit()
    DRIVER_DUMMY = driver_name == b"dummy"
    DRIVER_X11 = driver_name == b"x11"
except:
    pass

# Some tests don't work right on PyPy
is_pypy = hasattr(sys, "pypy_version_info")

if sys.version_info[0] >= 3:
    long = int

to_ctypes = lambda seq, dtype: (dtype * len(seq))(*seq)

def has_opengl_lib():
    for libname in("gl", "opengl", "opengl32"):
        path = find_library(libname)
        if path is not None:
            return True

def get_opengl_path():
    for libname in("gl", "opengl", "opengl32"):
        path = find_library(libname)
        if path is not None:
            return path

@pytest.fixture
def with_sdl_gl(with_sdl):
    ret = sdl2.SDL_GL_LoadLibrary(None)
    assert SDL_GetError() == b""
    assert ret == 0
    yield
    sdl2.SDL_GL_UnloadLibrary()

@pytest.fixture
def window(with_sdl):
    flag = sdl2.SDL_WINDOW_BORDERLESS
    w = sdl2.SDL_CreateWindow(b"Test", 10, 40, 12, 13, flag)
    if not isinstance(w.contents, sdl2.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(w.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    yield w
    sdl2.SDL_DestroyWindow(w)

@pytest.fixture
def decorated_window(with_sdl):
    flag = sdl2.SDL_WINDOW_RESIZABLE
    w = sdl2.SDL_CreateWindow(b"Test", 10, 40, 12, 13, flag)
    if not isinstance(w.contents, sdl2.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(w.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    yield w
    sdl2.SDL_DestroyWindow(w)

@pytest.fixture
def gl_window(with_sdl_gl):
    flag = sdl2.SDL_WINDOW_OPENGL
    w = sdl2.SDL_CreateWindow(b"OpenGL", 10, 40, 12, 13, flag)
    if not isinstance(w.contents, sdl2.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(w.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    ctx = sdl2.SDL_GL_CreateContext(w)
    assert SDL_GetError() == b""
    yield (w, ctx)
    sdl2.SDL_GL_DeleteContext(ctx)
    sdl2.SDL_DestroyWindow(w)

def _create_window(name, h, w, x, y, flags):
    window = sdl2.SDL_CreateWindow(name, h, w, x, y, flags)
    if not isinstance(window.contents, sdl2.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(window.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    return window

# Test custom macros

def test_SDL_WINDOWPOS_UNDEFINED_DISPLAY():
    undef_mask = sdl2.SDL_WINDOWPOS_UNDEFINED_MASK
    for x in range(0xFFFF):
        undef = sdl2.SDL_WINDOWPOS_UNDEFINED_DISPLAY(x)
        assert undef_mask | x == undef
        assert (undef & undef_mask) == undef_mask
        assert undef != sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(x)

def test_SDL_WINDOWPOS_ISUNDEFINED():
    assert sdl2.SDL_WINDOWPOS_ISUNDEFINED(sdl2.SDL_WINDOWPOS_UNDEFINED)
    assert not sdl2.SDL_WINDOWPOS_ISUNDEFINED(sdl2.SDL_WINDOWPOS_CENTERED)
    for x in range(0xFFFF):
        undef = sdl2.SDL_WINDOWPOS_UNDEFINED_DISPLAY(x)
        assert sdl2.SDL_WINDOWPOS_ISUNDEFINED(undef)

def test_SDL_WINDOWPOS_CENTERED_DISPLAY():
    centered_mask = sdl2.SDL_WINDOWPOS_CENTERED_MASK
    for x in range(0xFFFF):
        centered = sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(x)
        assert centered_mask | x == centered
        assert (centered & centered_mask) == centered_mask
        assert centered != sdl2.SDL_WINDOWPOS_UNDEFINED_DISPLAY(x)

def test_SDL_WINDOWPOS_ISCENTERED():
    assert sdl2.SDL_WINDOWPOS_ISCENTERED(sdl2.SDL_WINDOWPOS_CENTERED)
    assert not sdl2.SDL_WINDOWPOS_ISCENTERED(sdl2.SDL_WINDOWPOS_UNDEFINED)
    for x in range(0xFFFF):
        centered = sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(x)
        assert sdl2.SDL_WINDOWPOS_ISCENTERED(centered)


# Test structures and classes

def test_SDL_Window():
    window = sdl2.SDL_Window()
    assert isinstance(window, sdl2.SDL_Window)


class TestSDLDisplayMode(object):

    def test_init(self):
        mode = sdl2.SDL_DisplayMode()
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        fmt = sdl2.SDL_PIXELFORMAT_ARGB8888
        mode = sdl2.SDL_DisplayMode(fmt, 800, 600, 60)
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        assert mode.format == fmt
        assert mode.w == 800
        assert mode.h == 600
        assert mode.refresh_rate == 60
        # Test exceptions on bad input
        with pytest.raises(TypeError):
            sdl2.SDL_DisplayMode("Test")
        with pytest.raises(TypeError):
            sdl2.SDL_DisplayMode(10, 10.6, 10, 10)
        with pytest.raises(TypeError):
            sdl2.SDL_DisplayMode(10, 10, 10, None)

    def test___eq__(self):
        DMode = sdl2.SDL_DisplayMode
        assert DMode() == DMode()
        assert DMode(10, 0, 0, 0) == DMode(10, 0, 0, 0)
        assert DMode(10, 10, 0, 0) == DMode(10, 10, 0, 0)
        assert DMode(10, 10, 10, 0) == DMode(10, 10, 10, 0)
        assert DMode(10, 10, 10, 10) == DMode(10, 10, 10, 10)
        assert DMode(0, 10, 0, 0) == DMode(0, 10, 0, 0)
        assert DMode(0, 0, 10, 0) == DMode(0, 0, 10, 0)
        assert DMode(0, 0, 0, 10) == DMode(0, 0, 0, 10)

        assert not (DMode() == DMode(10, 0, 0, 0))
        assert not (DMode(10, 0, 0, 0) == DMode(0, 0, 0, 0))
        assert not (DMode(10, 0, 0, 0) == DMode(0, 10, 0, 0))
        assert not (DMode(10, 0, 0, 0) == DMode(0, 0, 10, 0))
        assert not (DMode(10, 0, 0, 0) == DMode(0, 0, 0, 10))

    def test___ne__(self):
        DMode = sdl2.SDL_DisplayMode
        assert not (DMode() != DMode())
        assert not (DMode(10, 0, 0, 0) != DMode(10, 0, 0, 0))
        assert not (DMode(10, 10, 0, 0) != DMode(10, 10, 0, 0))
        assert not (DMode(10, 10, 10, 0) != DMode(10, 10, 10, 0))
        assert not (DMode(10, 10, 10, 10) != DMode(10, 10, 10, 10))
        assert not (DMode(0, 10, 0, 0) != DMode(0, 10, 0, 0))
        assert not (DMode(0, 0, 10, 0) != DMode(0, 0, 10, 0))
        assert not (DMode(0, 0, 0, 10) != DMode(0, 0, 0, 10))

        assert DMode() != DMode(10, 0, 0, 0)
        assert DMode(10, 0, 0, 0) != DMode(0, 0, 0, 0)
        assert DMode(10, 0, 0, 0) != DMode(0, 10, 0, 0)
        assert DMode(10, 0, 0, 0) != DMode(0, 0, 10, 0)
        assert DMode(10, 0, 0, 0) != DMode(0, 0, 0, 10)


# Test module SDL functions

def test_SDL_VideoInitQuit():
    # Test with default driver
    assert sdl2.SDL_WasInit(0) & sdl2.SDL_INIT_VIDEO != sdl2.SDL_INIT_VIDEO
    ret = sdl2.SDL_VideoInit(None)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert sdl2.SDL_GetCurrentVideoDriver() # If initialized, should be string
    sdl2.SDL_VideoQuit()
    assert not sdl2.SDL_GetCurrentVideoDriver()
    # TODO: Test with string input (fails with b"dummy" for some reason?)

def test_SDL_GetNumVideoDrivers(with_sdl):
    numdrivers = sdl2.SDL_GetNumVideoDrivers()
    assert numdrivers >= 1

def test_SDL_GetVideoDriver(with_sdl):
    numdrivers = sdl2.SDL_GetNumVideoDrivers()
    for i in range(numdrivers):
        name = sdl2.SDL_GetVideoDriver(i)
        assert type(name) in (str, bytes)

def test_SDL_GetCurrentVideoDriver(with_sdl):
    curdriver = sdl2.SDL_GetCurrentVideoDriver()
    numdrivers = sdl2.SDL_GetNumVideoDrivers()
    drivers = []
    for i in range(numdrivers):
        drivers.append(sdl2.SDL_GetVideoDriver(i))
    assert curdriver in drivers

def test_SDL_GetNumVideoDisplays(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    assert numdisplays >= 1

def test_SDL_GetNumDisplayModes(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        modes = sdl2.SDL_GetNumDisplayModes(index)
        assert modes >= 1

def test_SDL_GetDisplayMode(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        modes = sdl2.SDL_GetNumDisplayModes(index)
        for mode in range(modes):
            dmode = sdl2.SDL_DisplayMode()
            ret = sdl2.SDL_GetDisplayMode(index, mode, byref(dmode))
            assert sdl2.SDL_GetError() == b""
            assert ret == 0
            if not DRIVER_DUMMY:
                assert dmode.w > 0
                assert dmode.h > 0

def test_SDL_GetCurrentDisplayMode(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        dmode = sdl2.SDL_DisplayMode()
        ret = sdl2.SDL_GetCurrentDisplayMode(index, byref(dmode))
        assert sdl2.SDL_GetError() == b""
        assert ret == 0
        assert dmode.w > 0
        assert dmode.h > 0

def test_SDL_GetDesktopDisplayMode(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        dmode = sdl2.SDL_DisplayMode()
        ret = sdl2.SDL_GetDesktopDisplayMode(index, byref(dmode))
        assert sdl2.SDL_GetError() == b""
        assert ret == 0
        assert dmode.w > 0
        assert dmode.h > 0

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GetClosestDisplayMode(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        dmode = sdl2.SDL_DisplayMode()
        ret = sdl2.SDL_GetCurrentDisplayMode(index, byref(dmode))
        assert sdl2.SDL_GetError() == b""
        assert ret == 0
        cmode = sdl2.SDL_DisplayMode(
            dmode.format, dmode.w - 1, dmode.h - 1, dmode.refresh_rate
        )
        closest = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetClosestDisplayMode(index, cmode, byref(closest))
        assert closest == dmode

def test_SDL_GetDisplayName(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        name = sdl2.SDL_GetDisplayName(index)
        assert type(name) in (str, bytes)

def test_SDL_GetDisplayBounds(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        bounds = rect.SDL_Rect()
        ret = sdl2.SDL_GetDisplayBounds(index, byref(bounds))
        assert sdl2.SDL_GetError() == b""
        assert ret == 0
        assert bounds.w > 0
        assert bounds.h > 0
        assert not rect.SDL_RectEmpty(bounds)

@pytest.mark.skipif(sdl2.dll.version < 2005, reason="not available")
def test_SDL_GetDisplayUsableBounds(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        bounds = rect.SDL_Rect()
        ret = sdl2.SDL_GetDisplayUsableBounds(index, byref(bounds))
        assert ret == 0
        assert not rect.SDL_RectEmpty(bounds)

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GetDisplayDPI(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        ddpi, hdpi, vdpi = c_float(0), c_float(0), c_float(0)
        ret = sdl2.SDL_GetDisplayDPI(
            index, byref(ddpi), byref(hdpi), byref(vdpi)
        )
        assert SDL_GetError() == b""
        assert ret == 0
        assert ddpi.value >= 96.0
        assert hdpi.value >= 96.0
        assert vdpi.value >= 96.0

@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_GetDisplayOrientation(with_sdl):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    for index in range(numdisplays):
        orientation = sdl2.SDL_GetDisplayOrientation(index)
        assert isinstance(orientation, int)
        assert orientation >= 0

def test_GetDisplayInfo(with_sdl):
    current = sdl2.SDL_GetCurrentVideoDriver().decode('utf-8')
    print("Available Video Drivers:")
    for i in range(sdl2.SDL_GetNumVideoDrivers()):
        name = sdl2.SDL_GetVideoDriver(i).decode('utf-8')
        if name == current:
            name += " (*)"
        print(" - " + name)
    print("")
    print("Detected Displays:")
    for i in range(sdl2.SDL_GetNumVideoDisplays()):
        name = sdl2.SDL_GetDisplayName(i).decode('utf-8')
        info = " - " + name
        dm = sdl2.SDL_DisplayMode()
        ret = sdl2.SDL_GetDesktopDisplayMode(i, byref(dm))
        if ret == 0:
            res = " ({0}x{1} @ {2}Hz)".format(dm.w, dm.h, dm.refresh_rate)
            info += res
        print(info)

def test_SDL_CreateDestroyWindow(with_sdl):
    flag = sdl2.SDL_WINDOW_BORDERLESS
    window = sdl2.SDL_CreateWindow(b"Test", 10, 40, 12, 13, flag)
    if not isinstance(window.contents, sdl2.SDL_Window):
        assert SDL_GetError() == b""
        assert isinstance(window.contents, sdl2.SDL_Window)
    sdl2.SDL_DestroyWindow(window)

@pytest.mark.skip("not implemented")
def test_SDL_CreateWindowFrom(with_sdl):
    # No obvious cross-platform way to test this
    pass

@pytest.mark.skipif(sdl2.dll.version < 2240, reason="not available")
def test_SDL_GetPointDisplayIndex(with_sdl):
    for index in range(sdl2.SDL_GetNumVideoDisplays()):
        bounds = rect.SDL_Rect()
        ret = sdl2.SDL_GetDisplayUsableBounds(index, byref(bounds))
        assert ret == 0
        p = sdl2.SDL_Point(bounds.x + 50, bounds.y + 50)
        assert sdl2.SDL_GetPointDisplayIndex(p) == index

@pytest.mark.skipif(sdl2.dll.version < 2240, reason="not available")
def test_SDL_GetRectDisplayIndex(with_sdl):
    for index in range(sdl2.SDL_GetNumVideoDisplays()):
        bounds = rect.SDL_Rect()
        ret = sdl2.SDL_GetDisplayUsableBounds(index, byref(bounds))
        assert ret == 0
        r = sdl2.SDL_Rect(bounds.x + 50, bounds.y + 50, 10, 10)
        assert sdl2.SDL_GetRectDisplayIndex(r) == index

def test_SDL_GetWindowDisplayIndex(window):
    numdisplays = sdl2.SDL_GetNumVideoDisplays()
    dindex = sdl2.SDL_GetWindowDisplayIndex(window)
    # Make sure display index is valid
    assert 0 <= dindex <= numdisplays

def test_SDL_GetWindowDisplayMode(window):
    # NOTE: Gets fullscreen mode of parent display, not size of window
    dmode = sdl2.SDL_DisplayMode()
    ret = sdl2.SDL_GetWindowDisplayMode(window, byref(dmode))
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0
    assert dmode.w > 0
    assert dmode.h > 0

def test_SDL_SetWindowDisplayMode(window):
    # NOTE: Sets the fullscreen mode of the window, so can't easily test
    # NOTE: If set mode not supported, will change to closest supported res
    dindex = sdl2.SDL_GetWindowDisplayIndex(window)
    dmode = sdl2.SDL_DisplayMode()
    ret = sdl2.SDL_GetCurrentDisplayMode(dindex, byref(dmode))
    assert ret == 0
    sdl2.SDL_SetWindowDisplayMode(window, dmode)
    wmode = sdl2.SDL_DisplayMode()
    ret = sdl2.SDL_GetWindowDisplayMode(window, byref(wmode))
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0
    assert dmode == wmode

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_GetWindowICCProfile(window):
    prof_size = ctypes.c_size_t(0)
    prof_ptr = sdl2.SDL_GetWindowICCProfile(window, byref(prof_size))
    # This function returns a void pointer to the loaded ICC profile, which
    # needs to be cast to bytes to be read. As per the ICC spec, bytes
    # 36 to 39 of the header should always be 'acsp' in ASCII.
    if prof_size.value > 0:
        prof = ctypes.cast(prof_ptr, ctypes.POINTER(c_ubyte))
        assert bytes(prof[36:40]) == b"acsp"

def test_SDL_GetWindowPixelFormat(window):
    fmt = sdl2.SDL_GetWindowPixelFormat(window)
    assert fmt in sdl2.ALL_PIXELFORMATS

def test_SDL_GetWindowID(window):
    assert sdl2.SDL_GetWindowID(window) >= 0

def test_SDL_GetWindowFromID(window):
    window2 = sdl2.SDL_GetWindowFromID(sdl2.SDL_GetWindowID(window))
    assert sdl2.SDL_GetWindowID(window) == sdl2.SDL_GetWindowID(window2)
    assert sdl2.SDL_GetWindowTitle(window) == sdl2.SDL_GetWindowTitle(window2)
    # Make sure sizes/positions are the same
    px1, py1, px2, py2 = c_int(0), c_int(0), c_int(0), c_int(0)
    sdl2.SDL_GetWindowPosition(window, byref(px1), byref(py1))
    sdl2.SDL_GetWindowPosition(window2, byref(px2), byref(py2))
    assert (px1.value, py1.value) == (px2.value, py2.value)
    sdl2.SDL_GetWindowSize(window, byref(px1), byref(py1))
    sdl2.SDL_GetWindowSize(window2, byref(px2), byref(py2))
    assert (px1.value, py1.value) == (px2.value, py2.value)

def test_SDL_GetWindowFlags(with_sdl):
    flags = (
        sdl2.SDL_WINDOW_BORDERLESS,
        sdl2.SDL_WINDOW_BORDERLESS | sdl2.SDL_WINDOW_HIDDEN,
        sdl2.SDL_WINDOW_RESIZABLE
    )
    for flag in flags:
        win = sdl2.SDL_CreateWindow(b"Test", 10, 10, 10, 10, flag)
        wflags = sdl2.SDL_GetWindowFlags(win)
        assert (wflags & flag) == flag
        sdl2.SDL_DestroyWindow(win)

def test_SDL_GetSetWindowTitle(window):
    assert sdl2.SDL_GetWindowTitle(window) == b"Test"
    sdl2.SDL_SetWindowTitle(window, b"Hello there")
    assert sdl2.SDL_GetWindowTitle(window) == b"Hello there"

def test_SDL_SetWindowIcon(window):
    sf = surface.SDL_CreateRGBSurface(
        0, 16, 16, 16, 0xF000, 0x0F00, 0x00F0, 0x000F
    )
    assert isinstance(sf.contents, surface.SDL_Surface)
    sdl2.SDL_SetWindowIcon(window, sf)
    assert SDL_GetError() == b""

@pytest.mark.xfail(is_pypy, reason="PyPy can't create proper py_object values")
def test_SDL_GetSetWindowData(window):
    values = {
        b"text": py_object("Teststring"),
        b"list": py_object([1, 2, "a", "b"]),
        b"tuple": py_object((1, 2, 3)),
    }
    for k, v in values.items():
        sdl2.SDL_SetWindowData(window, k, v)
        retval = sdl2.SDL_GetWindowData(window, k)
        assert retval.contents.value == v.value

@pytest.mark.xfail(DRIVER_X11, reason="Wonky with some window managers")
def test_SDL_GetSetWindowPosition(with_sdl):
    window = _create_window(b"Test", 10, 200, 10, 10, 0)
    px, py = c_int(0), c_int(0)
    sdl2.SDL_GetWindowPosition(window, byref(px), byref(py))
    assert (px.value, py.value) == (10, 200)
    sdl2.SDL_SetWindowPosition(window, 0, 150)
    sdl2.SDL_GetWindowPosition(window, byref(px), byref(py))
    assert (px.value, py.value) == (0, 150)
    sdl2.SDL_SetWindowPosition(window, 480, 320)
    sdl2.SDL_GetWindowPosition(window, byref(px), byref(py))
    assert (px.value, py.value) == (480, 320)
    sdl2.SDL_DestroyWindow(window)

def test_SDL_GetSetWindowSize(window):
    sx, sy = c_int(0), c_int(0)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (12, 13)
    sdl2.SDL_SetWindowSize(window, 1, 1)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (1, 1)
    sdl2.SDL_SetWindowSize(window, 480, 320)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (480, 320)
    # Test that negative sizes are ignored
    sdl2.SDL_SetWindowSize(window, -200, -10)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (480, 320)

@pytest.mark.skipif(sdl2.dll.version < 2260, reason="not available")
def test_SDL_GetWindowSizeInPixels(window):
    sx, sy = c_int(0), c_int(0)
    sxp, syp = c_int(0), c_int(0)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    sdl2.SDL_GetWindowSizeInPixels(window, byref(sxp), byref(syp))
    assert sxp.value >= sx.value
    assert syp.value >= sy.value

def test_SDL_GetWindowBordersSize(window, decorated_window):
    # Currently, only X11 and Windows video drivers support border size
    supports_borders = sdl2.SDL_GetCurrentVideoDriver() in [b"x11", b"windows"]
    # For a decorated window, make sure all borders are >= 0
    sdl2.SDL_ShowWindow(decorated_window)
    t, l, b, r = c_int(), c_int(), c_int(), c_int()
    ret = sdl2.SDL_GetWindowBordersSize(
       decorated_window, byref(t), byref(l), byref(b), byref(r)
    )
    values = [x.value for x in (t, l, b, r)]
    assert all([v >= 0 for v in values])
    if supports_borders:
        assert ret == 0
    # Test again with a borderless window & make sure borders are all 0
    sdl2.SDL_ShowWindow(window)
    ret = sdl2.SDL_GetWindowBordersSize(
        window, byref(t), byref(l), byref(b), byref(r)
    )
    values = [x.value for x in (t, l, b, r)]
    assert all([v == 0 for v in values])
    if supports_borders:
        assert ret == 0

def test_SDL_GetSetWindowMinimumSize(window):
    sx, sy = c_int(0), c_int(0)
    minx, miny = c_int(0), c_int(0)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (12, 13)
    # Set and verify the minimum window size
    sdl2.SDL_SetWindowMinimumSize(window, 10, 10)
    assert SDL_GetError() == b""
    sdl2.SDL_GetWindowMinimumSize(window, byref(minx), byref(miny))
    assert (minx.value, miny.value) == (10, 10)
    # Make sure window can't be set below its minimum size
    sdl2.SDL_SetWindowSize(window, 1, 1)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (10, 10)

def test_SDL_GetSetWindowMaximumSize(window):
    sx, sy = c_int(0), c_int(0)
    maxx, maxy = c_int(0), c_int(0)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (12, 13)
    # Set and verify the maximum window size
    sdl2.SDL_SetWindowMaximumSize(window, 32, 32)
    assert SDL_GetError() == b""
    sdl2.SDL_GetWindowMaximumSize(window, byref(maxx), byref(maxy))
    assert (maxx.value, maxy.value) == (32, 32)
    # Make sure window can't be set above its maximum size
    sdl2.SDL_SetWindowSize(window, 50, 50)
    sdl2.SDL_GetWindowSize(window, byref(sx), byref(sy))
    assert (sx.value, sy.value) == (32, 32)

def test_SDL_SetWindowBordered(window):
    border_flag = sdl2.SDL_WINDOW_BORDERLESS
    assert sdl2.SDL_GetWindowFlags(window) & border_flag == border_flag
    sdl2.SDL_SetWindowBordered(window, SDL_TRUE)
    if not DRIVER_DUMMY:
        assert not sdl2.SDL_GetWindowFlags(window) & border_flag == border_flag
        sdl2.SDL_SetWindowBordered(window, SDL_FALSE)
        assert sdl2.SDL_GetWindowFlags(window) & border_flag == border_flag

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_SetWindowResizable(window):
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & sdl2.SDL_WINDOW_RESIZABLE != sdl2.SDL_WINDOW_RESIZABLE
    sdl2.SDL_SetWindowResizable(window, SDL_TRUE)
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & sdl2.SDL_WINDOW_RESIZABLE == sdl2.SDL_WINDOW_RESIZABLE
    sdl2.SDL_SetWindowResizable(window, SDL_FALSE)
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & sdl2.SDL_WINDOW_RESIZABLE != sdl2.SDL_WINDOW_RESIZABLE

@pytest.mark.skip("Test doesn't work, may need to be interactive")
@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_SetWindowAlwaysOnTop(with_sdl):
    ON_TOP_FLAG = sdl2.SDL_WINDOW_ALWAYS_ON_TOP
    window = sdl2.SDL_CreateWindow(
        b"Always On Top", 10, 100, 10, 10, ON_TOP_FLAG
    )
    sdl2.SDL_ShowWindow(window)
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & ON_TOP_FLAG == ON_TOP_FLAG
    sdl2.SDL_SetWindowAlwaysOnTop(window, SDL_FALSE)
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & ON_TOP_FLAG != ON_TOP_FLAG
    sdl2.SDL_SetWindowAlwaysOnTop(window, SDL_TRUE)
    flags = sdl2.SDL_GetWindowFlags(window)
    assert flags & ON_TOP_FLAG == ON_TOP_FLAG
    sdl2.SDL_DestroyWindow(window)

def test_SDL_ShowHideWindow(window):
    shown_flag = sdl2.SDL_WINDOW_SHOWN
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowFlags(window) & shown_flag == shown_flag
    sdl2.SDL_HideWindow(window)
    assert not sdl2.SDL_GetWindowFlags(window) & shown_flag == shown_flag

def test_SDL_RaiseWindow(window):
    # NOTE: Doesn't set any flags, so can't test this super well
    sdl2.SDL_RaiseWindow(window)

@pytest.mark.skipif(SKIP_ANNOYING, reason="Skip unless requested")
def test_SDL_MaximizeWindow(decorated_window):
    shown_flag = sdl2.SDL_WINDOW_SHOWN
    max_flag = sdl2.SDL_WINDOW_MAXIMIZED
    window = decorated_window
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowFlags(window) & shown_flag == shown_flag
    assert not sdl2.SDL_GetWindowFlags(window) & max_flag == max_flag
    sdl2.SDL_MaximizeWindow(window)
    if not DRIVER_DUMMY:
        assert sdl2.SDL_GetWindowFlags(window) & max_flag == max_flag

@pytest.mark.skipif(SKIP_ANNOYING, reason="Skip unless requested")
def test_SDL_MinimizeRestoreWindow(decorated_window):
    shown_flag = sdl2.SDL_WINDOW_SHOWN
    min_flag = sdl2.SDL_WINDOW_MINIMIZED
    window = decorated_window
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowFlags(window) & shown_flag == shown_flag
    assert not sdl2.SDL_GetWindowFlags(window) & min_flag == min_flag
    sdl2.SDL_MinimizeWindow(window)
    if not (DRIVER_DUMMY or DRIVER_X11):
        assert sdl2.SDL_GetWindowFlags(window) & min_flag == min_flag
    sdl2.SDL_RestoreWindow(window)
    if not (DRIVER_DUMMY or DRIVER_X11):
        assert not sdl2.SDL_GetWindowFlags(window) & min_flag == min_flag

def test_SDL_SetWindowFullscreen(with_sdl):
    # TODO: Add non-hidden test once annoying test toggle implemented
    flags = (
        sdl2.SDL_WINDOW_BORDERLESS | sdl2.SDL_WINDOW_HIDDEN,
        sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_HIDDEN,
    )
    is_fullscreen = sdl2.SDL_WINDOW_FULLSCREEN
    for flag in flags:
        window = sdl2.SDL_CreateWindow(b"Test", 0, 0, 1024, 768, flag)
        sdl2.SDL_SetWindowFullscreen(window, True)
        flags = sdl2.SDL_GetWindowFlags(window)
        assert flags & is_fullscreen == is_fullscreen
        sdl2.SDL_SetWindowFullscreen(window, False)
        flags = sdl2.SDL_GetWindowFlags(window)
        assert flags & is_fullscreen != is_fullscreen
        sdl2.SDL_DestroyWindow(window)

def test_SDL_GetWindowSurface(window):
    sf = sdl2.SDL_GetWindowSurface(window)
    assert SDL_GetError() == b""
    assert isinstance(sf.contents, surface.SDL_Surface)

def test_SDL_UpdateWindowSurface(window):
    sf = sdl2.SDL_GetWindowSurface(window)
    assert isinstance(sf.contents, surface.SDL_Surface)
    ret = sdl2.SDL_UpdateWindowSurface(window)
    assert SDL_GetError() == b""
    assert ret == 0

def test_SDL_UpdateWindowSurfaceRects(window):
    sf = sdl2.SDL_GetWindowSurface(window)
    assert isinstance(sf.contents, surface.SDL_Surface)
    rectlist = (rect.SDL_Rect * 4)(
        rect.SDL_Rect(0, 0, 0, 0),
        rect.SDL_Rect(10, 10, 10, 10),
        rect.SDL_Rect(0, 0, 5, 4),
        rect.SDL_Rect(-5, -5, 6, 2)
    )
    rect_ptr = cast(rectlist, POINTER(rect.SDL_Rect))
    ret = sdl2.SDL_UpdateWindowSurfaceRects(window, rect_ptr, 4)
    assert SDL_GetError() == b""
    assert ret == 0

@pytest.mark.skip("Can't set window grab for some reason")
def test_SDL_GetSetWindowGrab(decorated_window):
    window = decorated_window
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowGrab(window) == SDL_FALSE
    sdl2.SDL_SetWindowGrab(window, SDL_TRUE)
    assert sdl2.SDL_GetWindowGrab(window) == SDL_TRUE
    sdl2.SDL_SetWindowGrab(window, SDL_FALSE)
    assert sdl2.SDL_GetWindowGrab(window) == SDL_FALSE

@pytest.mark.skip("Can't set window grab for some reason")
@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_GetSetWindowKeyboardGrab(decorated_window):
    window = decorated_window
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowKeyboardGrab(window) == SDL_FALSE
    sdl2.SDL_SetWindowKeyboardGrab(window, SDL_TRUE)
    assert sdl2.SDL_GetWindowKeyboardGrab(window) == SDL_TRUE
    sdl2.SDL_SetWindowKeyboardGrab(window, SDL_FALSE)
    assert sdl2.SDL_GetWindowKeyboardGrab(window) == SDL_FALSE

@pytest.mark.skip("Can't set window grab for some reason")
@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_GetSetWindowMouseGrab(decorated_window):
    window = decorated_window
    sdl2.SDL_ShowWindow(window)
    assert sdl2.SDL_GetWindowMouseGrab(window) == SDL_FALSE
    sdl2.SDL_SetWindowMouseGrab(window, SDL_TRUE)
    assert sdl2.SDL_GetWindowMouseGrab(window) == SDL_TRUE
    sdl2.SDL_SetWindowMouseGrab(window, SDL_FALSE)
    assert sdl2.SDL_GetWindowMouseGrab(window) == SDL_FALSE

@pytest.mark.skip("not implemented")
def test_SDL_GetGrabbedWindow(window):
    # NOTE: Should implement this once the above tests are fixed
    pass

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_GetSetWindowMouseRect(with_sdl):
    flags = sdl2.SDL_WINDOW_BORDERLESS
    bounds_in = rect.SDL_Rect(0, 0, 100, 50)
    window = _create_window(b"Test", 200, 200, 200, 200, flags)
    # Try setting a mouse boundary
    ret = sdl2.SDL_SetWindowMouseRect(window, byref(bounds_in))
    assert SDL_GetError() == b""
    assert ret == 0
    bounds_out = sdl2.SDL_GetWindowMouseRect(window)
    assert bounds_out != None
    assert bounds_in == bounds_out.contents
    # Try removing the boundary
    ret = sdl2.SDL_SetWindowMouseRect(window, None)
    assert SDL_GetError() == b""
    assert ret == 0
    bounds_out = sdl2.SDL_GetWindowMouseRect(window)
    assert not bounds_out  # bounds_out should be null pointer
    sdl2.SDL_DestroyWindow(window)

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GetSetWindowBrightness(window):
    orig = sdl2.SDL_GetWindowBrightness(window)
    assert isinstance(orig, float)
    assert orig >= 0
    # Go from 0.0, 0.1 ... to 1.0
    gammas = (x * 0.1 for x in range(0, 10))
    count = 0
    for b in gammas:
        ret = sdl2.SDL_SetWindowBrightness(window, b)
        if ret == 0:
            val = sdl2.SDL_GetWindowBrightness(window)
            assert round(abs(val-b), 7) == 0
            count += 1
    assert count > 0

def test_SDL_GetSetWindowOpacity(window):
    opacity = c_float(0)
    ret = sdl2.SDL_GetWindowOpacity(window, byref(opacity))
    assert ret == 0
    assert opacity.value == 1.0
    if not DRIVER_DUMMY:
        ret = sdl2.SDL_SetWindowOpacity(window, 0.5)
        assert SDL_GetError() == b""
        assert ret == 0
        ret = sdl2.SDL_GetWindowOpacity(window, byref(opacity))
        assert SDL_GetError() == b""
        assert ret == 0
        assert opacity.value == 0.5

@pytest.mark.skipif(sdl2.dll.version < 2005, reason="not available")
def test_SDL_SetWindowModalFor(window, decorated_window):
    # NOTE: Only supported on X11
    ret = sdl2.SDL_SetWindowModalFor(window, decorated_window)
    if sdl2.SDL_GetCurrentVideoDriver() == b"x11":
        assert SDL_GetError() == b""
        assert ret == 0

@pytest.mark.skipif(sdl2.dll.version < 2005, reason="not available")
def test_SDL_SetWindowInputFocus(window):
    # NOTE: Only supported on X11 and Wayland
    ret = sdl2.SDL_SetWindowInputFocus(window)
    if sdl2.SDL_GetCurrentVideoDriver() in [b"x11", b"wayland"]:
        assert SDL_GetError() == b""
        assert ret == 0

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GetSetWindowGammaRamp(window):
    vals = (Uint16 * 256)()
    pixels.SDL_CalculateGammaRamp(0.5, vals)
    ret = sdl2.SDL_SetWindowGammaRamp(window, vals, vals, vals)
    assert SDL_GetError() == b""
    assert ret == 0
    r = (Uint16 * 256)()
    g = (Uint16 * 256)()
    b = (Uint16 * 256)()
    ret = sdl2.SDL_GetWindowGammaRamp(window, r, g, b)
    assert SDL_GetError() == b""
    assert ret == 0
    for i in range(len(vals)):
        assert r[i] == vals[i]
        assert g[i] == vals[i]
        assert b[i] == vals[i]

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2004, reason="not available")
def test_SDL_SetWindowHitTest(self):
    # NOTE: This sets a callback that's triggered when you mouse over certain
    # regions of a window. Pretty sure this can't be tested non-interactively.
    pass

@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_FlashWindow(window):
    # NOTE: Not the most comprehensive test, but it does test the basic bindings
    ret = sdl2.SDL_FlashWindow(window, sdl2.SDL_FLASH_BRIEFLY)
    if not DRIVER_DUMMY:
        assert SDL_GetError() == b""
        assert ret == 0

def test_screensaver(with_sdl):
    sdl2.SDL_EnableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_TRUE
    sdl2.SDL_EnableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_TRUE
    sdl2.SDL_DisableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_FALSE
    sdl2.SDL_DisableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_FALSE
    sdl2.SDL_EnableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_TRUE
    sdl2.SDL_DisableScreenSaver()
    assert sdl2.SDL_IsScreenSaverEnabled() == SDL_FALSE


# Test SDL OpenGL functions

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_LoadUnloadLibrary(with_sdl):
    # TODO: Test whether other GL functions work after GL is unloaded
    # (unloading doesn't always work right on macOS for some reason)
    ret = sdl2.SDL_GL_LoadLibrary(None)
    assert SDL_GetError() == b""
    assert ret == 0
    sdl2.SDL_GL_UnloadLibrary()
    # Try loading a library from a path
    if has_opengl_lib():
        fpath = get_opengl_path().encode("utf-8")
        ret = sdl2.SDL_GL_LoadLibrary(fpath)
        assert SDL_GetError() == b""
        assert ret == 0
        sdl2.SDL_GL_UnloadLibrary()

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_CreateDeleteContext(with_sdl_gl):
    window = _create_window(
        b"OpenGL", 10, 40, 32, 24, sdl2.SDL_WINDOW_OPENGL
    )
    ctx = sdl2.SDL_GL_CreateContext(window)
    assert SDL_GetError() == b""
    sdl2.SDL_GL_DeleteContext(ctx)
    ctx = sdl2.SDL_GL_CreateContext(window)
    assert SDL_GetError() == b""
    sdl2.SDL_GL_DeleteContext(ctx)
    sdl2.SDL_DestroyWindow(window)

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_GetProcAddress(gl_window):
    procaddr = sdl2.SDL_GL_GetProcAddress(b"glGetString")
    assert SDL_GetError() == b""
    assert procaddr is not None and int(procaddr) != 0

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_ExtensionSupported(gl_window):
    assert sdl2.SDL_GL_ExtensionSupported(b"GL_EXT_bgra")
    assert SDL_GetError() == b""

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_GetSetResetAttribute(with_sdl_gl):
    # Create a context and get its bit depth
    window = _create_window(
        b"OpenGL", 10, 40, 12, 13, sdl2.SDL_WINDOW_OPENGL
    )
    ctx = sdl2.SDL_GL_CreateContext(window)
    bufstate = c_int(0)
    ret = sdl2.SDL_GL_GetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, byref(bufstate))
    sdl2.SDL_GL_DeleteContext(ctx)
    sdl2.SDL_DestroyWindow(window)
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0
    sdl2.SDL_ClearError()
    # Try setting a different GL bit depth
    new_bufstate = 0 if bufstate.value == 1 else 1
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, new_bufstate)
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0
    sdl2.SDL_ClearError()
    # Create a new context to see if it's using the new bit depth 
    window = _create_window(
        b"OpenGL", 10, 40, 12, 13, sdl2.SDL_WINDOW_OPENGL
    )
    ctx = sdl2.SDL_GL_CreateContext(window)
    val = c_int(0)
    ret = sdl2.SDL_GL_GetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, byref(val))
    sdl2.SDL_GL_DeleteContext(ctx)
    sdl2.SDL_DestroyWindow(window)
    if ret != 0:
        assert SDL_GetError() == b""
        assert ret == 0
    sdl2.SDL_ClearError()
    assert bufstate.value != val.value
    assert val.value == new_bufstate
    # Try resetting the context and see if it goes back to the original depth
    sdl2.SDL_GL_ResetAttributes()
    window = _create_window(
        b"OpenGL", 10, 40, 12, 13, sdl2.SDL_WINDOW_OPENGL
    )
    ctx = sdl2.SDL_GL_CreateContext(window)
    val = c_int(0)
    ret = sdl2.SDL_GL_GetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, byref(val))
    sdl2.SDL_GL_DeleteContext(ctx)
    sdl2.SDL_DestroyWindow(window)
    assert bufstate.value == val.value

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_MakeCurrent(gl_window):
    window, ctx = gl_window
    ret = sdl2.SDL_GL_MakeCurrent(window, ctx)
    assert SDL_GetError() == b""
    assert ret == 0

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_GetSetSwapInterval(gl_window):
    window, ctx = gl_window
    ret = sdl2.SDL_GL_MakeCurrent(window, ctx)
    assert SDL_GetError() == b""
    assert ret == 0
    # Try enabling/disabling OpenGL vsync
    for value in [0, 1]:
        ret = sdl2.SDL_GL_SetSwapInterval(value)
        if ret == 0:
            assert sdl2.SDL_GL_GetSwapInterval() == value

@pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
def test_SDL_GL_SwapWindow(gl_window):
    window, ctx = gl_window
    ret = sdl2.SDL_GL_MakeCurrent(window, ctx)
    assert SDL_GetError() == b""
    assert ret == 0
    sdl2.SDL_GL_SwapWindow(window)
    sdl2.SDL_GL_SwapWindow(window)
    sdl2.SDL_GL_SwapWindow(window)
    assert SDL_GetError() == b""
