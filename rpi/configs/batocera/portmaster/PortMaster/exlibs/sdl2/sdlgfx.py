import os
from ctypes import Structure, POINTER, c_int, c_float, c_void_p, c_char, \
    c_char_p, c_double
from ctypes import POINTER as _P
from .dll import DLL, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint32, Sint16
from .render import SDL_Renderer
from .surface import SDL_Surface

# NOTE: This module is currently missing wrappers for the image filtering
# functions in SDL2_imageFilter.h. However, because we have Pillow on Python
# this isn't really a pressing concern. Time permitting, these functions may
# be wrapped at a later date for the sake of completeness.

__all__ = [
    # Constants
    "FPS_UPPER_LIMIT", "FPS_LOWER_LIMIT", "FPS_DEFAULT",
    "SDL2_GFXPRIMITIVES_MAJOR", "SDL2_GFXPRIMITIVES_MAJOR",
    "SDL2_GFXPRIMITIVES_MICRO", "SMOOTHING_OFF", "SMOOTHING_ON",

    # Structs
    "FPSManager",

    # Python Functions
    "get_dll_file"
]


try:
    dll = DLL("SDL2_gfx", ["SDL2_gfx", "SDL2_gfx-1.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)


def get_dll_file():
    """Gets the file name of the loaded SDL2_gfx library."""
    return dll.libfile

_bind = dll.bind_function


# Constants, enums, type definitions, and macros

SDL2_GFXPRIMITIVES_MAJOR = 1
SDL2_GFXPRIMITIVES_MINOR = 0
SDL2_GFXPRIMITIVES_MICRO = 4

FPS_UPPER_LIMIT = 200
FPS_LOWER_LIMIT = 1
FPS_DEFAULT = 30

SMOOTHING_OFF = 0
SMOOTHING_ON = 1

class FPSManager(Structure):
    """A structure holding the state and timing of the framerate manager.

    This class can be used with other SDL_gfx functions to set a custom
    framerate within a given rendering loop. When used with
    :func:`SDL_framerateDelay`, it uses its initial frame onset time
    (:attr:`baseticks`) and the duration per frame to try to present frames
    at consistent intervals from that initial point.

    After an FPSManager is created, it needs to be initialized with
    :func:`SDL_initFramerate` before it can be used.

    .. note::
        This method of frame pacing may not play nicely with vsync in SDL2.

    Attributes:
        framecount (int): The number of frames counted by the manager since
            being initialized.
        rateticks (float): The time delay (in ms) between each frame.
        baseticks (int): The milliseconds since SDL initialization at which the
            manager was initialized with :func:`SDL_initFramerate`. Used
            internally as the initial frame onset time.
        lastticks (int): The milliseconds since SDL initialization at which the
            previous frame was displayed.
        rate (int): The framerate (in Hz) of the manager.

    """
    _fields_ = [
        ("framecount", Uint32),
        ("rateticks", c_float),
        ("baseticks", Uint32),
        ("lastticks", Uint32),
        ("rate", Uint32),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_initFramerate", [_P(FPSManager)]),
    SDLFunc("SDL_setFramerate", [_P(FPSManager), Uint32], c_int),
    SDLFunc("SDL_getFramerate", [_P(FPSManager)], c_int),
    SDLFunc("SDL_getFramecount", [_P(FPSManager)], Uint32),
    SDLFunc("SDL_framerateDelay", [_P(FPSManager)], Uint32),
    SDLFunc("pixelColor", [_P(SDL_Renderer), Sint16, Sint16, Uint32], c_int),
    SDLFunc("pixelRGBA", [_P(SDL_Renderer), Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("hlineColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("hlineRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("vlineColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("vlineRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("rectangleColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("rectangleRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("roundedRectangleColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("roundedRectangleRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("boxColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("boxRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("roundedBoxColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("roundedBoxRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("lineColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("lineRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("aalineColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("aalineRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("thickLineColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint32], c_int),
    SDLFunc("thickLineRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("circleColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("circleRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("arcColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("arcRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("aacircleColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("aacircleRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("filledCircleColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("filledCircleRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("ellipseColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("ellipseRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("aaellipseColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("aaellipseRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("filledEllipseColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("filledEllipseRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("pieColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("pieRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("filledPieColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("filledPieRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("trigonColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("trigonRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("aatrigonColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("aatrigonRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("filledTrigonColor", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint32], c_int),
    SDLFunc("filledTrigonRGBA", [_P(SDL_Renderer), Sint16, Sint16, Sint16, Sint16, Sint16, Sint16, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("polygonColor", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint32], c_int),
    SDLFunc("polygonRGBA", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("aapolygonColor", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint32], c_int),
    SDLFunc("aapolygonRGBA", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("filledPolygonColor", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint32], c_int),
    SDLFunc("filledPolygonRGBA", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("texturedPolygon", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, _P(SDL_Surface), c_int, c_int], c_int),
    SDLFunc("bezierColor", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, c_int, Uint32], c_int),
    SDLFunc("bezierRGBA", [_P(SDL_Renderer), _P(Sint16), _P(Sint16), c_int, c_int, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("gfxPrimitivesSetFont", [c_void_p, Uint32, Uint32]),
    SDLFunc("gfxPrimitivesSetFontRotation", [Uint32]),
    SDLFunc("characterColor", [_P(SDL_Renderer), Sint16, Sint16, c_char, Uint32], c_int),
    SDLFunc("characterRGBA", [_P(SDL_Renderer), Sint16, Sint16, c_char, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("stringColor", [_P(SDL_Renderer), Sint16, Sint16, c_char_p, Uint32], c_int),
    SDLFunc("stringRGBA", [_P(SDL_Renderer), Sint16, Sint16, c_char_p, Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("rotozoomSurface", [_P(SDL_Surface), c_double, c_double, c_int], _P(SDL_Surface)),
    SDLFunc("rotozoomSurfaceXY", [_P(SDL_Surface), c_double, c_double, c_double, c_int], _P(SDL_Surface)),
    SDLFunc("rotozoomSurfaceSize", [c_int, c_int, c_double, c_double, _P(c_int), _P(c_int)]),
    SDLFunc("rotozoomSurfaceSizeXY", [c_int, c_int, c_double, c_double, c_double, _P(c_int), _P(c_int)]),
    SDLFunc("zoomSurface", [_P(SDL_Surface), c_double, c_double, c_int], _P(SDL_Surface)),
    SDLFunc("zoomSurfaceSize", [c_int, c_int, c_double, c_double, _P(c_int), _P(c_int)]),
    SDLFunc("shrinkSurface", [_P(SDL_Surface), c_int, c_int], _P(SDL_Surface)),
    SDLFunc("rotateSurface90Degrees", [_P(SDL_Surface), c_int], _P(SDL_Surface)),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Python wrapper functions

def SDL_initFramerate(manager):
    """Initializes a framerate manager.

    Calling this function on an :class:`FPSManager` initializes it with a
    default framerate of 30 Hz and prepares it for counting and timing frames.
    If the manager was already initialized, calling this function will reset
    its framecount, initial frame onset time, and framerate.

    Args:
        manager (:obj:`sdlgfx.FPSManager`): The framerate manager to initialize.

    """
    return _ctypes.SDL_initFramerate(manager)

def SDL_setFramerate(manager, rate):
    """Sets the framerate of a framerate manager.

    Sets a new framerate for the manager, resetting both the framecount and the
    the initial frame onset time. Framerates must be between ``FPS_LOWER_LIMIT``
    (1) and ``FPS_UPPER_LIMIT`` (200), inclusive, to be accepted.

    Args:
        manager (:obj:`sdlgfx.FPSManager`): The framerate manager to configure.
        rate (int): The new framerate in Hz.

    Returns:
        int: 0 on success, or -1 if an error occurred.

    """
    return _ctypes["SDL_setFramerate"](manager, rate)

def SDL_getFramerate(manager):
    """Gets the current framerate for a framerate manager.

    Args:
        manager (:obj:`sdlgfx.FPSManager`): The framerate manager for which the
            currently set framerate will be retrieved.

    Returns:
        int: 0 on success, or -1 if an error occurred.

    """
    return _ctypes["SDL_getFramerate"](manager)

def SDL_getFramecount(manager):
    """Gets the current number of frames counted by a framerate manager.

    .. note::
        This value is reset whenever a frame is dropped (i.e. the rendering
        loop takes longer than the set interval between frames) or the framerate
        is changed.

    Args:
        manager (:obj:`sdlgfx.FPSManager`): The framerate manager for which the
            current framecount will be retrieved.

    Returns:
        int: 0 on success, or -1 if an error occurred.

    """
    return _ctypes["SDL_getFramecount"](manager)

def SDL_framerateDelay(manager):
    """Delays execution until the next frame occurs.

    This function waits for the next frame onset (as determined by the rate set
    by :func:`SDL_setFramerate`) to keep frame pacing consistent. This should be
    called once per loop within the program's main rendering loop.
    
    If the rendering loop takes longer than the set framerate, the delay will be
    zero and the framecount and initial frame onset time will be reset.

    Args:
        manager (:obj:`sdlgfx.FPSManager`): The framerate manager to use for
            frame pacing.

    Returns:
        int: 0 on success, or -1 if an error occurred.

    """
    return _ctypes["SDL_framerateDelay"](manager)


def pixelColor(renderer, x, y, color):
    """Draws a single pixel to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X (horizontal) coordinate of the pixel.
        y (int): The Y (vertical) coordinate of the pixel.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["pixelColor"](renderer, x, y, color)

def pixelRGBA(renderer, x, y, r, g, b, a):
    """Draws a single pixel to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X (horizontal) coordinate of the pixel.
        y (int): The Y (vertical) coordinate of the pixel.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["pixelRGBA"](renderer, x, y, r, g, b, a)

def hlineColor(renderer, x1, x2, y, color):
    """Draws a horizontal line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y (int): The Y (vertical) coordinate of the points of the line.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["hlineColor"](renderer, x1, x2, y, color)

def hlineRGBA(renderer, x1, x2, y, r, g, b, a):
    """Draws a horizontal line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y (int): The Y coordinate of the points of the line.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["hlineRGBA"](renderer, x1, x2, y, r, g, b, a)

def vlineColor(renderer, x, y1, y2, color):
    """Draws a vertical line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the points of the line.
        y1 (int): The X coordinate of the first point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["vlineColor"](renderer, x, y1, y2, color)

def vlineRGBA(renderer, x, y1, y2, r, g, b, a):
    """Draws a vertical line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the points of the line.
        y1 (int): The X coordinate of the first point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["vlineRGBA"](renderer, x, y1, y2, r, g, b, a)


def rectangleColor(renderer, x1, y1, x2, y2, color):
    """Draws an unfilled rectangle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["rectangleColor"](renderer, x1, y1, x2, y2, color)

def rectangleRGBA(renderer, x1, y1, x2, y2, r, g, b, a):
    """Draws an unfilled rectangle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["rectangleRGBA"](renderer, x1, y1, x2, y2, r, g, b, a)

def roundedRectangleColor(renderer, x1, y1, x2, y2, rad, color):
    """Draws an unfilled rectangle with rounded corners to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        rad (int): The radius of the arc of the rounded corners.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["roundedRectangleColor"](renderer, x1, y1, x2, y2, rad, color)

def roundedRectangleRGBA(renderer, x1, y1, x2, y2, rad, r, g, b, a):
    """Draws an unfilled rectangle with rounded corners to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        rad (int): The radius of the arc of the rounded corners.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["roundedRectangleRGBA"](renderer, x1, y1, x2, y2, rad, r, g, b, a)

def boxColor(renderer, x1, y1, x2, y2, color):
    """Draws a filled rectangle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["boxColor"](renderer, x1, y1, x2, y2, color)

def boxRGBA(renderer, x1, y1, x2, y2, r, g, b, a):
    """Draws a filled rectangle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["boxRGBA"](renderer, x1, y1, x2, y2, r, g, b, a)

def roundedBoxColor(renderer, x1, y1, x2, y2, rad, color):
    """Draws a filled rectangle with rounded corners to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        rad (int): The radius of the arc of the rounded corners.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["roundedBoxColor"](renderer, x1, y1, x2, y2, rad, color)

def roundedBoxRGBA(renderer, x1, y1, x2, y2, rad, r, g, b, a):
    """Draws a filled rectangle with rounded corners to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the top-right point of the rectangle.
        y1 (int): The Y coordinate of the top-right point of the rectangle.
        x2 (int): The X coordinate of the bottom-left point of the rectangle.
        y2 (int): The Y coordinate of the bottom-left point of the rectangle.
        rad (int): The radius of the arc of the rounded corners.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["roundedBoxRGBA"](renderer, x1, y1, x2, y2, rad, r, g, b, a)


def lineColor(renderer, x1, y1, x2, y2, color):
    """Draws a line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["lineColor"](renderer, x1, y1, x2, y2, color)

def lineRGBA(renderer, x1, y1, x2, y2, r, g, b, a):
    """Draws a line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["lineRGBA"](renderer, x1, y1, x2, y2, r, g, b, a)

def aalineColor(renderer, x1, y1, x2, y2, color):
    """Draws an anti-aliased line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aalineColor"](renderer, x1, y1, x2, y2, color)

def aalineRGBA(renderer, x1, y1, x2, y2, r, g, b, a):
    """Draws an anti-aliased line to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aalineRGBA"](renderer, x1, y1, x2, y2, r, g, b, a)

def thickLineColor(renderer, x1, y1, x2, y2, width, color):
    """Draws a line with a given thickness to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        width (int): The thickness of the line in pixels (from 1 to 255).
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["thickLineColor"](renderer, x1, y1, x2, y2, width, color)

def thickLineRGBA(renderer, x1, y1, x2, y2, width, r, g, b, a):
    """Draws a line with a given thickness to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): The X coordinate of the first point of the line.
        y1 (int): The Y coordinate of the first point of the line.
        x2 (int): The X coordinate of the second point of the line.
        y2 (int): The Y coordinate of the second point of the line.
        width (int): The thickness of the line in pixels (from 1 to 255).
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["thickLineRGBA"](renderer, x1, y1, x2, y2, width, r, g, b, a)


def circleColor(renderer, x, y, rad, color):
    """Draws an unfilled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["circleColor"](renderer, x, y, rad, color)

def circleRGBA(renderer, x, y, rad, r, g, b, a):
    """Draws an unfilled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["circleRGBA"](renderer, x, y, rad, r, g, b, a)

def arcColor(renderer, x, y, rad, start, end, color):
    """Draws an arc to the renderer with a given color.

    The start and end of the arc are defined in units of degrees, with 0 being
    the bottom of the arc circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        start (int): The start of the arc (in degrees).
        end (int): The end of the arc (in degrees).
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["arcColor"](renderer, x, y, rad, start, end, color)

def arcRGBA(renderer, x, y, rad, start, end, r, g, b, a):
    """Draws an arc to the renderer with a given color.

    The start and end of the arc are defined in units of degrees, with 0 being
    the bottom of the arc circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        start (int): The start of the arc (in degrees).
        end (int): The end of the arc (in degrees).
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["arcRGBA"](renderer, x, y, rad, start, end, r, g, b, a)

def aacircleColor(renderer, x, y, rad, color):
    """Draws an anti-aliased unfilled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aacircleColor"](renderer, x, y, rad, color)

def aacircleRGBA(renderer, x, y, rad, r, g, b, a):
    """Draws an anti-aliased unfilled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aacircleRGBA"](renderer, x, y, rad, r, g, b, a)

def filledCircleColor(renderer, x, y, rad, color):
    """Draws a filled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledCircleColor"](renderer, x, y, rad, color)

def filledCircleRGBA(renderer, x, y, rad, r, g, b, a):
    """Draws a filled circle to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the circle.
        y (int): The Y coordinate of the center of the circle.
        rad (int): The radius (in pixels) of the circle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledCircleRGBA"](renderer, x, y, rad, r, g, b, a)


def ellipseColor(renderer, x, y, rx, ry, color):
    """Draws an unfilled ellipse to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["ellipseColor"](renderer, x, y, rx, ry, color)

def ellipseRGBA(renderer, x, y, rx, ry, r, g, b, a):
    """Draws an unfilled ellipse to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["ellipseRGBA"](renderer, x, y, rx, ry, r, g, b, a)

def aaellipseColor(renderer, x, y, rx, ry, color):
    """Draws an anti-aliased unfilled ellipse to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aaellipseColor"](renderer, x, y, rx, ry, color)

def aaellipseRGBA(renderer, x, y, rx, ry, r, g, b, a):
    """Draws an anti-aliased unfilled ellipse to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aaellipseRGBA"](renderer, x, y, rx, ry, r, g, b, a)

def filledEllipseColor(renderer, x, y, rx, ry, color):
    """Draws a filled ellipse to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledEllipseColor"](renderer, x, y, rx, ry, color)

def filledEllipseRGBA(renderer, x, y, rx, ry, r, g, b, a):
    """Draws a filled ellipse to the renderer with a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the ellipse.
        y (int): The Y coordinate of the center of the ellipse.
        rx (int): The x-axis radius (i.e. width) of the ellipse.
        ry (int): The y-axis radius (i.e. height) of the ellipse.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledEllipseRGBA"](renderer, x, y, rx, ry, r, g, b, a)


def pieColor(renderer, x, y, rad, start, end, color):
    """Draws an unfilled pie slice (i.e. circle segment) to the renderer.

    The start and end of the pie are defined in units of degrees, with 0 being
    the bottom of the circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the pie (circle).
        y (int): The Y coordinate of the center of the pie (circle).
        rad (int): The radius (in pixels) of the pie.
        start (int): Start of the pie slice (in degrees).
        end (int): End of the pie slice (in degrees)
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["pieColor"](renderer, x, y, rad, start, end, color)

def pieRGBA(renderer, x, y, rad, start, end, r, g, b, a):
    """Draws an unfilled pie slice (i.e. circle segment) to the renderer.

    The start and end of the pie are defined in units of degrees, with 0 being
    the bottom of the circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the pie (circle).
        y (int): The Y coordinate of the center of the pie (circle).
        rad (int): The radius (in pixels) of the pie.
        start (int): Start of the pie slice (in degrees).
        end (int): End of the pie slice (in degrees)
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["pieRGBA"](renderer, x, y, rad, start, end, r, g, b, a)

def filledPieColor(renderer, x, y, rad, start, end, color):
    """Draws a filled pie slice (i.e. circle segment) to the renderer.

    The start and end of the pie are defined in units of degrees, with 0 being
    the bottom of the circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the pie (circle).
        y (int): The Y coordinate of the center of the pie (circle).
        rad (int): The radius (in pixels) of the pie.
        start (int): Start of the pie slice (in degrees).
        end (int): End of the pie slice (in degrees)
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledPieColor"](renderer, x, y, rad, start, end, color)

def filledPieRGBA(renderer, x, y, rad, start, end, r, g, b, a):
    """Draws a filled pie slice (i.e. circle segment) to the renderer.

    The start and end of the pie are defined in units of degrees, with 0 being
    the bottom of the circle and increasing counter-clockwise (e.g. 90 being
    the rightmost point of the circle).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the center of the pie (circle).
        y (int): The Y coordinate of the center of the pie (circle).
        rad (int): The radius (in pixels) of the pie.
        start (int): Start of the pie slice (in degrees).
        end (int): End of the pie slice (in degrees)
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledPieRGBA"](renderer, x, y, rad, start, end, r, g, b, a)


def trigonColor(renderer, x1, y1, x2, y2, x3, y3, color):
    """Draws a trigon (i.e. triangle outline) to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["trigonColor"](renderer, x1, y1, x2, y2, x3, y3, color)

def trigonRGBA(renderer, x1, y1, x2, y2, x3, y3, r, g, b, a):
    """Draws a trigon (i.e. triangle outline) to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["trigonRGBA"](renderer, x1, y1, x2, y2, x3, y3, r, g, b, a)

def aatrigonColor(renderer, x1, y1, x2, y2, x3, y3, color):
    """Draws an anti-aliased trigon (i.e. triangle outline) to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aatrigonColor"](renderer, x1, y1, x2, y2, x3, y3, color)

def aatrigonRGBA(renderer, x1, y1, x2, y2, x3, y3, r, g, b, a):
    """Draws an anti-aliased trigon (i.e. triangle outline) to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aatrigonRGBA"](renderer, x1, y1, x2, y2, x3, y3, r, g, b, a)

def filledTrigonColor(renderer, x1, y1, x2, y2, x3, y3, color):
    """Draws a filled triangle to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledTrigonColor"](renderer, x1, y1, x2, y2, x3, y3, color)

def filledTrigonRGBA(renderer, x1, y1, x2, y2, x3, y3, r, g, b, a):
    """Draws a filled triangle to the renderer in a given color.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x1 (int): X coordinate of the first point of the triangle.
        y1 (int): Y coordinate of the first point of the triangle.
        x2 (int): X coordinate of the second point of the triangle.
        y2 (int): Y coordinate of the second point of the triangle.
        x3 (int): X coordinate of the third point of the triangle.
        y3 (int): Y coordinate of the third point of the triangle.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledTrigonRGBA"](renderer, x1, y1, x2, y2, x3, y3, r, g, b, a)


def polygonColor(renderer, vx, vy, n, color):
    """Draws an unfilled polygon to the renderer in a given color.

    Vertices are specified as ``ctypes.c_int16`` arrays, with two arrays of
    equal size defining the x and y coordinates of the points making up the
    polygon. To create these vertex arrays in Python, you can create lists and
    cast them to ctypes arrays which can be passed directly to the function::

       x_coords = [5, 5, 15, 15]
       y_coords = [5, 10, 10, 5]
       vx = (ctypes.c_int16 * len(x_coords))(*x_coords)
       vy = (ctypes.c_int16 * len(y_coords))(*y_coords)

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["polygonColor"](renderer, vx, vy, n, color)

def polygonRGBA(renderer, vx, vy, n, r, g, b, a):
    """Draws an unfilled polygon to the renderer in a given color.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["polygonRGBA"](renderer, vx, vy, n, r, g, b, a)

def aapolygonColor(renderer, vx, vy, n, color):
    """Draws an anti-aliased unfilled polygon to the renderer in a given color.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aapolygonColor"](renderer, vx, vy, n, color)

def aapolygonRGBA(renderer, vx, vy, n, r, g, b, a):
    """Draws an anti-aliased unfilled polygon to the renderer in a given color.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["aapolygonRGBA"](renderer, vx, vy, n, r, g, b, a)

def filledPolygonColor(renderer, vx, vy, n, color):
    """Draws a filled polygon to the renderer in a given color.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledPolygonColor"](renderer, vx, vy, n, color)

def filledPolygonRGBA(renderer, vx, vy, n, r, g, b, a):
    """Draws a filled polygon to the renderer in a given color.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["filledPolygonRGBA"](renderer, vx, vy, n, r, g, b, a)

def texturedPolygon(renderer, vx, vy, n, texture, texture_dx, texture_dy):
    """Draws a polygon to the renderer with a given texture.

    The location of the texture is relative to the top-left corner of the
    renderer, as opposed to being relative to the polygon itself. As such,
    both the vertex coordinates and texture coordinates need to be adjusted
    equally to render a polygon with the same texture placement at a different
    location.

    The texture must be associated with the same renderer used to draw the
    polygon.

    See :func:`polygonColor` for more information on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the polygon's vertices.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the polygon's vertices.
        n (int): The number of vertices in the polygon.
        texture (:obj:`SDL_Texture`): The texture with which to fill the
            polygon.
        texture_dx (int): The X offset of the texture relative to the top-left
            corner of the renderer.
        texture_dy (int): The Y offset of the texture relative to the top-left
            corner of the renderer.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["texturedPolygon"](
        renderer, vx, vy, n, texture, texture_dx, texture_dy
    )


def bezierColor(renderer, vx, vy, n, s, color):
    """Draws a Bezier curve to the renderer in a given color.

    The first and last vertex are the start and end points of the Bezier,
    respectively, with the points in between defining the control points of the
    curve. For example, a 3rd order (i.e. cubic) Bezier would be defined using
    4 vertices, with the two middle vertices being the control points.

    See :func:`polygonColor` for more information on creating the vertex arrays
    for this function.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the points of the Bezier curve.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the points of the Bezier curve.
        n (int): The number of points in the bezier curve (minimum of 3).
        s (int): The number of interpolation steps to use when drawing the
            curve (minimum of 2). The higher the value, the smoother the curve.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["bezierColor"](renderer, vx, vy, n, s, color)

def bezierRGBA(renderer, vx, vy, n, s, r, g, b, a):
    """Draws a Bezier curve to the renderer in a given color.

    See :func:`bezierColor` for more details on usage.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the X coordinates
            of the points of the Bezier curve.
        vx (POINTER(:obj:`~ctypes.c_int16`)): Array containing the Y coordinates
            of the points of the Bezier curve.
        n (int): The number of points in the bezier curve (minimum of 3).
        s (int): The number of interpolation steps to use when drawing the
            curve (minimum of 2). The higher the value, the smoother the curve.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["bezierRGBA"](renderer, vx, vy, n, s, r, g, b, a)


def gfxPrimitivesSetFont(fontdata, cw, ch):
    """Sets or resets the current global GFX font.

    The SDL_gfx library uses its own special format for bitmap fonts. Basically,
    fonts are byte arrays where each glyph is made up of the same number of
    bytes (as defined by the ``cw`` and ``ch`` arguments). The bytes are used as
    a binary bitmask with 1s indicating the pixels of the character and 0s
    indicating the transparent background. For example, the following is the
    definition of the capital H glyph in the default font:

    .. code-block:: c

       /*
       * 72 0x48 'H' 
       */
       0xc6,			/* 11000110 */
       0xc6,			/* 11000110 */
       0xc6,			/* 11000110 */
       0xfe,			/* 11111110 */
       0xc6,			/* 11000110 */
       0xc6,			/* 11000110 */
       0xc6,			/* 11000110 */
       0x00,			/* 00000000 */

    Each font must contain glyphs for all 256 ASCII characters. Since this is
    a pretty painful format for defining your own fonts, you can load and use
    any of the predefined SDL_gfx fonts from the following link:
    https://github.com/ferzkopp/SDL_gfx/tree/master/Fonts

    If no font has been set, SDL_gfx defaults to rendering with a built-in 8x8
    pixel font.

    .. note::
        If anyone comes up with a way of converting standard bitmap fonts into
        the SDL_gfx format, please let us know! That would be incredibly cool
        and handy.

    Args:
        fontdata (:obj:`~ctypes.c_void_p`): A pointer to the start of the array
            containing the new global font data, or a null pointer to reset the
            global font to the default 8x8 font.
        cw (int): The width (in bytes) of each character of the font. Ignored if
            ``fontdata`` is null.
        ch (int): The height (in bytes) of each character of the font. Ignored
            if ``fontdata`` is null.

    """
    return _ctypes["gfxPrimitivesSetFont"](fontdata, cw, ch)

def gfxPrimitivesSetFontRotation(rotation):
    """Sets the global character rotation for GFX font rendering.

    Characters can only be rotated in 90 degree increments. Calling this
    function will reset the character cache.

    Args:
        rotation (int): The number of clockwise 90-degree rotations to apply to
            font characters when rendering text.

    """
    return _ctypes["gfxPrimitivesSetFontRotation"](rotation)

def characterColor(renderer, x, y, c, color):
    """Draws a single character with the current GFX font to the renderer.

    Python characters can be converted to ASCII integers for use with this
    function using the built-in :func:`ord` function (e.g. ``ord(u"A")``).

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the upper-left corner of the character.
        y (int): The Y coordinate of the upper-left corner of the character.
        c (int): The ASCII number (from 0 to 255) of the character.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["characterColor"](renderer, x, y, c, color)

def characterRGBA(renderer, x, y, c, r, g, b, a):
    """Draws a single character with the current GFX font to the renderer.

    See :func:`characterColor` for more usage information.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the upper-left corner of the character.
        y (int): The Y coordinate of the upper-left corner of the character.
        c (int): The ASCII number (from 0 to 255) of the character.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["characterRGBA"](renderer, x, y, c, r, g, b, a)

def stringColor(renderer, x, y, s, color):
    """Draws an ASCII string with the current GFX font to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the upper-left corner of the string.
        y (int): The Y coordinate of the upper-left corner of the string.
        s (bytes): The ASCII-encoded bytestring of text to render.
        color (int): The color to draw with as a 32-bit ``0xRRGGBBAA`` integer
            (e.g. ``0xFF0000FF`` for solid red).

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["stringColor"](renderer, x, y, s, color)

def stringRGBA(renderer, x, y, s, r, g, b, a):
    """Draws an ASCII string with the current GFX font to the renderer.

    If the rendering color has any transparency, blending will be enabled.

    Args:
        renderer (:obj:`SDL_Renderer`): The renderer to draw on.
        x (int): The X coordinate of the upper-left corner of the string.
        y (int): The Y coordinate of the upper-left corner of the string.
        s (bytes): The ASCII-encoded bytestring of text to render.
        r (int): The red value (from 0 to 255) of the color to draw with.
        g (int): The green value (from 0 to 255) of the color to draw with.
        b (int): The blue value (from 0 to 255) of the color to draw with.
        a (int): The alpha value (from 0 to 255) of the color to draw with.

    Returns:
        int: 0 on success, or -1 on failure.

    """
    return _ctypes["stringRGBA"](renderer, x, y, s, r, g, b, a)


def rotozoomSurface(src, angle, zoom, smooth):
    """Rotates & zooms a surface.

    Rotates and zooms an :obj:`SDL_Surface` to a new output surface, with
    optional anti-aliasing. If the surface is not 8-bit or 32-bit RGBA/ABGR, it
    will be converted into a 32-bit RGBA format on the fly.
    
    Args:
        src (:obj:`SDL_Surface`): The surface to rotate and zoom.
        angle (float): The angle to rotate the surface (in degrees).
        zoom (float): The scaling factor for the surface.
        smooth (int): If set to 1, the output image will be anti-aliased. If set
            to 0, no anti-aliasing will be performed. Must be either 0 or 1.
    
    Returns:
        :obj:`SDL_Surface`: A new output surface with zoom & rotation applied.

    """
    return _ctypes["rotozoomSurface"](src, angle, zoom, smooth)

def rotozoomSurfaceXY(src, angle, zoomx, zoomy, smooth):
    """Rotates & zooms a surface with different x & y scaling factors.

    Rotates and zooms an :obj:`SDL_Surface` to a new output surface, with
    optional anti-aliasing. If the surface is not 8-bit or 32-bit RGBA/ABGR, it
    will be converted into a 32-bit RGBA format on the fly.
    
    Args:
        src (:obj:`SDL_Surface`): The surface to rotate and zoom.
        angle (float): The angle to rotate the surface (in degrees).
        zoomx (float): The x-axis (horizontal) scaling factor.
        zoomy (float): The y-axis (vertical) scaling factor.
        smooth (int): If set to 1, the output image will be anti-aliased. If set
            to 0, no anti-aliasing will be performed. Must be either 0 or 1.
    
    Returns:
        :obj:`SDL_Surface`: A new output surface with zoom & rotation applied.

    """
    return _ctypes["rotozoomSurfaceXY"](src, angle, zoomx, zoomy, smooth)

def rotozoomSurfaceSize(width, height, angle, zoom, dstwidth, dstheight):
    """Returns the output surface size of a :func:`rotozoomSurface` call.

    This function outputs the calculated height and width by reference to the
    ``dstwidth`` and ``dstheight`` arguments, and does not return any value
    itself.

    Args:
        width (int): The width (in pixels) of the source surface.
        height (int): The height (in pixels) of the source surface.
        angle (float): The angle to rotate the surface (in degrees).
        zoom (float): The scaling factor for the surface.
        dstwidth (byref(`c_int`)): A reference to the ctypes int where the
            calculated width of the output surface will be stored.
        dstheight (byref(`c_int`)): A reference to the ctypes int where the
            calculated height of the output surface will be stored.

    """
    return _ctypes["rotozoomSurfaceSize"](
        width, height, angle, zoom, dstwidth, dstheight
    )

def rotozoomSurfaceSizeXY(width, height, angle, zoomx, zoomy, dstwidth, dstheight):
    """Returns the output surface size of a :func:`rotozoomSurfaceXY` call.

    This function outputs the calculated height and width by reference to the
    ``dstwidth`` and ``dstheight`` arguments, and does not return any value
    itself.

    Args:
        width (int): The width (in pixels) of the source surface.
        height (int): The height (in pixels) of the source surface.
        angle (float): The angle to rotate the surface (in degrees).
        zoomx (float): The x-axis (horizontal) scaling factor.
        zoomy (float): The y-axis (vertical) scaling factor.
        dstwidth (byref(`c_int`)): A reference to the ctypes int where the
            calculated width of the output surface will be stored.
        dstheight (byref(`c_int`)): A reference to the ctypes int where the
            calculated height of the output surface will be stored.

    """
    return _ctypes["rotozoomSurfaceSizeXY"](
        width, height, angle, zoomx, zoomy, dstwidth, dstheight
    )

def zoomSurface(src, zoomx, zoomy, smooth):
    """Zooms a surface with different x & y scaling factors.

    This function renders to a new surface, with optional anti-aliasing. If a
    zoom factor is negative, the image will be flipped along that axis. If the
    surface is not 8-bit or 32-bit RGBA/ABGR, it will be converted into a 32-bit
    RGBA format on the fly.

    Args:
        src (:obj:`SDL_Surface`): The surface to zoom.
        zoomx (float): The x-axis (horizontal) zoom factor.
        zoomy (float): The y-axis (vertical) zoom factor.
        smooth (int): If set to 1, the output image will be anti-aliased. If set
            to 0, no anti-aliasing will be performed. Must be either 0 or 1.
    
    Returns:
        :obj:`SDL_Surface`: A new output surface with zoom applied.

    """
    return _ctypes["zoomSurface"](src, zoomx, zoomy, smooth)

def zoomSurfaceSize(width, height, zoomx, zoomy, dstwidth, dstheight):
    """Returns the output surface size of a :func:`zoomSurface` call.

    This function outputs the calculated height and width by reference to the
    ``dstwidth`` and ``dstheight`` arguments, and does not return any value
    itself.

    Args:
        width (int): The width (in pixels) of the source surface.
        height (int): The height (in pixels) of the source surface.
        zoomx (float): The x-axis (horizontal) scaling factor.
        zoomy (float): The y-axis (vertical) scaling factor.
        dstwidth (byref(`c_int`)): A reference to the ctypes int where the
            calculated width of the output surface will be stored.
        dstheight (byref(`c_int`)): A reference to the ctypes int where the
            calculated height of the output surface will be stored.

    """
    return _ctypes["zoomSurfaceSize"](width, height, zoomx, zoomy, dstwidth, dstheight)

def shrinkSurface(src, factorx, factory):
    """Shrinks a surface by an integer ratio using averaging.

    This function renders to a new surface, meaning that the original surface is
    not modified. The output surface is anti-aliased by averaging the source
    RGBA information. If the surface is not 8-bit or 32-bit RGBA/ABGR, it will
    be converted into a 32-bit RGBA format on the fly.

    Args:
        src (:obj:`SDL_Surface`): The surface to zoom.
        factorx (int): The x-axis (horizontal) shrink factor (e.g. 2 = 2x smaller).
        factory (int): The y-axis (vertical) shrink factor (e.g. 2 = 2x smaller).


    Returns:
        :obj:`SDL_Surface`: The new shrunken surface.

    """
    return _ctypes["shrinkSurface"](src, factorx, factory)

def rotateSurface90Degrees(src, numClockwiseTurns):
    """Rotates an SDL surface clockwise in increments of 90 degrees.

    Faster than rotozoomer since no scanning or interpolation takes place.
    Input surface must be 8-bit, 16-bit, 24-bit, or 32-bit.

    Args:
        src (:obj:`SDL_Surface`): The source surface to rotate.
        numClockwiseTurns (int): The number of clockwise 90 degree rotations to
            apply to the source.

    Returns:
        :obj:`SDL_Surface`: The new rotated surface, or `None` if the source
        surface was not a compatible format.

    """
    return _ctypes["rotateSurface90Degrees"](src, numClockwiseTurns)
