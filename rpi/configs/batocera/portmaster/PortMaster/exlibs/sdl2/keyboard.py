from ctypes import Structure, c_int, c_char_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint16, Uint32, SDL_bool
from .keycode import SDL_Keycode, SDL_Keymod
from .scancode import SDL_Scancode
from .rect import SDL_Rect
from .video import SDL_Window

__all__ = [
    # Structs
    "SDL_Keysym",
]


# Struct definitions

class SDL_Keysym(Structure):
    _fields_ = [
        ("scancode", SDL_Scancode),
        ("sym", SDL_Keycode),
        ("mod", Uint16),
        ("unused", Uint32),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetKeyboardFocus", None, _P(SDL_Window)),
    SDLFunc("SDL_GetKeyboardState", [_P(c_int)], _P(Uint8)),
    SDLFunc("SDL_ResetKeyboard", None, None, added='2.24.0'),
    SDLFunc("SDL_GetModState", None, SDL_Keymod),
    SDLFunc("SDL_SetModState", [SDL_Keymod]),
    SDLFunc("SDL_GetKeyFromScancode", [SDL_Scancode], SDL_Keycode),
    SDLFunc("SDL_GetScancodeFromKey", [SDL_Keycode], SDL_Scancode),
    SDLFunc("SDL_GetScancodeName", [SDL_Scancode], c_char_p),
    SDLFunc("SDL_GetScancodeFromName", [c_char_p], SDL_Scancode),
    SDLFunc("SDL_GetKeyName", [SDL_Keycode], c_char_p),
    SDLFunc("SDL_GetKeyFromName", [c_char_p], SDL_Keycode),
    SDLFunc("SDL_StartTextInput"),
    SDLFunc("SDL_IsTextInputActive", None, SDL_bool),
    SDLFunc("SDL_StopTextInput"),
    SDLFunc("SDL_ClearComposition", added='2.0.22'),
    SDLFunc("SDL_IsTextInputShown", None, SDL_bool, added='2.0.22'),
    SDLFunc("SDL_SetTextInputRect", [_P(SDL_Rect)]),
    SDLFunc("SDL_HasScreenKeyboardSupport", None, SDL_bool),
    SDLFunc("SDL_IsScreenKeyboardShown", [_P(SDL_Window)], SDL_bool),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetKeyboardFocus = _ctypes["SDL_GetKeyboardFocus"]
SDL_GetKeyboardState = _ctypes["SDL_GetKeyboardState"]
SDL_ResetKeyboard = _ctypes["SDL_ResetKeyboard"]
SDL_GetModState = _ctypes["SDL_GetModState"]
SDL_SetModState = _ctypes["SDL_SetModState"]
SDL_GetKeyFromScancode = _ctypes["SDL_GetKeyFromScancode"]
SDL_GetScancodeFromKey = _ctypes["SDL_GetScancodeFromKey"]
SDL_GetScancodeName = _ctypes["SDL_GetScancodeName"]
SDL_GetScancodeFromName = _ctypes["SDL_GetScancodeFromName"]
SDL_GetKeyName = _ctypes["SDL_GetKeyName"]
SDL_GetKeyFromName = _ctypes["SDL_GetKeyFromName"]
SDL_StartTextInput = _ctypes["SDL_StartTextInput"]
SDL_IsTextInputActive = _ctypes["SDL_IsTextInputActive"]
SDL_StopTextInput = _ctypes["SDL_StopTextInput"]
SDL_ClearComposition = _ctypes["SDL_ClearComposition"]
SDL_IsTextInputShown = _ctypes["SDL_IsTextInputShown"]
SDL_SetTextInputRect = _ctypes["SDL_SetTextInputRect"]
SDL_HasScreenKeyboardSupport = _ctypes["SDL_HasScreenKeyboardSupport"]
SDL_IsScreenKeyboardShown = _ctypes["SDL_IsScreenKeyboardShown"]
