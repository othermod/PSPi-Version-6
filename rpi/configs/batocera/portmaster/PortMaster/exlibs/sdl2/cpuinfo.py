from ctypes import c_int, c_size_t, c_void_p
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import SDL_bool

__all__ = [
    # Defines
    "SDL_CACHELINE_SIZE",
]


# Constants & enums

SDL_CACHELINE_SIZE = 128


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetCPUCount", None, c_int),
    SDLFunc("SDL_GetCPUCacheLineSize", None, c_int),
    SDLFunc("SDL_HasRDTSC", None, SDL_bool),
    SDLFunc("SDL_HasAltiVec", None, SDL_bool),
    SDLFunc("SDL_HasMMX", None, SDL_bool),
    SDLFunc("SDL_Has3DNow", None, SDL_bool),
    SDLFunc("SDL_HasSSE", None, SDL_bool),
    SDLFunc("SDL_HasSSE2", None, SDL_bool),
    SDLFunc("SDL_HasSSE3", None, SDL_bool),
    SDLFunc("SDL_HasSSE41", None, SDL_bool),
    SDLFunc("SDL_HasSSE42", None, SDL_bool),
    SDLFunc("SDL_GetSystemRAM", None, c_int),
    SDLFunc("SDL_HasAVX", None, SDL_bool),
    SDLFunc("SDL_HasAVX2", None, SDL_bool, added='2.0.4'),
    SDLFunc("SDL_HasAVX512F", None, SDL_bool, added='2.0.9'),
    SDLFunc("SDL_HasARMSIMD", None, SDL_bool, added='2.0.12'),
    SDLFunc("SDL_HasNEON", None, SDL_bool, added='2.0.6'),
    SDLFunc("SDL_HasLSX", None, SDL_bool, added='2.23.1'),
    SDLFunc("SDL_HasLASX", None, SDL_bool, added='2.23.1'),
    SDLFunc("SDL_SIMDGetAlignment", None, c_size_t, added='2.0.10'),
    SDLFunc("SDL_SIMDAlloc", [c_size_t], c_void_p, added='2.0.10'),
    SDLFunc("SDL_SIMDRealloc", [c_void_p, c_size_t], c_void_p, added='2.0.14'),
    SDLFunc("SDL_SIMDFree", [c_void_p], None, added='2.0.10'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetCPUCount = _ctypes["SDL_GetCPUCount"]
SDL_GetCPUCacheLineSize = _ctypes["SDL_GetCPUCacheLineSize"]
SDL_HasRDTSC = _ctypes["SDL_HasRDTSC"]
SDL_HasAltiVec = _ctypes["SDL_HasAltiVec"]
SDL_HasMMX = _ctypes["SDL_HasMMX"]
SDL_Has3DNow = _ctypes["SDL_Has3DNow"]
SDL_HasSSE = _ctypes["SDL_HasSSE"]
SDL_HasSSE2 = _ctypes["SDL_HasSSE2"]
SDL_HasSSE3 = _ctypes["SDL_HasSSE3"]
SDL_HasSSE41 = _ctypes["SDL_HasSSE41"]
SDL_HasSSE42 = _ctypes["SDL_HasSSE42"]
SDL_GetSystemRAM = _ctypes["SDL_GetSystemRAM"]
SDL_HasAVX = _ctypes["SDL_HasAVX"]
SDL_HasAVX2 = _ctypes["SDL_HasAVX2"]
SDL_HasAVX512F = _ctypes["SDL_HasAVX512F"]
SDL_HasARMSIMD = _ctypes["SDL_HasARMSIMD"]
SDL_HasNEON = _ctypes["SDL_HasNEON"]
SDL_HasLSX = _ctypes["SDL_HasLSX"]
SDL_HasLASX = _ctypes["SDL_HasLASX"]
SDL_SIMDGetAlignment = _ctypes["SDL_SIMDGetAlignment"]
SDL_SIMDAlloc = _ctypes["SDL_SIMDAlloc"]
SDL_SIMDRealloc = _ctypes["SDL_SIMDRealloc"]
SDL_SIMDFree = _ctypes["SDL_SIMDFree"]
