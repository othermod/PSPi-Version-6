from ctypes import c_float, byref
from .common import raise_sdl_err
from .. import video, rect
from .._sdl_init import SDL_WasInit, SDL_INIT_VIDEO

__all__ = ["DisplayInfo", "get_displays"]


def _check_video_init(suffix="performing that action"):
    err = "The SDL video subsystem must be initialized before "
    if not SDL_WasInit(0) & SDL_INIT_VIDEO == SDL_INIT_VIDEO:
        raise RuntimeError(err + suffix + ".")


class DisplayInfo(object):
    """The name and video mode information for a given connected display.

    Video modes are represented with :obj:`~sdl2.SDL_VideoMode` structures,
    which contain the width (``mode.w``), height (``mode.h``), refresh rate
    (``mode.refresh_rate``), and SDL pixel format (``mode.format``) for a
    given video mode.

    Note that refresh rates in SDL are returned as integers, meaning that the
    refresh rate for a display may be reported incorrectly on some platforms
    (e.g. ``59`` for an OS-reported refresh rate of 59.94 Hz).

    Args:
        index (int): The index of the display to query. Must be less than the
            total number of connected displays.

    Attributes:
        index (int): The index of the display.
        name (str): The name of the display.
        modes (list of :obj:`~sdl2.SDL_VideoMode`): A list of all video modes
            supported by the display.

    """
    def __init__(self, index):
        # Make sure video subsystem active and index is valid
        _check_video_init("querying display info")
        n_displays = video.SDL_GetNumVideoDisplays()
        if not 0 <= index < n_displays:
            err = "Invalid display index '{0}' (valid displays: {1})."
            valid = str(list(range(n_displays)))
            raise ValueError(err.format(index, valid))

        self.index = index
        self._sdl_name = video.SDL_GetDisplayName(index)
        self.name = self._sdl_name.decode('utf-8')
        if len(self.name) == 1 and self.name.isdigit():
            self.name = u"Display " + self.name
        self.modes = self._get_modes()

    def __repr__(self):
        return "DisplayInfo({0}, '{1}')".format(self.index, self.name)

    def _get_modes(self):
        modes = []
        n_modes = video.SDL_GetNumDisplayModes(self.index)
        for i in range(n_modes):
            dmode = video.SDL_DisplayMode()
            ret = video.SDL_GetDisplayMode(self.index, i, byref(dmode))
            if ret != 0:
                raise_sdl_err("retrieving display modes")
            modes.append(dmode)
        return modes

    def _check_connected(self):
        # NOTE: SDL2 doesn't seem to notice if a display is disconnected, at
        # least on macOS
        if video.SDL_GetDisplayName(self.index) != self._sdl_name:
            err = "The display '{0}' is no longer connected to the system."
            raise RuntimeError(err.format(self.name))

    @property
    def dpi(self):
        """float: The current diagonal DPI for the display.

        Note that this value is the DPI reported by the display itself, which
        is not always available or guaranteed to be accurate.

        """
        self._check_connected()
        ddpi, hdpi, vdpi = c_float(0), c_float(0), c_float(0)
        ret = video.SDL_GetDisplayDPI(
            self.index, byref(ddpi), byref(hdpi), byref(vdpi)
        )
        if ret != 0:
            raise_sdl_err("retrieving display DPI")
        return float(ddpi.value)

    @property
    def current_mode(self):
        """:obj:`~sdl2.SDL_DisplayMode`: The current mode for the display.
        """
        self._check_connected()
        currmode = video.SDL_DisplayMode()
        ret = video.SDL_GetCurrentDisplayMode(self.index, byref(currmode))
        if ret != 0:
            raise_sdl_err("retrieving the current display mode")
        return currmode

    @property
    def desktop_mode(self):
        """:obj:`~sdl2.SDL_DisplayMode`: The desktop mode for the display.

        If the fullscreen resolution has been changed by SDL, this returns the
        original desktop mode for the display.

        """
        self._check_connected()
        ddmode = video.SDL_DisplayMode()
        ret = video.SDL_GetDesktopDisplayMode(self.index, byref(ddmode))
        if ret != 0:
            raise_sdl_err("retrieving the desktop display mode")
        return ddmode

    @property
    def bounds(self):
        """:obj:`~sdl2.SDL_Rect`: The bounding rectangle of the display relative
        to the full desktop.

        The x and y values for the rectangle represent the pixel coordinates of
        the top-left corner of the display relative to the full desktop. For
        example, for a multi-monitor desktop with 2 1920x1200 displays side by
        side, x and y would be (0, 0) for the left display and (1920, 0) for the
        right display. The w and h values indicate the current resolution of the
        display.

        """
        self._check_connected()
        bounds = rect.SDL_Rect()
        ret = video.SDL_GetDisplayBounds(self.index, byref(bounds))
        if ret != 0:
            raise_sdl_err("retrieving the display bounds")
        return bounds

    def closest_mode(self, w, h, hz=None):
        """Determines the closest supported mode to a given resolution.

        For example, if this method is called with (1280, 800) on a
        display that supports up to 1280x720, the 1280x720 display mode
        will be returned. 

        Args:
            w (int): The target display mode width (in pixels).
            h (int): The target display mode height (in pixels).
            hz (int, optional): The target display mode refresh rate (in Hz).
                If ``None``, refresh rate will be ignored.
        
        Returns:
            :obj:`~sdl2.SDL_DisplayMode`: The closest mode to the requested
            size/Hz supported by the display.

        """
        self._check_connected()
        if hz == None:
            hz = 0
        req = video.SDL_DisplayMode(w=w, h=h, refresh_rate=hz)
        closest = video.SDL_DisplayMode()
        ret = video.SDL_GetClosestDisplayMode(self.index, req, byref(closest))
        if not ret:
            raise_sdl_err("retrieving the closest display mode")
        return closest

    def has_mode(self, w, h, hz=None):
        """Checks whether a given mode is supported by the display.

        Note that this function treats a reported refresh rate of 59 Hz as
        equivalent to 60 Hz (and 99 Hz to 100 Hz, etc.) to better support OSes
        that report 60 Hz as 59.94 Hz and get rounded down.

        Args:
            w (int): The width of the mode to check (in pixels).
            h (int): The height of the mode to check (in pixels).
            hz (int, optional): The refresh rate of the mode to check (in Hz).
                If ``None``, refresh rate will be ignored.
        
        Returns:
            bool: True if the mode is supported, otherwise False.

        """
        closest = self.closest_mode(w, h, hz)
        same = w == closest.w and h == closest.h
        if hz:
            allowed = [hz]
            # Handle 60 Hz reported as 59 Hz on some OSes
            if closest.refresh_rate % 10 == 9:
                allowed.append(hz - 1)
            same = same and closest.refresh_rate in allowed
        return same


def get_displays():
    """Returns a list all currently connected displays.

    Returns:
        list of :obj:`~sdl2.ext.DisplayInfo`: The display info objects for each
        connected display.

    """
    _check_video_init("querying display info")
    displays = []
    for i in range(video.SDL_GetNumVideoDisplays()):
        displays.append(DisplayInfo(i))
    return displays
