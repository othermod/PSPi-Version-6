from ctypes import Union, Structure, c_char_p, c_uint, c_int
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint32, SDL_bool
from .pixels import SDL_Color
from .surface import SDL_Surface
from .video import SDL_Window

__all__ = [
    # Structs & Unions
    "SDL_WindowShapeParams", "SDL_WindowShapeMode",

    # Defines
    "SDL_NONSHAPEABLE_WINDOW", "SDL_INVALID_SHAPE_ARGUMENT",
    "SDL_WINDOW_LACKS_SHAPE",

    # Enums
    "WindowShapeMode",
    "ShapeModeDefault", "ShapeModeBinarizeAlpha",
    "ShapeModeReverseBinarizeAlpha", "ShapeModeColorKey",

    # Macro Functions
    "SDL_SHAPEMODEALPHA",
]


# Constants & enums

SDL_NONSHAPEABLE_WINDOW = -1
SDL_INVALID_SHAPE_ARGUMENT = -2
SDL_WINDOW_LACKS_SHAPE = -3

WindowShapeMode = c_int
ShapeModeDefault = 0
ShapeModeBinarizeAlpha = 1
ShapeModeReverseBinarizeAlpha = 2
ShapeModeColorKey = 3


# Macros & inline functions

def SDL_SHAPEMODEALPHA(mode):
    return ShapeModeDefault <= mode <= ShapeModeReverseBinarizeAlpha


# Struct definitions

class SDL_WindowShapeParams(Union):
    _fields_ = [
        ("binarizationCutoff", Uint8),
        ("colorKey", SDL_Color),
    ]

class SDL_WindowShapeMode(Structure):
    _fields_ = [
        ("mode", WindowShapeMode),
        ("parameters", SDL_WindowShapeParams),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_CreateShapedWindow",
        [c_char_p, c_uint, c_uint, c_uint, c_uint, Uint32],
        returns = _P(SDL_Window)
    ),
    SDLFunc("SDL_IsShapedWindow", [_P(SDL_Window)], SDL_bool),
    SDLFunc("SDL_SetWindowShape",
        [_P(SDL_Window), _P(SDL_Surface), _P(SDL_WindowShapeMode)],
        returns = c_int
    ),
    SDLFunc("SDL_GetShapedWindowMode", [_P(SDL_Window), _P(SDL_WindowShapeMode)], c_int),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_CreateShapedWindow = _ctypes["SDL_CreateShapedWindow"]
SDL_IsShapedWindow = _ctypes["SDL_IsShapedWindow"]
SDL_SetWindowShape = _ctypes["SDL_SetWindowShape"]
SDL_GetShapedWindowMode = _ctypes["SDL_GetShapedWindowMode"]
