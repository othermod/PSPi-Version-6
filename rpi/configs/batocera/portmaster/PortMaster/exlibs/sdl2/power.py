from ctypes import c_int
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict

__all__ = [
    # Enums
    "SDL_PowerState",
    "SDL_POWERSTATE_UNKNOWN", "SDL_POWERSTATE_ON_BATTERY",
    "SDL_POWERSTATE_NO_BATTERY", "SDL_POWERSTATE_CHARGING",
    "SDL_POWERSTATE_CHARGED",
]


# Constants & enums

SDL_PowerState = c_int
SDL_POWERSTATE_UNKNOWN = 0
SDL_POWERSTATE_ON_BATTERY = 1
SDL_POWERSTATE_NO_BATTERY = 2
SDL_POWERSTATE_CHARGING = 3
SDL_POWERSTATE_CHARGED = 4


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetPowerInfo", [_P(c_int), _P(c_int)], SDL_PowerState),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetPowerInfo = _ctypes["SDL_GetPowerInfo"]
