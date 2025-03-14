from ctypes import CFUNCTYPE, c_void_p, c_int
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint32, Uint64, SDL_bool

__all__ = [
    # Defines
    "SDL_TimerID",

    # Macro Functions
    "SDL_TICKS_PASSED",

    # Callback Functions
    "SDL_TimerCallback"
]


# Callback function definitions & typedefs

SDL_TimerID = c_int
SDL_TimerCallback = CFUNCTYPE(Uint32, Uint32, c_void_p)


# Macros & inline functions

def SDL_TICKS_PASSED(A, B):
    return ((A - B) & 0xFFFFFFFF) <= 0x80000000


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetTicks", None, Uint32),
    SDLFunc("SDL_GetTicks64", None, Uint64, added='2.0.18'),
    SDLFunc("SDL_GetPerformanceCounter", None, Uint64),
    SDLFunc("SDL_GetPerformanceFrequency", None, Uint64),
    SDLFunc("SDL_Delay", [Uint32]),
    SDLFunc("SDL_AddTimer", [Uint32, SDL_TimerCallback, c_void_p], SDL_TimerID),
    SDLFunc("SDL_RemoveTimer", [SDL_TimerID], SDL_bool),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetTicks = _ctypes["SDL_GetTicks"]
SDL_GetTicks64 = _ctypes["SDL_GetTicks64"]
SDL_GetPerformanceCounter = _ctypes["SDL_GetPerformanceCounter"]
SDL_GetPerformanceFrequency = _ctypes["SDL_GetPerformanceFrequency"]
SDL_Delay = _ctypes["SDL_Delay"]
SDL_AddTimer = _ctypes["SDL_AddTimer"]
SDL_RemoveTimer = _ctypes["SDL_RemoveTimer"]
