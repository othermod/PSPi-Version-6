import os
import sys
import pytest
from sdl2 import ext as sdl2ext
from sdl2.ext import color
from sdl2.ext.surface import _create_surface
from sdl2 import surface, pixels

try:
    import numpy
    _HASNUMPY = True
except:
    _HASNUMPY = False


colors = {
    'red': color.Color(255, 0, 0, 255),
    'blue': color.Color(0, 0, 255, 255),
    'black': color.Color(0, 0, 0, 255),
    'white': color.Color(255, 255, 255, 255)
}

@pytest.fixture
def imgsurf(with_sdl):
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    testfile = os.path.join(parent_dir, "resources", "surfacetest.bmp")
    sf = surface.SDL_LoadBMP(testfile.encode("utf-8"))
    yield sf
    surface.SDL_FreeSurface(sf)

@pytest.fixture
def rgbasurf(imgsurf):
    rgba = pixels.SDL_PIXELFORMAT_RGBA32
    rgbasurf = surface.SDL_ConvertSurfaceFormat(imgsurf.contents, rgba, 0)
    yield rgbasurf
    surface.SDL_FreeSurface(rgbasurf)

@pytest.fixture
def surf_rgb24(with_sdl):
    grey = [128, 128, 128, 255]
    sf = _create_surface((16, 16), grey, fmt="RGB24")
    yield sf
    surface.SDL_FreeSurface(sf)


def test_PixelView(imgsurf, surf_rgb24):
    # Open pixel view for test image
    pxview = sdl2ext.PixelView(imgsurf.contents)

    # Test different coordinates on surface
    assert color.ARGB(pxview[0][0]) == colors['red']
    assert color.ARGB(pxview[0][16]) == colors['blue']
    assert color.ARGB(pxview[0][31]) == colors['white']
    assert color.ARGB(pxview[31][31]) == colors['black']

    # Try modifying surface, test if changes persist 
    pxview[31][0] = 0xFF808080 # medium grey in ARGB
    pxview2 = sdl2ext.PixelView(imgsurf)
    assert pxview2[31][0] == 0xFF808080

    # Test that negative indexing works as expected
    assert color.ARGB(pxview[0][-1]) == colors['white']
    assert color.ARGB(pxview[-1][-1]) == colors['black']

    # Test out-of-bounds exceptions for indices
    with pytest.raises(IndexError):
        pxview[32][32]

    # Test exception on use with a 3 byte per pixel surface
    with pytest.raises(RuntimeError):
        sdl2ext.PixelView(surf_rgb24)


@pytest.mark.skipif(not _HASNUMPY, reason="numpy module is not supported")
def test_pixels2d(imgsurf, surf_rgb24):
    # Open pixels2d view for test image
    nparray = sdl2ext.pixels2d(imgsurf.contents, transpose=False)
    assert nparray.shape == (32, 32)

    # Test different coordinates on surface
    assert color.ARGB(nparray[0][0]) == colors['red']
    assert color.ARGB(nparray[0][16]) == colors['blue']
    assert color.ARGB(nparray[0][31]) == colors['white']
    assert color.ARGB(nparray[31][31]) == colors['black']

    # Try modifying surface, test if changes persist 
    nparray[31][0] = 0xFF808080 # medium grey in ARGB
    nparray2 = sdl2ext.pixels2d(imgsurf, transpose=False)
    assert nparray2[31][0] == 0xFF808080

    # Test exception on use with a 3 byte per pixel surface
    with pytest.raises(RuntimeError):
        sdl2ext.pixels2d(surf_rgb24)


@pytest.mark.skipif(not _HASNUMPY, reason="numpy module is not supported")
def test_pixels3d(rgbasurf, surf_rgb24):
    # Create view and test different coordinates on surface
    nparray = sdl2ext.pixels3d(rgbasurf.contents, transpose=False)
    assert nparray.shape == (32, 32, 4)
    assert color.Color(*nparray[0][0]) == colors['red']
    assert color.Color(*nparray[0][16]) == colors['blue']
    assert color.Color(*nparray[0][31]) == colors['white']
    assert color.Color(*nparray[31][31]) == colors['black']

    # Create transposed view and test different coordinates on surface
    nptrans = sdl2ext.pixels3d(rgbasurf.contents, transpose=True)
    assert nptrans.shape == (32, 32, 4)
    assert color.Color(*nptrans[0][0]) == colors['red']
    assert color.Color(*nptrans[16][0]) == colors['blue']
    assert color.Color(*nptrans[31][0]) == colors['white']
    assert color.Color(*nptrans[31][31]) == colors['black']

    # Try modifying surface, test if changes persist
    grey = [128, 128, 128, 255]
    nparray[31][0][:] = grey
    nparray2 = sdl2ext.pixels3d(rgbasurf, transpose=False)
    assert color.Color(*nparray2[31][0]) == color.Color(*grey)

    # Test usage with a 3 bytes-per-pixel surface 
    nparray_rgb24 = sdl2ext.pixels3d(surf_rgb24)
    assert color.Color(*nparray_rgb24[0][0]) == color.Color(*grey)


@pytest.mark.skipif(not _HASNUMPY, reason="numpy module is not supported")
def test_surface_to_ndarray(imgsurf, rgbasurf):
    # Create a 2D ndarray from the surface & test different coordinates
    arr_2d = sdl2ext.surface_to_ndarray(imgsurf.contents, ndim=2)
    assert color.ARGB(arr_2d[0][0]) == colors['red']
    assert color.ARGB(arr_2d[0][16]) == colors['blue']
    assert color.ARGB(arr_2d[0][31]) == colors['white']
    assert color.ARGB(arr_2d[31][31]) == colors['black']

    # Create a 3D ndarray from the surface & test different coordinates
    arr_3d = sdl2ext.surface_to_ndarray(rgbasurf.contents)
    assert arr_3d.shape == (32, 32, 4)
    assert color.Color(*arr_3d[0][0]) == colors['red']
    assert color.Color(*arr_3d[0][16]) == colors['blue']
    assert color.Color(*arr_3d[0][31]) == colors['white']
    assert color.Color(*arr_3d[31][31]) == colors['black']

    # Try modifying surface, make sure changes don't persist
    grey = [128, 128, 128, 255]
    arr_3d[31][0][:] = grey
    arr_view = sdl2ext.pixels3d(rgbasurf, transpose=False)
    assert color.Color(*arr_view[31][0]) != color.Color(*grey)
