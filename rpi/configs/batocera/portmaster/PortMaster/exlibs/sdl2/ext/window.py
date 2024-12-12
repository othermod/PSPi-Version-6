"""Window routines to manage on-screen windows."""
from ctypes import c_int, byref
from .compat import stringify, utf8
from .err import SDLError, raise_sdl_err
from .displays import _check_video_init
from .. import video

__all__ = ["Window"]


def _get_sdl_window(w, argname="window"):
    if isinstance(w, Window):
        w = w.window
    elif hasattr(w, "contents"):
        w = w.contents
    if not isinstance(w, video.SDL_Window):
        err = "'{0}' is not a valid SDL window.".format(argname)
        raise ValueError(err)
    return w


class Window(object):
    """Creates a visible window with an optional border and title text.

    In SDL2, a window is the object through which visuals are displayed and
    all input events are captured. This class is a Pythonic alternative to
    working directly with SDL2's :obj:`~sdl2.SDL_Window` type, wrapping a
    number of useful functions for working with windows.

    The created Window is hidden by default, but can be shown using the
    :meth:`~Window.show` method. Additionally, the type and properties of the
    created window can be configured using various flags:

    ================================== =========================================
    Flag                               Description
    ================================== =========================================
    ``SDL_WINDOW_SHOWN``               Will be shown when created
    ``SDL_WINDOW_HIDDEN``              Will be hidden when created
    ``SDL_WINDOW_BORDERLESS``          Will not be decorated by the OS
    ``SDL_WINDOW_RESIZABLE``           Will be resizable
    ``SDL_WINDOW_MINIMIZED``           Will be created in a minimized state
    ``SDL_WINDOW_MAXIMIZED``           Will be created in a maximized state
    ``SDL_WINDOW_FULLSCREEN``          Will be fullscreen
    ``SDL_WINDOW_FULLSCREEN_DESKTOP``  Will be fullscreen at the current desktop
                                       resolution
    ``SDL_WINDOW_OPENGL``              Will be usable with an OpenGL context
    ``SDL_WINDOW_VULKAN``              Will be usable with a Vulkan instance
    ``SDL_WINDOW_METAL``               Will be usable with a Metal context
    ``SDL_WINDOW_ALLOW_HIGHDPI``       Will be created in high-DPI mode
                                       (if supported)
    ``SDL_WINDOW_INPUT_FOCUS``         Will have input focus when created
    ``SDL_WINDOW_MOUSE_FOCUS``         Will have mouse focus when created
    ``SDL_WINDOW_INPUT_GRABBED``       Will prevent the mouse from leaving the
                                       bounds of the window
    ``SDL_WINDOW_MOUSE_CAPTURE``       Will capture mouse to track input outside
                                       of the window when created
    ================================== =========================================

    There are also a few additional window creation flags that only affect the
    X11 window manager (i.e. most distributions of Linux and BSD):

    ================================== =====================================
    Flag                               Description
    ================================== =====================================
    ``SDL_WINDOW_ALWAYS_ON_TOP``       Should stay on top of other windows
    ``SDL_WINDOW_SKIP_TASKBAR``        Should not be added to the taskbar
    ``SDL_WINDOW_UTILITY``             Should be treated as a utility window
    ``SDL_WINDOW_TOOLTIP``             Should be treated as a tooltip
    ``SDL_WINDOW_POPUP_MENU``          Should be treated as a popup menu
    ================================== =====================================

    To combine multiple flags, you can use a bitwise OR to combine two or more
    together before passing them to the `flags` argument. For example, to create
    a fullscreen window that supports an OpenGL context and is shown on
    creation, you would use::

      win_flags = (
          sdl2.SDL_WINDOW_FULLSCREEN | sdl2.SDL_WINDOW_OPENGL |
          sdl2.SDL_WINDOW_SHOWN
      )
      sdl2.ext.Window("PySDL2", (800, 600), flags=win_flags)

    Args:
        title (str): The title to use for the window.
        size (tuple): The initial size (in pixels) of the window, in the format
            `(width, height)`.
        position (tuple, optional): The initial `(x, y)` coordinates of the
            top-left corner of the window. If not specified, defaults to letting
            the system's window manager choose a location for the window.
        flags (int, optional): The window attribute flags with which the window
            will be created. Defaults to ``SDL_WINDOW_HIDDEN``.

    Attributes:
        window (:obj:`~sdl2.SDL_Window`, None): The underlying SDL2 Window
            object. If the window has been closed, this value will be `None`.

    """
    DEFAULTFLAGS = video.SDL_WINDOW_HIDDEN
    DEFAULTPOS = (video.SDL_WINDOWPOS_UNDEFINED,
                  video.SDL_WINDOWPOS_UNDEFINED)

    def __init__(self, title, size, position=None, flags=None):
        _check_video_init("creating a window")
        if position is None:
            position = self.DEFAULTPOS
        if flags is None:
            flags = self.DEFAULTFLAGS

        self.window = None
        self._title = title
        self._position = position
        self._flags = flags
        self._size = size

        self.create()

    def __del__(self):
        """Releases the resources of the Window, implicitly destroying the
        underlying SDL2 window."""
        self.close()

    def _ensure_window(self, action):
        if not self.window:
            raise RuntimeError("Cannot {0} a closed window.".format(action))

    @property
    def position(self):
        """tuple: The (x, y) pixel coordinates of the top-left corner of the
        window.

        """
        if not self.window:
            return self._position
        x, y = c_int(), c_int()
        video.SDL_GetWindowPosition(self.window, byref(x), byref(y))
        return x.value, y.value

    @position.setter
    def position(self, value):
        if self.window:
            video.SDL_SetWindowPosition(self.window, value[0], value[1])
        self._position = value[0], value[1]

    @property
    def title(self):
        """str: The title of the window."""
        if not self.window:
            return stringify(self._title, "utf-8")
        return stringify(video.SDL_GetWindowTitle(self.window), "utf-8")

    @title.setter
    def title(self, value):
        if self.window:
            title_bytes = utf8(value).encode('utf-8')
            video.SDL_SetWindowTitle(self.window, title_bytes)
        self._title = value

    @property
    def size(self):
        """tuple: The current dimensions of the window (in pixels) in the form
        ``(width, height)``.
        
        """
        if not self.window:
            return self._size
        w, h = c_int(), c_int()
        video.SDL_GetWindowSize(self.window, byref(w), byref(h))
        return w.value, h.value

    @size.setter
    def size(self, value):
        self._size = value[0], value[1]
        if self.window:
            video.SDL_SetWindowSize(self.window, value[0], value[1])

    def create(self):
        """Creates the window if it does not already exist."""
        if self.window:
            return
        window = video.SDL_CreateWindow(utf8(self._title).encode('utf-8'),
                                        self._position[0], self._position[1],
                                        self._size[0], self._size[1],
                                        self._flags)
        if not window:
            raise_sdl_err("creating the window")
        self.window = window.contents

    def open(self):
        """Creates and shows the window."""
        if not self.window:
            self.create()
        self.show()

    def close(self):
        """Closes and destroys the window.
        
        Once this method has been called, the window cannot be re-opened.
        However, you can create a new window with the same settings using the
        :meth:`create` method.

        """
        if self.window:
            video.SDL_DestroyWindow(self.window)
            self.window = None

    def show(self):
        """Shows the window on the display.
        
        If the window is already visible, this method does nothing.

        """
        self._ensure_window("show")
        video.SDL_ShowWindow(self.window)

    def hide(self):
        """Hides the window.

        If the window is already hidden, this method does nothing.
        
        """
        self._ensure_window("hide")
        video.SDL_HideWindow(self.window)

    def maximize(self):
        """Maximizes the window."""
        self._ensure_window("maximize")
        video.SDL_MaximizeWindow(self.window)

    def minimize(self):
        """Minimizes the window into the system's dock or task bar."""
        self._ensure_window("minimize")
        video.SDL_MinimizeWindow(self.window)

    def restore(self):
        """Restores a minimized or maximized window to its original state.
        
        If the window has not been minimized or maximized, this method does
        nothing.

        """
        self._ensure_window("restore")
        video.SDL_RestoreWindow(self.window)

    def refresh(self):
        """Updates the window to reflect any changes made to its surface.

        .. note::
           This only needs to be called if the window surface was acquired and
           modified using :meth:`get_surface`.

        """
        self._ensure_window("refresh")
        video.SDL_UpdateWindowSurface(self.window)

    def get_surface(self):
        """Gets the :obj:`~sdl2.SDL_Surface` used by the window.

        This method obtains the SDL surface used by the window, which can be
        then be modified to change the contents of the window (e.g draw shapes
        or images) using functions such as :func:`sdl2.SDL_BlitSurface` or
        :func:`sdl2.ext.fill`.

        The obtained surface will be invalidated if the window is resized. As
        such, you will need to call this method again whenever this happens
        in order to continue to access the window's contents.

        .. note::
           If using OpenGL/Vulkan/Metal rendering or the SDL rendering API (e.g.
           :func:`sdl2.SDL_CreateRenderer`) for drawing to the window, this
           method should not be used.

        Returns:
            :obj:`~sdl2.SDL_Surface`: The surface associated with the window.

        """
        self._ensure_window("get the surface of")
        sf = video.SDL_GetWindowSurface(self.window)
        if not sf:
            raise_sdl_err("getting the window surface")
        return sf.contents
