import sys
import pytest
import sdl2
from sdl2 import SDL_Window, SDL_ClearError
from sdl2 import ext as sdl2ext

from .conftest import SKIP_ANNOYING


@pytest.fixture(scope="module")
def with_ext_window(with_sdl):
    win = sdl2ext.Window("Test", (100, 100))
    win.show()
    yield win
    win.close()


def test_ButtonState():
    test1 = sdl2.SDL_BUTTON_LMASK | sdl2.SDL_BUTTON_RMASK | sdl2.SDL_BUTTON_MMASK
    test2 = sdl2.SDL_BUTTON_X1MASK | sdl2.SDL_BUTTON_X2MASK

    b1 = sdl2ext.ButtonState(test1)
    assert b1.raw == test1
    assert b1.left and b1.right and b1.middle
    assert not (b1.x1 or b1.x2)
    assert b1.any_pressed

    b2 = sdl2ext.ButtonState(test2)
    assert not (b2.left or b2.right or b2.middle)
    assert b2.x1 and b2.x2
    assert b2.any_pressed

    b3 = sdl2ext.ButtonState(0)
    assert not b3.any_pressed

def test_showhide_cursor(with_ext_window):
    sdl2ext.hide_cursor()
    assert sdl2ext.cursor_hidden()
    sdl2ext.show_cursor()
    assert not sdl2ext.cursor_hidden()

def test_mouse_button_state(with_ext_window):
    bstate = sdl2ext.mouse_button_state()
    assert isinstance(bstate, sdl2ext.ButtonState)

def test_mouse_coords(with_ext_window):
    # Get mouse positon within the window
    pos = sdl2ext.mouse_coords()
    assert 0 <= pos[0] <= 100
    assert 0 <= pos[1] <= 100
    # Get mouse positon relative to the desktop
    pos = sdl2ext.mouse_coords(desktop=True)
    assert 0 <= pos[0]
    assert 0 <= pos[1]

def test_mouse_delta(with_ext_window):
    # NOTE: Can't test properly with warp_mouse, since warping the mouse in SDL
    # doesn't affect the mouse xdelta/ydelta properties 
    dx, dy = sdl2ext.mouse_delta()
    assert type(dx) == int and type(dy) == int

@pytest.mark.skipif(SKIP_ANNOYING, reason="Skip unless requested")
def test_warp_mouse(with_ext_window):
    x_orig, y_orig = sdl2ext.mouse_coords(desktop=True)
    # Test warping within a specific window
    win = with_ext_window
    sdl2ext.warp_mouse(20, 30, window=win)
    x, y = sdl2ext.mouse_coords()
    assert x == 20 and y == 30
    # Test warping in the window that currently has focus
    sdl2ext.warp_mouse(50, 50)
    x, y = sdl2ext.mouse_coords()
    assert x == 50 and y == 50
    # Test warping relative to the desktop
    sdl2ext.warp_mouse(x_orig, y_orig, desktop=True)
    x, y = sdl2ext.mouse_coords(desktop=True)
    assert x == x_orig and y == y_orig
