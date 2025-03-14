import sys
import pytest
from sdl2.surface import SDL_CreateRGBSurface, SDL_FreeSurface
from sdl2.rect import SDL_Rect
from sdl2.error import SDL_GetError
from sdl2.ext.color import Color, COLOR
from sdl2.ext.surface import _create_surface
from sdl2 import ext as sdl2ext

try:
    import numpy
    _HASNUMPY = True
except:
    _HASNUMPY = False


@pytest.fixture
def testsurf(with_sdl):
    sf = _create_surface((10, 10), fmt="RGBA32")
    assert SDL_GetError() == b""
    yield sf
    SDL_FreeSurface(sf)


@pytest.mark.skipif(not _HASNUMPY, reason="pixels3d requires numpy module")
def test_fill(testsurf):
    # Initialize colour and surface/view
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    sf = testsurf
    view = sdl2ext.pixels3d(sf.contents, False)

    # Test with no provided fill area
    sdl2ext.fill(sf.contents, WHITE, None)
    assert all(x == 255 for x in view[0][0][:3])
    assert all(x == 255 for x in view[-1][-1][:3])

    # Test with SDL_Rect fill area
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    r = SDL_Rect(0, 0, 5, 5)
    sdl2ext.fill(sf.contents, WHITE, r)
    assert all(x == 255 for x in view[0][0][:3])
    assert all(x == 255 for x in view[4][4][:3])
    assert all(x == 0 for x in view[-1][-1][:3])

    # Test with tuple fill area
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    r = (5, 5, 5, 5)
    sdl2ext.fill(sf.contents, WHITE, r)
    assert all(x == 0 for x in view[4][4][:3])
    assert all(x == 255 for x in view[5][5][:3])
    assert all(x == 255 for x in view[-1][-1][:3])

    # Test with multiple fill areas
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    rects = [(0, 0, 10, 5), SDL_Rect(0, 0, 3, 10), (7, 7, 3, 10)]
    sdl2ext.fill(sf.contents, WHITE, rects)
    assert all(x == 255 for x in view[0][0][:3])
    assert all(x == 255 for x in view[0][-1][:3])
    assert all(x == 255 for x in view[-1][-1][:3])
    assert all(x == 0 for x in view[-1][4][:3])

    # Test exception on bad input
    with pytest.raises(ValueError):
        sdl2ext.fill(sf.contents, WHITE, (1, 2, 3))

@pytest.mark.skipif(not _HASNUMPY, reason="pixels3d requires numpy module")
def test_line(testsurf):
    # Initialize colour and surface/view
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    sf = testsurf
    view = sdl2ext.pixels3d(sf.contents, False)

    # Test with a single straight line
    sdl2ext.line(sf.contents, WHITE, (0, 0, 11, 0))
    assert all(x == 255 for x in view[0][0][:3])
    assert all(x == 255 for x in view[0][-1][:3])
    assert all(x == 0 for x in view[1][0][:3])

    # Test specifying line width
    sdl2ext.line(sf.contents, WHITE, (0, 5, 11, 5), width=4)
    assert all(x == 255 for x in view[3][0][:3])
    assert all(x == 255 for x in view[6][-1][:3])
    assert all(x == 0 for x in view[2][0][:3])

    # Test with a single diagonal line
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    sdl2ext.line(sf.contents, WHITE, (1, 1, 9, 9))
    assert all(x == 255 for x in view[2][2][:3])
    assert all(x == 255 for x in view[3][3][:3])
    assert all(x == 0 for x in view[4][6][:3])

    # Test with multiple lines
    lines = [(0, 0, 0, 10), (0, 0, 10, 0), (0, 0, 10, 10)]
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    sdl2ext.line(sf.contents, WHITE, lines)
    assert all(x == 255 for x in view[0][-1][:3])
    assert all(x == 255 for x in view[-1][0][:3])
    assert all(x == 255 for x in view[-1][-1][:3])
    assert all(x == 0 for x in view[1][5][:3])

    # Test with multiple lines (old weird method)
    lines = (0, 0, 0, 10, 0, 0, 10, 0, 0, 0, 10, 10)
    sdl2ext.fill(sf.contents, BLACK, None)  # reset surface
    sdl2ext.line(sf.contents, WHITE, lines)
    assert all(x == 255 for x in view[0][-1][:3])
    assert all(x == 255 for x in view[-1][0][:3])
    assert all(x == 255 for x in view[-1][-1][:3])
    assert all(x == 0 for x in view[1][5][:3])

    # Test surfaces with nonstandard bpp values
    fmts = ["RGB332", "RGBA4444"]
    for f in fmts:
        sf2 = _create_surface((10, 10), fmt=f)
        sdl2ext.line(sf2.contents, WHITE, (1, 1, 9, 9))
        SDL_FreeSurface(sf2)

    # Test exception on bad input
    with pytest.raises(ValueError):
        sdl2ext.line(sf.contents, WHITE, (1, 2, 3))

def test_prepare_color(with_sdl):
    rcolors = (
        Color(0, 0, 0, 0),
        Color(255, 255, 255, 255),
        Color(8, 55, 110, 220),
    )
    icolors = (
        0x00000000,
        0xFFFFFFFF,
        0xAABBCCDD,
    )
    scolors = (
        "#000",
        "#FFF",
        "#AABBCCDD",
    )
    sf = _create_surface((10, 10), fmt="RGBA8888")
    for color in rcolors:
        c = sdl2ext.prepare_color(color, sf)
        assert c == int(color)
    for color in icolors:
        c = sdl2ext.prepare_color(color, sf)
        cc = COLOR(color)
        assert c == int(cc)
    for color in scolors:
        c = sdl2ext.prepare_color(color, sf)
        cc = COLOR(color)
        assert c == int(cc)
    SDL_FreeSurface(sf)