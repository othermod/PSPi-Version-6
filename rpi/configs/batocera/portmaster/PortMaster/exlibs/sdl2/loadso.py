from ctypes import c_char_p, c_void_p
from .dll import _bind, SDLFunc, AttributeDict

__all__ = []


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_LoadObject", [c_char_p], c_void_p),
    SDLFunc("SDL_LoadFunction", [c_void_p, c_char_p], c_void_p),
    SDLFunc("SDL_UnloadObject", [c_void_p]),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_LoadObject = _ctypes["SDL_LoadObject"]
SDL_LoadFunction = _ctypes["SDL_LoadFunction"]
SDL_UnloadObject = _ctypes["SDL_UnloadObject"]
