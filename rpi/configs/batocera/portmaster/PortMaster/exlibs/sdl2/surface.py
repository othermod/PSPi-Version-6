from ctypes import CFUNCTYPE, Structure, c_int, c_void_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint32, SDL_bool
from .blendmode import SDL_BlendMode
from .rect import SDL_Rect
from .pixels import SDL_PixelFormat, SDL_Palette
from .rwops import SDL_RWops, SDL_RWFromFile

__all__ = [
    # Structs & Opaque Types
    "SDL_BlitMap", "SDL_Surface",

    # Defines
    "SDL_SWSURFACE", "SDL_PREALLOC", "SDL_RLEACCEL", "SDL_DONTFREE",
    "SDL_SIMD_ALIGNED",

    # Macro Functions
    "SDL_MUSTLOCK", "SDL_LoadBMP", "SDL_SaveBMP",
    
    # Function Aliases
    "SDL_BlitSurface", "SDL_BlitScaled",

    # Callback Functions
    "SDL_blit", "SDL_Blit",
]


# Constants & enums

SDL_SWSURFACE = 0
SDL_PREALLOC = 0x00000001
SDL_RLEACCEL = 0x00000002
SDL_DONTFREE = 0x00000004
SDL_SIMD_ALIGNED = 0x00000008

SDL_YUV_CONVERSION_MODE = c_int
SDL_YUV_CONVERSION_JPEG = 0
SDL_YUV_CONVERSION_BT601 = 1
SDL_YUV_CONVERSION_BT709 = 2
SDL_YUV_CONVERSION_AUTOMATIC = 3


# Macros & inline functions

def SDL_MUSTLOCK(surf):
    if hasattr(surf, "contents"):
        surf = surf.contents
    return surf.flags & SDL_RLEACCEL != 0


# Structs & opaque typedefs

class SDL_BlitMap(c_void_p):
    pass

class SDL_Surface(Structure):
    _fields_ = [
        ("flags", Uint32),
        ("format", _P(SDL_PixelFormat)),
        ("w", c_int), ("h", c_int),
        ("pitch", c_int),
        ("pixels", c_void_p),
        ("userdata", c_void_p),
        ("locked", c_int),
        ("list_blitmap", c_void_p),
        ("clip_rect", SDL_Rect),
        ("map", _P(SDL_BlitMap)),
        ("refcount", c_int),
    ]


# Function type definitions

SDL_blit = CFUNCTYPE(c_int, _P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect))
SDL_Blit = SDL_blit  # for backwards compatibility


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_CreateRGBSurface",
        [Uint32, c_int, c_int, c_int, Uint32, Uint32, Uint32, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("SDL_CreateRGBSurfaceWithFormat",
        [Uint32, c_int, c_int, c_int, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("SDL_CreateRGBSurfaceFrom",
        [c_void_p, c_int, c_int, c_int, c_int, Uint32, Uint32, Uint32, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("SDL_CreateRGBSurfaceWithFormatFrom",
        [c_void_p, c_int, c_int, c_int, c_int, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("SDL_FreeSurface", [_P(SDL_Surface)]),
    SDLFunc("SDL_SetSurfacePalette", [_P(SDL_Surface), _P(SDL_Palette)], c_int),
    SDLFunc("SDL_LockSurface", [_P(SDL_Surface)], c_int),
    SDLFunc("SDL_UnlockSurface", [_P(SDL_Surface)]),
    SDLFunc("SDL_LoadBMP_RW", [_P(SDL_RWops), c_int], _P(SDL_Surface)),
    SDLFunc("SDL_SaveBMP_RW", [_P(SDL_Surface), _P(SDL_RWops), c_int], c_int),
    SDLFunc("SDL_SetSurfaceRLE", [_P(SDL_Surface), c_int], c_int),
    SDLFunc("SDL_HasSurfaceRLE", [_P(SDL_Surface)], SDL_bool, added='2.0.14'),
    SDLFunc("SDL_SetColorKey", [_P(SDL_Surface), c_int, Uint32], c_int),
    SDLFunc("SDL_HasColorKey", [_P(SDL_Surface)], SDL_bool, added='2.0.9'),
    SDLFunc("SDL_GetColorKey", [_P(SDL_Surface), _P(Uint32)], c_int),
    SDLFunc("SDL_SetSurfaceColorMod", [_P(SDL_Surface), Uint8, Uint8, Uint8], c_int),
    SDLFunc("SDL_GetSurfaceColorMod", [_P(SDL_Surface), _P(Uint8), _P(Uint8), _P(Uint8)], c_int),
    SDLFunc("SDL_SetSurfaceAlphaMod", [_P(SDL_Surface), Uint8], c_int),
    SDLFunc("SDL_GetSurfaceAlphaMod", [_P(SDL_Surface), _P(Uint8)], c_int),
    SDLFunc("SDL_SetSurfaceBlendMode", [_P(SDL_Surface), SDL_BlendMode], c_int),
    SDLFunc("SDL_GetSurfaceBlendMode", [_P(SDL_Surface), _P(SDL_BlendMode)], c_int),
    SDLFunc("SDL_SetClipRect", [_P(SDL_Surface), _P(SDL_Rect)], SDL_bool),
    SDLFunc("SDL_GetClipRect", [_P(SDL_Surface), _P(SDL_Rect)]),
    SDLFunc("SDL_DuplicateSurface", [_P(SDL_Surface)], _P(SDL_Surface), added='2.0.6'),
    SDLFunc("SDL_ConvertSurface", [_P(SDL_Surface), _P(SDL_PixelFormat), Uint32], _P(SDL_Surface)),
    SDLFunc("SDL_ConvertSurfaceFormat", [_P(SDL_Surface), Uint32, Uint32], _P(SDL_Surface)),
    SDLFunc("SDL_ConvertPixels",
        [c_int, c_int, Uint32, c_void_p, c_int, Uint32, c_void_p, c_int],
        returns = c_int
    ),
    SDLFunc("SDL_PremultiplyAlpha",
        [c_int, c_int, Uint32, c_void_p, c_int, Uint32, c_void_p, c_int],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_FillRect", [_P(SDL_Surface), _P(SDL_Rect), Uint32], c_int),
    SDLFunc("SDL_FillRects", [_P(SDL_Surface), _P(SDL_Rect), c_int, Uint32], c_int),
    SDLFunc("SDL_UpperBlit",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_LowerBlit",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_SoftStretch",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_SoftStretchLinear",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int, added = '2.0.16'
    ),
    SDLFunc("SDL_UpperBlitScaled",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_LowerBlitScaled",
        [_P(SDL_Surface), _P(SDL_Rect), _P(SDL_Surface), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_SetYUVConversionMode", [SDL_YUV_CONVERSION_MODE], None, added='2.0.8'),
    SDLFunc("SDL_GetYUVConversionMode", None, SDL_YUV_CONVERSION_MODE, added='2.0.8'),
    SDLFunc("SDL_GetYUVConversionModeForResolution",
        [c_int, c_int],
        returns = SDL_YUV_CONVERSION_MODE, added = '2.0.8'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_CreateRGBSurface = _ctypes["SDL_CreateRGBSurface"]
SDL_CreateRGBSurfaceFrom = _ctypes["SDL_CreateRGBSurfaceFrom"]
SDL_CreateRGBSurfaceWithFormat = _ctypes["SDL_CreateRGBSurfaceWithFormat"]
SDL_CreateRGBSurfaceWithFormatFrom = _ctypes["SDL_CreateRGBSurfaceWithFormatFrom"]
SDL_FreeSurface = _ctypes["SDL_FreeSurface"]
SDL_SetSurfacePalette = _ctypes["SDL_SetSurfacePalette"]
SDL_LockSurface = _ctypes["SDL_LockSurface"]
SDL_UnlockSurface = _ctypes["SDL_UnlockSurface"]
SDL_DuplicateSurface = _ctypes["SDL_DuplicateSurface"]

SDL_LoadBMP_RW = _ctypes["SDL_LoadBMP_RW"]
SDL_LoadBMP = lambda fname: SDL_LoadBMP_RW(SDL_RWFromFile(fname, b"rb"), 1)
SDL_SaveBMP_RW = _ctypes["SDL_SaveBMP_RW"]
SDL_SaveBMP = lambda surface, fname: SDL_SaveBMP_RW(surface, SDL_RWFromFile(fname, b"wb"), 1)

SDL_SetSurfaceRLE = _ctypes["SDL_SetSurfaceRLE"]
SDL_HasSurfaceRLE = _ctypes["SDL_HasSurfaceRLE"]
SDL_HasColorKey = _ctypes["SDL_HasColorKey"]
SDL_SetColorKey = _ctypes["SDL_SetColorKey"]
SDL_GetColorKey = _ctypes["SDL_GetColorKey"]
SDL_SetSurfaceColorMod = _ctypes["SDL_SetSurfaceColorMod"]
SDL_GetSurfaceColorMod = _ctypes["SDL_GetSurfaceColorMod"]
SDL_SetSurfaceAlphaMod = _ctypes["SDL_SetSurfaceAlphaMod"]
SDL_GetSurfaceAlphaMod = _ctypes["SDL_GetSurfaceAlphaMod"]
SDL_SetSurfaceBlendMode = _ctypes["SDL_SetSurfaceBlendMode"]
SDL_GetSurfaceBlendMode = _ctypes["SDL_GetSurfaceBlendMode"]
SDL_SetClipRect = _ctypes["SDL_SetClipRect"]
SDL_GetClipRect = _ctypes["SDL_GetClipRect"]
SDL_ConvertSurface = _ctypes["SDL_ConvertSurface"]
SDL_ConvertSurfaceFormat = _ctypes["SDL_ConvertSurfaceFormat"]
SDL_ConvertPixels = _ctypes["SDL_ConvertPixels"]
SDL_PremultiplyAlpha = _ctypes["SDL_PremultiplyAlpha"]
SDL_FillRect = _ctypes["SDL_FillRect"]
SDL_FillRects = _ctypes["SDL_FillRects"]

SDL_UpperBlit = _ctypes["SDL_UpperBlit"]
SDL_BlitSurface = SDL_UpperBlit
SDL_LowerBlit = _ctypes["SDL_LowerBlit"]
SDL_SoftStretch = _ctypes["SDL_SoftStretch"]
SDL_SoftStretchLinear = _ctypes["SDL_SoftStretchLinear"]
SDL_UpperBlitScaled = _ctypes["SDL_UpperBlitScaled"]
SDL_BlitScaled = SDL_UpperBlitScaled
SDL_LowerBlitScaled = _ctypes["SDL_LowerBlitScaled"]

SDL_SetYUVConversionMode = _ctypes["SDL_SetYUVConversionMode"]
SDL_GetYUVConversionMode = _ctypes["SDL_GetYUVConversionMode"]
SDL_GetYUVConversionModeForResolution = _ctypes["SDL_GetYUVConversionModeForResolution"]
