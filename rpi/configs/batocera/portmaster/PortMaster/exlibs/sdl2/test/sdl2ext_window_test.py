import sys
import pytest
import sdl2
from sdl2 import SDL_WINDOW_SHOWN
from sdl2 import ext as sdl2ext
from sdl2 import surface, video
from .conftest import SKIP_ANNOYING

# Some tests don't work properly with some video drivers, so check the name
DRIVER_DUMMY = False
DRIVER_X11 = False
try:
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    driver_name = video.SDL_GetCurrentVideoDriver()
    sdl2.SDL_Quit()
    DRIVER_DUMMY = driver_name == b"dummy"
    DRIVER_X11 = driver_name == b"x11"
except:
    pass


class TestExtWindow(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        flags = video.SDL_WINDOW_BORDERLESS
        sizes = ((1, 1), (10, 10), (10, 20), (200, 17), (640, 480))
        for w, h in sizes:
            window = sdl2ext.Window("Window", size=(w, h), flags=flags)
            assert window.size == (w, h)
            window.close()

    def test_title(self, with_sdl):
        window = sdl2ext.Window("Window", size=(10, 10))
        assert window.title == "Window"
        window.title = b"Test1234"
        assert window.title == "Test1234"
        video.SDL_SetWindowTitle(window.window, b"manual override")
        assert window.title == "manual override"
        window.close()
        assert window.title == "Test1234"
        window.title = "set when closed"
        assert window.title == "set when closed"

    def test_show_hide(self, with_sdl):
        get_flags = video.SDL_GetWindowFlags
        window = sdl2ext.Window("Test Show Window", size=(200, 200))
        assert get_flags(window.window) & SDL_WINDOW_SHOWN != SDL_WINDOW_SHOWN
        window.show()
        assert get_flags(window.window) & SDL_WINDOW_SHOWN == SDL_WINDOW_SHOWN
        window.hide()
        assert get_flags(window.window) & SDL_WINDOW_SHOWN != SDL_WINDOW_SHOWN
        window.close()
        # Test informative exceptions for closed window
        with pytest.raises(RuntimeError):
            window.show()
        with pytest.raises(RuntimeError):
            window.hide()

    @pytest.mark.skipif(SKIP_ANNOYING, reason="Skip unless requested")
    def test_maximize(self, with_sdl):
        get_flags = video.SDL_GetWindowFlags
        max_flag = video.SDL_WINDOW_MAXIMIZED
        flags = video.SDL_WINDOW_RESIZABLE
        window = sdl2ext.Window("Test", size=(200, 200), flags=flags)
        window.show()
        assert get_flags(window.window) & max_flag != max_flag
        window.maximize()
        if not DRIVER_DUMMY:
            assert get_flags(window.window) & max_flag == max_flag
        window.close()
        # Test informative exception for closed window
        with pytest.raises(RuntimeError):
            window.maximize()

    @pytest.mark.skipif(SKIP_ANNOYING, reason="Skip unless requested")
    def test_minimize_restore(self, with_sdl):
        get_flags = video.SDL_GetWindowFlags
        min_flag = video.SDL_WINDOW_MINIMIZED
        window = sdl2ext.Window("Test", size=(200, 200))
        window.show()
        assert get_flags(window.window) & min_flag != min_flag
        window.minimize()
        if not (DRIVER_DUMMY or DRIVER_X11):
            assert get_flags(window.window) & min_flag == min_flag
        window.restore()
        assert get_flags(window.window) & min_flag != min_flag
        window.close()
        # Test informative exceptions for closed window
        with pytest.raises(RuntimeError):
            window.minimize()
        with pytest.raises(RuntimeError):
            window.restore()

    @pytest.mark.skip("not implemented")
    def test_refresh(self, with_sdl):
        pass

    def test_get_surface(self, with_sdl):
        window = sdl2ext.Window("Surface", size=(200, 200))
        sf = window.get_surface()
        assert isinstance(sf, surface.SDL_Surface)
        window.close()
        # Test informative exception for closed window
        with pytest.raises(RuntimeError):
            sf = window.get_surface()

    def test_open_close(self, with_sdl):
        get_flags = video.SDL_GetWindowFlags
        window = sdl2ext.Window("Test", size=(200, 200))
        window.close()
        assert window.window == None
        window.open()
        assert isinstance(window.window, video.SDL_Window)
        assert get_flags(window.window) & SDL_WINDOW_SHOWN == SDL_WINDOW_SHOWN
        window.close()

    def test_position(self, with_sdl):
        window = sdl2ext.Window("Position", size=(200, 200), position=(100, 100))
        assert window.position == (100, 100)
        window.position = 70, 300
        assert window.position == (70, 300)
        window.close()

    def test_size(self, with_sdl):
        # This may fail for fullscreen WMs or Win10 tablet modes
        flags = video.SDL_WINDOW_RESIZABLE
        window = sdl2ext.Window("Size", size=(200, 200), flags=flags)
        assert window.size == (200, 200)
        window.size = 150, 77
        assert window.size == (150, 77)
        window.close()
