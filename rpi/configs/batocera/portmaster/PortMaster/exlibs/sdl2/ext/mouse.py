from ctypes import c_int, byref
from collections import namedtuple
from .compat import stringify, utf8
from .err import SDLError, raise_sdl_err
from .window import _get_sdl_window
from .. import mouse
from ..events import SDL_ENABLE, SDL_DISABLE, SDL_QUERY

__all__ = [
    "show_cursor", "hide_cursor", "cursor_hidden", "mouse_coords", "mouse_delta",
    "warp_mouse", "mouse_button_state", "ButtonState",
]


class ButtonState(object):
    """A class representing the state of the mouse buttons.

    Args:
        buttonmask (int): The raw SDL button mask to parse.

    Attributes:
        raw (int): The raw SDL button mask representing the button state.

    """
    def __init__(self, buttonmask):
        self.raw = buttonmask

    def __repr__(self):
        s = "ButtonState(l={0}, r={1}, m={2})"
        return s.format(self.left, self.right, self.middle)

    def __eq__(self, s2):
        return self.raw == s2.raw

    def __ne__(self, s2):
        return self.raw != s2.raw

    def _check_button(self, bmask):
        return int(bool(self.raw & bmask))

    @property
    def any_pressed(self):
        """bool: True if any buttons are currently pressed, otherwise False.
        """
        return self.raw != 0

    @property
    def left(self):
        """int: The state of the left mouse button (0 = up, 1 = down).
        """
        return self._check_button(mouse.SDL_BUTTON_LMASK)

    @property
    def right(self):
        """int: The state of the right mouse button (0 = up, 1 = down).
        """
        return self._check_button(mouse.SDL_BUTTON_RMASK)

    @property
    def middle(self):
        """int: The state of the middle mouse button (0 = up, 1 = down).
        """
        return self._check_button(mouse.SDL_BUTTON_MMASK)

    @property
    def x1(self):
        """int: The state of the first extra mouse button (0 = up, 1 = down).
        """
        return self._check_button(mouse.SDL_BUTTON_X1MASK)

    @property
    def x2(self):
        """int: The state of the second extra mouse button (0 = up, 1 = down).
        """
        return self._check_button(mouse.SDL_BUTTON_X2MASK)


def show_cursor():
    """Unhides the mouse cursor if it is currently hidden.

    """
    ret = mouse.SDL_ShowCursor(SDL_ENABLE)
    if ret < 0:
        raise_sdl_err("showing the mouse cursor")

def hide_cursor():
    """Hides the mouse cursor if it is currently visible.

    """
    ret = mouse.SDL_ShowCursor(SDL_DISABLE)
    if ret < 0:
        raise_sdl_err("hiding the mouse cursor")

def cursor_hidden():
    """Checks whether the mouse cursor is currently visible.

    Returns:
        bool: True if the cursor is hidden, otherwise False.

    """
    return mouse.SDL_ShowCursor(SDL_QUERY) == SDL_DISABLE

def mouse_coords(desktop=False):
    """Get the current x/y coordinates of the mouse cursor.

    By default, this function reports the coordinates relative to the top-left
    corner of the SDL window that currently has focus. To obtain the mouse
    coordinates relative to the top-right corner of the full desktop, this
    function can optionally be called with ``desktop`` argument set to True.

    Args:
        desktop (bool, optional): If True, reports the mouse coordinates
            relative to the full desktop instead of the currently-focused SDL
            window. Defaults to False.

    Returns:
        tuple: The current (x, y) coordinates of the mouse cursor.

    """
    x, y = c_int(0), c_int(0)
    if desktop:
        mouse.SDL_GetGlobalMouseState(byref(x), byref(y))
    else:
        mouse.SDL_GetMouseState(byref(x), byref(y))
    return (int(x.value), int(y.value))

def mouse_button_state():
    """Gets the current state of each button of the mouse.

    Mice in SDL are currently able to have up to 5 buttons: left, right, middle,
    and two extras (x1 and x2). You can check each of these individually, or
    alternatively check whether any buttons have been pressed::

       bstate = mouse_button_state()
       if bstate.any_pressed:
           if bstate.left == 1:
               print("left button down!")
           if bstate.right == 1:
               print("right button down!")

    Returns:
        :obj:`ButtonState`: A representation of the current button state of the
        mouse.

    """
    x, y = c_int(0), c_int(0)
    bmask = mouse.SDL_GetMouseState(byref(x), byref(y))
    return ButtonState(bmask)

def mouse_delta():
    """Get the relative change in cursor position since last checked.

    The first time this function is called, it will report the (x, y) change in
    cursor position since the SDL video or event system was initialized.
    Subsequent calls to this function report the change in position since the
    previous time the function was called.

    Returns:
        tuple: The (x, y) change in cursor coordinates since the function was
        last called.

    """
    x, y = c_int(0), c_int(0)
    mouse.SDL_GetRelativeMouseState(byref(x), byref(y))
    return (int(x.value), int(y.value))

def warp_mouse(x, y, window=None, desktop=False):
    """Warps the mouse cursor to a given location on the screen.

    By default, this warps the mouse cursor relative to the top-left corner of
    whatever SDL window currently has mouse focus. For example,::

       warp_mouse(400, 300)

    would warp the mouse to the middle of a 800x600 SDL window. Alternatively,
    the cursor can be warped within a specific SDL window or relative to the
    full desktop.

    Args:
        x (int): The new X position for the mouse cursor.
        y (int): The new Y position for the mouse cursor.
        window (:obj:`SDL_Window` or :obj:`~sdl2.ext.Window`, optional): The
            SDL window within which to warp the mouse cursor. If not specified
            (the default), the cursor will be warped within the SDL window that
            currently has mouse focus.
        desktop (bool, optional): If True, the mouse cursor will be warped
            relative to the full desktop instead of the current SDL window.
            Defaults to False.
    
    """
    if desktop:
        ret = mouse.SDL_WarpMouseGlobal(x, y)
        if ret < 0:
            raise_sdl_err("warping the mouse cursor")
    else:
        if window is not None:
            window = _get_sdl_window(window)
        mouse.SDL_WarpMouseInWindow(window, x, y)
