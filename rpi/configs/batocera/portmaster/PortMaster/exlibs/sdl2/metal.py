from ctypes import c_int, c_void_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .video import SDL_Window

# NOTE: These functions are currently untested, but proper usage likely involves
# the use of pyobjc to create an NSView from the created SDL_MetalView.

__all__ = [
    # Opaque Types
    "SDL_MetalView",
]


# Opaque typedefs

class SDL_MetalView(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_Metal_CreateView", [_P(SDL_Window)], SDL_MetalView, added='2.0.12'),
    SDLFunc("SDL_Metal_DestroyView", [SDL_MetalView], None, added='2.0.12'),
    SDLFunc("SDL_Metal_GetLayer", [SDL_MetalView], c_void_p, added='2.0.14'),
    SDLFunc("SDL_Metal_GetDrawableSize",
        [_P(SDL_Window), _P(c_int), _P(c_int)],
        returns = None, added = '2.0.14'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_Metal_CreateView = _ctypes["SDL_Metal_CreateView"]
SDL_Metal_DestroyView = _ctypes["SDL_Metal_DestroyView"]
SDL_Metal_GetLayer = _ctypes["SDL_Metal_GetLayer"]
SDL_Metal_GetDrawableSize = _ctypes["SDL_Metal_GetDrawableSize"]
