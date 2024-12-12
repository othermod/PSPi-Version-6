import sys
from ctypes import c_int, byref
import pytest
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_VIDEO
from sdl2 import video, error

macos = sys.platform == "darwin"


# TODO: Add more complete tests with pyobjc

@pytest.mark.xfail(reason="Metal not supported on all macs")
@pytest.mark.skipif(sdl2.dll.version < 2012 or not macos, reason="not available")
def test_SDL_Metal_CreateDestroyView(with_sdl):
    flags = video.SDL_WINDOW_HIDDEN | video.SDL_WINDOW_METAL
    window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10, flags)
    assert isinstance(window.contents, video.SDL_Window)
    view = sdl2.SDL_Metal_CreateView(window)
    err = error.SDL_GetError()
    if len(err):
        print("Metal Error: '{0}'".format(err.decode('utf-8')))
    assert view  # Verify pointer is not null
    sdl2.SDL_Metal_DestroyView(view)
    video.SDL_DestroyWindow(window)

@pytest.mark.xfail(reason="Metal not supported on all macs")
@pytest.mark.skipif(sdl2.dll.version < 2014 or not macos, reason="not available")
def test_SDL_Metal_GetLayer(with_sdl):
    flags = video.SDL_WINDOW_HIDDEN | video.SDL_WINDOW_METAL
    window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10, flags)
    assert isinstance(window.contents, video.SDL_Window)
    view = sdl2.SDL_Metal_CreateView(window)
    assert view  # Verify pointer is not null
    layer = sdl2.SDL_Metal_GetLayer(view)
    assert layer  # Verify pointer is not null
    sdl2.SDL_Metal_DestroyView(view)
    video.SDL_DestroyWindow(window)

@pytest.mark.xfail(reason="Metal not supported on all macs")
@pytest.mark.skipif(sdl2.dll.version < 2014 or not macos, reason="not available")
def test_SDL_Metal_GetDrawableSize(with_sdl):
    flags = video.SDL_WINDOW_HIDDEN | video.SDL_WINDOW_METAL
    window = video.SDL_CreateWindow(b"Test", 10, 10, 10, 10, flags)
    assert isinstance(window.contents, video.SDL_Window)
    view = sdl2.SDL_Metal_CreateView(window)
    assert view  # Verify pointer is not null
    w, h = c_int(0), c_int(0)
    sdl2.SDL_Metal_GetDrawableSize(window, byref(w), byref(h))
    assert w.value == 10 and h.value == 10
    sdl2.SDL_Metal_DestroyView(view)
    video.SDL_DestroyWindow(window)
