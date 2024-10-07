import sys
from .dll import _bind, SDLFunc, AttributeDict
from ctypes import (
    c_int, c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64,
    c_uint64, c_size_t, c_void_p, c_char_p
)

# NOTE: Lots of functions in SDL_stdinc.h are not yet added here, but they're
# mostly for math and string operations that Python can do much more easily.

__all__ = [
    # Defines
    "Sint8", "Uint8", "Sint16", "Uint16", "Sint32", "Uint32",
    "Sint64", "Uint64",

    # Constants
    "SDL_FLT_EPSILON",

    # Enums
    "SDL_bool",
    "SDL_FALSE", "SDL_TRUE",
    
    # Macro Functions
    "SDL_min", "SDL_max", "SDL_clamp",
]


# Constants, enums, & typedefs

SDL_FLT_EPSILON = sys.float_info.epsilon

SDL_bool = c_int
SDL_FALSE = 0
SDL_TRUE = 1

Sint8 = c_int8
Uint8 = c_uint8
Sint16 = c_int16
Uint16 = c_uint16
Sint32 = c_int32
Uint32 = c_uint32
Sint64 = c_int64
Uint64 = c_uint64


# Macro & inline functions

SDL_min = min
SDL_max = max

def SDL_clamp(x, a, b):
    if x < a:
        return a
    elif x > b:
        return b
    else:
        return x


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_malloc", [c_size_t], c_void_p),
    SDLFunc("SDL_calloc", [c_size_t, c_size_t], c_void_p),
    SDLFunc("SDL_realloc", [c_void_p, c_size_t], c_void_p),
    SDLFunc("SDL_free", [c_void_p], None),
    SDLFunc("SDL_getenv", [c_char_p], c_char_p),
    SDLFunc("SDL_setenv", [c_char_p, c_char_p, c_int], c_int),
    SDLFunc("SDL_abs", [c_int], c_int),
    SDLFunc("SDL_memset", [c_void_p, c_int, c_size_t], c_void_p),
    SDLFunc("SDL_memcpy", [c_void_p, c_void_p, c_size_t], c_void_p),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_malloc = _ctypes["SDL_malloc"]
SDL_calloc = _ctypes["SDL_calloc"]
SDL_realloc = _ctypes["SDL_realloc"]
SDL_free = _ctypes["SDL_free"]
SDL_getenv = _ctypes["SDL_getenv"]
SDL_setenv = _ctypes["SDL_setenv"]
SDL_abs = _ctypes["SDL_abs"]
SDL_memset = _ctypes["SDL_memset"]
SDL_memcpy = _ctypes["SDL_memcpy"]
