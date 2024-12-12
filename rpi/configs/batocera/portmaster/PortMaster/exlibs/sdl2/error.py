from ctypes import c_char_p, c_int, c_char
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict

__all__ = [
    # Enums
    "SDL_errorcode",
    "SDL_ENOMEM", "SDL_EFREAD", "SDL_EFWRITE", "SDL_EFSEEK",
    "SDL_UNSUPPORTED", "SDL_LASTERROR",

    # Macro Functions
    "SDL_OutOfMemory", "SDL_Unsupported", "SDL_InvalidParamError",
]


# Constants & enums

SDL_errorcode = c_int
SDL_ENOMEM = 0
SDL_EFREAD = 1
SDL_EFWRITE = 2
SDL_EFSEEK = 3
SDL_UNSUPPORTED = 4
SDL_LASTERROR = 5


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_SetError", [c_char_p], c_int),
    SDLFunc("SDL_GetError", None, c_char_p),
    SDLFunc("SDL_GetErrorMsg", [_P(c_char), c_int], c_char_p, added='2.0.14'),
    SDLFunc("SDL_ClearError"),
    SDLFunc("SDL_Error", [SDL_errorcode], c_int),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_SetError = _ctypes["SDL_SetError"]
SDL_GetError = _ctypes["SDL_GetError"]
SDL_GetErrorMsg = _ctypes["SDL_GetErrorMsg"]
SDL_ClearError = _ctypes["SDL_ClearError"]
SDL_Error = _ctypes["SDL_Error"]

SDL_OutOfMemory = SDL_Error(SDL_ENOMEM)
SDL_Unsupported = SDL_Error(SDL_UNSUPPORTED)

def SDL_InvalidParamError(x):
    return SDL_SetError("Parameter '%s' is invalid" % (x))
