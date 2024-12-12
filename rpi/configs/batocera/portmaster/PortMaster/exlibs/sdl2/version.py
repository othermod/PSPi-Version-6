from ctypes import Structure, c_char_p, c_int
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8

__all__ = [
    # Structs
    "SDL_version",

    # Defines
    "SDL_MAJOR_VERSION", "SDL_MINOR_VERSION", "SDL_PATCHLEVEL",

    # Macro Functions
    "SDL_VERSION", "SDL_VERSIONNUM", "SDL_COMPILEDVERSION",
    "SDL_VERSION_ATLEAST",
]


# Constants, enums, & macros

SDL_MAJOR_VERSION = 2
SDL_MINOR_VERSION = 26
SDL_PATCHLEVEL = 0

def SDL_VERSION(x):
    x.major = SDL_MAJOR_VERSION
    x.minor = SDL_MINOR_VERSION
    x.patch = SDL_PATCHLEVEL

SDL_VERSIONNUM = lambda x, y, z: (x * 1000 + y * 100 + z)
SDL_COMPILEDVERSION = SDL_VERSIONNUM(SDL_MAJOR_VERSION, SDL_MINOR_VERSION, SDL_PATCHLEVEL)

def SDL_VERSION_ATLEAST(X, Y, Z):
    return (
        (SDL_MAJOR_VERSION >= X) and
        (SDL_MAJOR_VERSION > X or SDL_MINOR_VERSION >= Y) and
        (SDL_MAJOR_VERSION > X or SDL_MINOR_VERSION > Y or SDL_PATCHLEVEL >= Z)
    )


# Struct definitions

class SDL_version(Structure):
    _fields_ = [
        ("major", Uint8),
        ("minor", Uint8),
        ("patch", Uint8),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetVersion", [_P(SDL_version)]),
    SDLFunc("SDL_GetRevision", None, c_char_p),
    SDLFunc("SDL_GetRevisionNumber", None, c_int),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetVersion = _ctypes["SDL_GetVersion"]
SDL_GetRevision = _ctypes["SDL_GetRevision"]
SDL_GetRevisionNumber = _ctypes["SDL_GetRevisionNumber"] # Deprecated as of 2.0.16, add warning?
