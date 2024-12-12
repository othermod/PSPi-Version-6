import sys
from ctypes import c_int, c_char_p
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8
from .joystick import SDL_JoystickGUID

__all__ = [
    # Defines
    "SDL_GUID",
]


# Constants & typedefs

SDL_GUID = SDL_JoystickGUID


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GUIDToString", [SDL_GUID, c_char_p, c_int], None, added='2.23.1'),
    SDLFunc("SDL_GUIDFromString", [c_char_p], SDL_GUID, added='2.23.1'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace

# Workaround for bizarre ctypes bug with older Python versions
# (The joystick function here is a thin wrapper around SDL_GUIDToString)
if sys.version_info < (3, 7, 0):
    from .joystick import SDL_JoystickGetGUIDString
    _ctypes["SDL_GUIDToString"] = SDL_JoystickGetGUIDString


# Aliases for ctypes bindings

def SDL_GUIDToString(guid, pszGUID, cbGUID):
    return _ctypes["SDL_GUIDToString"](guid, pszGUID, cbGUID)

def SDL_GUIDFromString(pchGUID):
    return _ctypes["SDL_GUIDFromString"](pchGUID)
