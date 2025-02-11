from ctypes import c_int, c_char_p, c_void_p, CFUNCTYPE
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict

__all__ = [
    # Defines
    "SDL_MAX_LOG_MESSAGE", 
    
    # Enums
    "SDL_LogCategory",
    "SDL_LOG_CATEGORY_APPLICATION",
    "SDL_LOG_CATEGORY_ERROR", "SDL_LOG_CATEGORY_ASSERT",
    "SDL_LOG_CATEGORY_SYSTEM", "SDL_LOG_CATEGORY_AUDIO",
    "SDL_LOG_CATEGORY_VIDEO", "SDL_LOG_CATEGORY_RENDER",
    "SDL_LOG_CATEGORY_INPUT", "SDL_LOG_CATEGORY_TEST",
    "SDL_LOG_CATEGORY_RESERVED1", "SDL_LOG_CATEGORY_RESERVED2",
    "SDL_LOG_CATEGORY_RESERVED3", "SDL_LOG_CATEGORY_RESERVED4",
    "SDL_LOG_CATEGORY_RESERVED5", "SDL_LOG_CATEGORY_RESERVED6",
    "SDL_LOG_CATEGORY_RESERVED7", "SDL_LOG_CATEGORY_RESERVED8",
    "SDL_LOG_CATEGORY_RESERVED9", "SDL_LOG_CATEGORY_RESERVED10",
    "SDL_LOG_CATEGORY_CUSTOM",

    "SDL_LogPriority",
    "SDL_LOG_PRIORITY_VERBOSE",
    "SDL_LOG_PRIORITY_DEBUG", "SDL_LOG_PRIORITY_INFO",
    "SDL_LOG_PRIORITY_WARN", "SDL_LOG_PRIORITY_ERROR",
    "SDL_LOG_PRIORITY_CRITICAL", "SDL_NUM_LOG_PRIORITIES",

    # Callback Functions
    "SDL_LogOutputFunction",
]


# Constants & enums

SDL_MAX_LOG_MESSAGE = 4096

SDL_LogCategory = c_int
SDL_LOG_CATEGORY_APPLICATION = 0
SDL_LOG_CATEGORY_ERROR = 1
SDL_LOG_CATEGORY_ASSERT = 2
SDL_LOG_CATEGORY_SYSTEM = 3
SDL_LOG_CATEGORY_AUDIO = 4
SDL_LOG_CATEGORY_VIDEO = 5
SDL_LOG_CATEGORY_RENDER = 6
SDL_LOG_CATEGORY_INPUT = 7
SDL_LOG_CATEGORY_TEST = 8
SDL_LOG_CATEGORY_RESERVED1 = 9
SDL_LOG_CATEGORY_RESERVED2 = 10
SDL_LOG_CATEGORY_RESERVED3 = 11
SDL_LOG_CATEGORY_RESERVED4 = 12
SDL_LOG_CATEGORY_RESERVED5 = 13
SDL_LOG_CATEGORY_RESERVED6 = 14
SDL_LOG_CATEGORY_RESERVED7 = 15
SDL_LOG_CATEGORY_RESERVED8 = 16
SDL_LOG_CATEGORY_RESERVED9 = 17
SDL_LOG_CATEGORY_RESERVED10 = 18
SDL_LOG_CATEGORY_CUSTOM = 19

SDL_LogPriority = c_int
SDL_LOG_PRIORITY_VERBOSE = 1
SDL_LOG_PRIORITY_DEBUG = 2
SDL_LOG_PRIORITY_INFO = 3
SDL_LOG_PRIORITY_WARN = 4
SDL_LOG_PRIORITY_ERROR = 5
SDL_LOG_PRIORITY_CRITICAL = 6
SDL_NUM_LOG_PRIORITIES = 7


# Callback function definitions

SDL_LogOutputFunction = CFUNCTYPE(None, c_void_p, c_int, SDL_LogPriority, c_char_p)


# Raw ctypes function definitions

# TODO: do we want SDL_LogMessageV?
_funcdefs = [
    SDLFunc("SDL_LogSetAllPriority", [SDL_LogPriority]),
    SDLFunc("SDL_LogSetPriority", [c_int, SDL_LogPriority]),
    SDLFunc("SDL_LogGetPriority", [c_int], SDL_LogPriority),
    SDLFunc("SDL_LogResetPriorities"),
    SDLFunc("SDL_Log", [c_char_p]),
    SDLFunc("SDL_LogVerbose", [c_int, c_char_p]),
    SDLFunc("SDL_LogDebug", [c_int, c_char_p]),
    SDLFunc("SDL_LogInfo", [c_int, c_char_p]),
    SDLFunc("SDL_LogWarn", [c_int, c_char_p]),
    SDLFunc("SDL_LogError", [c_int, c_char_p]),
    SDLFunc("SDL_LogCritical", [c_int, c_char_p]),
    SDLFunc("SDL_LogMessage", [c_int, SDL_LogPriority, c_char_p]),
    SDLFunc("SDL_LogGetOutputFunction", [_P(SDL_LogOutputFunction), c_void_p]),
    SDLFunc("SDL_LogSetOutputFunction", [SDL_LogOutputFunction, c_void_p]),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_LogSetAllPriority = _ctypes["SDL_LogSetAllPriority"]
SDL_LogSetPriority = _ctypes["SDL_LogSetPriority"]
SDL_LogGetPriority = _ctypes["SDL_LogGetPriority"]
SDL_LogResetPriorities = _ctypes["SDL_LogResetPriorities"]
SDL_Log = _ctypes["SDL_Log"]
SDL_LogVerbose = _ctypes["SDL_LogVerbose"]
SDL_LogDebug = _ctypes["SDL_LogDebug"]
SDL_LogInfo = _ctypes["SDL_LogInfo"]
SDL_LogWarn = _ctypes["SDL_LogWarn"]
SDL_LogError = _ctypes["SDL_LogError"]
SDL_LogCritical = _ctypes["SDL_LogCritical"]
SDL_LogMessage = _ctypes["SDL_LogMessage"]
SDL_LogGetOutputFunction = _ctypes["SDL_LogGetOutputFunction"]
SDL_LogSetOutputFunction = _ctypes["SDL_LogSetOutputFunction"]
