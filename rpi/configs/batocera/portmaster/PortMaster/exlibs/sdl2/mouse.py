from ctypes import Structure, c_int, c_void_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint32, SDL_bool
from .video import SDL_Window
from .surface import SDL_Surface

__all__ = [
    # Opaque Types
    "SDL_Cursor",
    
    # Defines
    "SDL_BUTTON_LEFT", "SDL_BUTTON_MIDDLE", "SDL_BUTTON_RIGHT",
    "SDL_BUTTON_X1", "SDL_BUTTON_X2",

    # Enums
    "SDL_SystemCursor",
    "SDL_SYSTEM_CURSOR_ARROW", "SDL_SYSTEM_CURSOR_IBEAM",
    "SDL_SYSTEM_CURSOR_WAIT", "SDL_SYSTEM_CURSOR_CROSSHAIR",
    "SDL_SYSTEM_CURSOR_WAITARROW", "SDL_SYSTEM_CURSOR_SIZENWSE",
    "SDL_SYSTEM_CURSOR_SIZENESW", "SDL_SYSTEM_CURSOR_SIZEWE",
    "SDL_SYSTEM_CURSOR_SIZENS", "SDL_SYSTEM_CURSOR_SIZEALL",
    "SDL_SYSTEM_CURSOR_NO", "SDL_SYSTEM_CURSOR_HAND", "SDL_NUM_SYSTEM_CURSORS",

    "SDL_MouseWheelDirection",
    "SDL_MOUSEWHEEL_NORMAL", "SDL_MOUSEWHEEL_FLIPPED",

    # Macro Functions
    "SDL_BUTTON", "SDL_BUTTON_LMASK", "SDL_BUTTON_MMASK",
    "SDL_BUTTON_RMASK", "SDL_BUTTON_X1MASK", "SDL_BUTTON_X2MASK",
]


# Constants, macros, & enums

SDL_SystemCursor = c_int
SDL_SYSTEM_CURSOR_ARROW = 0
SDL_SYSTEM_CURSOR_IBEAM = 1
SDL_SYSTEM_CURSOR_WAIT = 2
SDL_SYSTEM_CURSOR_CROSSHAIR = 3
SDL_SYSTEM_CURSOR_WAITARROW = 4
SDL_SYSTEM_CURSOR_SIZENWSE = 5
SDL_SYSTEM_CURSOR_SIZENESW = 6
SDL_SYSTEM_CURSOR_SIZEWE = 7
SDL_SYSTEM_CURSOR_SIZENS = 8
SDL_SYSTEM_CURSOR_SIZEALL = 9
SDL_SYSTEM_CURSOR_NO = 10
SDL_SYSTEM_CURSOR_HAND = 11
SDL_NUM_SYSTEM_CURSORS = 12

SDL_MouseWheelDirection = c_int
SDL_MOUSEWHEEL_NORMAL = 0
SDL_MOUSEWHEEL_FLIPPED = 1

SDL_BUTTON = lambda X: (1 << ((X) - 1))
SDL_BUTTON_LEFT = 1
SDL_BUTTON_MIDDLE = 2
SDL_BUTTON_RIGHT = 3
SDL_BUTTON_X1 = 4
SDL_BUTTON_X2 = 5
SDL_BUTTON_LMASK = SDL_BUTTON(SDL_BUTTON_LEFT)
SDL_BUTTON_MMASK = SDL_BUTTON(SDL_BUTTON_MIDDLE)
SDL_BUTTON_RMASK = SDL_BUTTON(SDL_BUTTON_RIGHT)
SDL_BUTTON_X1MASK = SDL_BUTTON(SDL_BUTTON_X1)
SDL_BUTTON_X2MASK = SDL_BUTTON(SDL_BUTTON_X2)


# Structs & opaque typedefs

class SDL_Cursor(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetMouseFocus", None, _P(SDL_Window)),
    SDLFunc("SDL_GetMouseState", [_P(c_int), _P(c_int)], Uint32),
    SDLFunc("SDL_GetRelativeMouseState", [_P(c_int), _P(c_int)], Uint32),
    SDLFunc("SDL_WarpMouseInWindow", [_P(SDL_Window), c_int, c_int]),
    SDLFunc("SDL_SetRelativeMouseMode", [SDL_bool], c_int),
    SDLFunc("SDL_GetRelativeMouseMode", None, SDL_bool),
    SDLFunc("SDL_CreateCursor",
        [_P(Uint8), _P(Uint8), c_int, c_int, c_int, c_int],
        returns = _P(SDL_Cursor)
    ),
    SDLFunc("SDL_CreateColorCursor", [_P(SDL_Surface), c_int, c_int], _P(SDL_Cursor)),
    SDLFunc("SDL_CreateSystemCursor", [SDL_SystemCursor], _P(SDL_Cursor)),
    SDLFunc("SDL_SetCursor", [_P(SDL_Cursor)]),
    SDLFunc("SDL_GetCursor", None, _P(SDL_Cursor)),
    SDLFunc("SDL_GetDefaultCursor", None, _P(SDL_Cursor)),
    SDLFunc("SDL_FreeCursor", [_P(SDL_Cursor)]),
    SDLFunc("SDL_ShowCursor", [c_int], c_int),
    SDLFunc("SDL_WarpMouseGlobal", [c_int, c_int], c_int, added='2.0.4'),
    SDLFunc("SDL_CaptureMouse", [SDL_bool], c_int, added='2.0.4'),
    SDLFunc("SDL_GetGlobalMouseState", [_P(c_int), _P(c_int)], Uint32, added='2.0.4'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetMouseFocus = _ctypes["SDL_GetMouseFocus"]
SDL_GetMouseState = _ctypes["SDL_GetMouseState"]
SDL_GetRelativeMouseState = _ctypes["SDL_GetRelativeMouseState"]
SDL_WarpMouseInWindow = _ctypes["SDL_WarpMouseInWindow"]
SDL_SetRelativeMouseMode = _ctypes["SDL_SetRelativeMouseMode"]
SDL_GetRelativeMouseMode = _ctypes["SDL_GetRelativeMouseMode"]
SDL_CreateCursor = _ctypes["SDL_CreateCursor"]
SDL_CreateColorCursor = _ctypes["SDL_CreateColorCursor"]
SDL_CreateSystemCursor = _ctypes["SDL_CreateSystemCursor"]
SDL_SetCursor = _ctypes["SDL_SetCursor"]
SDL_GetCursor = _ctypes["SDL_GetCursor"]
SDL_GetDefaultCursor = _ctypes["SDL_GetDefaultCursor"]
SDL_FreeCursor = _ctypes["SDL_FreeCursor"]
SDL_ShowCursor = _ctypes["SDL_ShowCursor"]
SDL_WarpMouseGlobal = _ctypes["SDL_WarpMouseGlobal"]
SDL_CaptureMouse = _ctypes["SDL_CaptureMouse"]
SDL_GetGlobalMouseState = _ctypes["SDL_GetGlobalMouseState"]
