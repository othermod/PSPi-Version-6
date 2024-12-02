import pytest
from sdl2.surface import SDL_CreateRGBSurface, SDL_FreeSurface
from sdl2.rect import SDL_Rect
from sdl2.ext.draw import prepare_color, fill
from sdl2.ext.surface import _create_surface
from sdl2 import ext as sdl2ext

try:
    import numpy
    _HASNUMPY = True
except:
    _HASNUMPY = False


@pytest.mark.skipif(not _HASNUMPY, reason="Numpy not available")
def test_subsurface(with_sdl):
    # Initialize colour and surface/view
    sf = _create_surface((10, 10), fmt="RGBA32")
    WHITE = prepare_color((255, 255, 255), sf)

    # Test creation of subsurface from parent
    ssf = sdl2ext.subsurface(sf.contents, (0, 0, 5, 5))
    assert ssf.w == 5 and ssf.h == 5

    # Test shared pixels between surface
    fill(ssf, (255, 255, 255))
    view = sdl2ext.pixels3d(sf.contents, False)
    assert all(x == 255 for x in view[0][0][:3])
    assert all(x == 255 for x in view[4][4][:3])
    assert all(x == 0 for x in view[5][5][:3])
    SDL_FreeSurface(ssf)

    # Test creation of subsurface using an SDL_Rect
    subsurf_rect = SDL_Rect(2, 2, 6, 6)
    ssf = sdl2ext.subsurface(sf.contents, subsurf_rect)
    assert ssf.w == 6 and ssf.h == 6
    SDL_FreeSurface(ssf)

    # Test creation of subsurface using a surface pointer
    ssf = sdl2ext.subsurface(sf, (0, 0, 5, 5))
    assert ssf.w == 5 and ssf.h == 5
    SDL_FreeSurface(ssf)

    # Test exceptions on bad input
    with pytest.raises(TypeError):
        sdl2ext.subsurface(WHITE, (0, 0, 5, 5))
    with pytest.raises(TypeError):
        sdl2ext.subsurface(sf, (0, 0, 5))
    with pytest.raises(ValueError):
        sdl2ext.subsurface(sf, (0, 0, 50, 50))

    # Clean up after tests
    SDL_FreeSurface(sf)
