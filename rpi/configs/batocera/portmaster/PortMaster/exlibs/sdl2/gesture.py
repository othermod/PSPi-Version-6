from ctypes import c_int
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Sint64
from .touch import SDL_TouchID
from .rwops import SDL_RWops

__all__ = [
    # Defines
    "SDL_GestureID",
]


# Constants & typedefs

SDL_GestureID = Sint64


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_RecordGesture", [SDL_TouchID], c_int),
    SDLFunc("SDL_SaveAllDollarTemplates", [_P(SDL_RWops)], c_int),
    SDLFunc("SDL_SaveDollarTemplate", [SDL_GestureID, _P(SDL_RWops)], c_int),
    SDLFunc("SDL_LoadDollarTemplates", [SDL_TouchID, _P(SDL_RWops)], c_int),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_RecordGesture = _ctypes["SDL_RecordGesture"]
SDL_SaveAllDollarTemplates = _ctypes["SDL_SaveAllDollarTemplates"]
SDL_SaveDollarTemplate = _ctypes["SDL_SaveDollarTemplate"]
SDL_LoadDollarTemplates = _ctypes["SDL_LoadDollarTemplates"]
