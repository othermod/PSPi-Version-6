from ctypes import c_int
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint32

__all__ = [
    # Constants
    "SDL_INIT_TIMER", "SDL_INIT_AUDIO", "SDL_INIT_VIDEO", "SDL_INIT_JOYSTICK",
    "SDL_INIT_HAPTIC", "SDL_INIT_GAMECONTROLLER", "SDL_INIT_EVENTS",
    "SDL_INIT_SENSOR", "SDL_INIT_NOPARACHUTE", "SDL_INIT_EVERYTHING",
]

# Constants & enums

SDL_INIT_TIMER = 0x00000001
SDL_INIT_AUDIO = 0x00000010
SDL_INIT_VIDEO = 0x00000020
SDL_INIT_JOYSTICK = 0x00000200
SDL_INIT_HAPTIC = 0x00001000
SDL_INIT_GAMECONTROLLER = 0x00002000
SDL_INIT_EVENTS = 0x00004000
SDL_INIT_SENSOR = 0x00008000
SDL_INIT_NOPARACHUTE = 0x00100000
SDL_INIT_EVERYTHING = (
    SDL_INIT_TIMER | SDL_INIT_AUDIO | SDL_INIT_VIDEO | SDL_INIT_EVENTS |
    SDL_INIT_JOYSTICK | SDL_INIT_HAPTIC | SDL_INIT_GAMECONTROLLER |
    SDL_INIT_SENSOR
)


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_Init", [Uint32], c_int),
    SDLFunc("SDL_InitSubSystem", [Uint32], c_int),
    SDLFunc("SDL_QuitSubSystem", [Uint32]),
    SDLFunc("SDL_WasInit", [Uint32], Uint32),
    SDLFunc("SDL_Quit"),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_Init = _ctypes["SDL_Init"]
SDL_InitSubSystem = _ctypes["SDL_InitSubSystem"]
SDL_QuitSubSystem = _ctypes["SDL_QuitSubSystem"]
SDL_WasInit = _ctypes["SDL_WasInit"]
SDL_Quit = _ctypes["SDL_Quit"]
