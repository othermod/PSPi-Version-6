import pytest
import sdl2
from sdl2 import ext as sdl2ext

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


def test_get_displays(with_sdl):
    n_displays = sdl2.SDL_GetNumVideoDisplays()
    displays = sdl2ext.get_displays()
    assert len(displays) == n_displays
    assert isinstance(displays[0], sdl2ext.DisplayInfo)


class TestExtDisplayInfo(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        n_displays = sdl2.SDL_GetNumVideoDisplays()
        for i in range(n_displays):
            d = sdl2ext.DisplayInfo(i)
            assert len(d.name) > 0
            assert len(d.modes) > 0
            assert isinstance(d.modes[0], sdl2.SDL_DisplayMode)
        # Test exception on bad index
        with pytest.raises(ValueError):
            sdl2ext.DisplayInfo(n_displays + 1)

    @pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
    def test_dpi(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        assert d.dpi > 0

    def test_current_mode(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        mode = d.current_mode
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        assert mode.w > 0 and mode.h > 0

    def test_desktop_mode(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        mode = d.desktop_mode
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        assert mode.w > 0 and mode.h > 0

    def test_bounds(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        bounds = d.bounds
        assert isinstance(bounds, sdl2.SDL_Rect)
        assert bounds.w > 0 and bounds.h > 0

    @pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
    def test_closest_mode(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        current = d.current_mode
        mode = d.closest_mode(current.w - 1, current.h - 1)
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        assert mode == current
        mode = d.closest_mode(current.w - 1, current.h - 1, 60)
        assert isinstance(mode, sdl2.SDL_DisplayMode)
        assert mode.w == current.w and mode.h == current.h

    @pytest.mark.skipif(DRIVER_DUMMY, reason="Doesn't work with dummy driver")
    def test_has_mode(self, with_sdl):
        d = sdl2ext.DisplayInfo(0)
        current = d.current_mode
        assert d.has_mode(current.w, current.h)
        assert not d.has_mode(1234, 567)
        assert not d.has_mode(1234, 567, hz=60)
