import sys
from ctypes import Structure, c_int, c_char_p, c_void_p, CFUNCTYPE
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Sint16, Sint32, Uint32, Uint16, Uint8, SDL_bool

__all__ = [
    # Structs & Opaque Types
    "SDL_Joystick", "SDL_JoystickGUID", "SDL_VirtualJoystickDesc",
    
    # Defines
    "SDL_JoystickID", "SDL_HAT_CENTERED", "SDL_HAT_UP", "SDL_HAT_RIGHT",
    "SDL_HAT_DOWN", "SDL_HAT_LEFT", "SDL_HAT_RIGHTUP", "SDL_HAT_RIGHTDOWN",
    "SDL_HAT_LEFTUP", "SDL_HAT_LEFTDOWN", "SDL_IPHONE_MAX_GFORCE",
    "SDL_VIRTUAL_JOYSTICK_DESC_VERSION",

    # Enums
    "SDL_JoystickType",
    "SDL_JOYSTICK_TYPE_UNKNOWN", "SDL_JOYSTICK_TYPE_GAMECONTROLLER",
    "SDL_JOYSTICK_TYPE_WHEEL", "SDL_JOYSTICK_TYPE_ARCADE_STICK",
    "SDL_JOYSTICK_TYPE_FLIGHT_STICK", "SDL_JOYSTICK_TYPE_DANCE_PAD",
    "SDL_JOYSTICK_TYPE_GUITAR", "SDL_JOYSTICK_TYPE_DRUM_KIT",
    "SDL_JOYSTICK_TYPE_ARCADE_PAD", "SDL_JOYSTICK_TYPE_THROTTLE",

    "SDL_JoystickPowerLevel",
    "SDL_JOYSTICK_POWER_UNKNOWN", "SDL_JOYSTICK_POWER_EMPTY",
    "SDL_JOYSTICK_POWER_LOW", "SDL_JOYSTICK_POWER_MEDIUM",
    "SDL_JOYSTICK_POWER_FULL", "SDL_JOYSTICK_POWER_WIRED",
    "SDL_JOYSTICK_POWER_MAX",
]


# Constants & enums

SDL_JoystickPowerLevel = c_int
SDL_JOYSTICK_POWER_UNKNOWN = -1
SDL_JOYSTICK_POWER_EMPTY = 0
SDL_JOYSTICK_POWER_LOW = 1
SDL_JOYSTICK_POWER_MEDIUM = 2
SDL_JOYSTICK_POWER_FULL = 3
SDL_JOYSTICK_POWER_WIRED = 4
SDL_JOYSTICK_POWER_MAX = 5

SDL_JoystickType = c_int
SDL_JOYSTICK_TYPE_UNKNOWN = 0
SDL_JOYSTICK_TYPE_GAMECONTROLLER = 1
SDL_JOYSTICK_TYPE_WHEEL = 2
SDL_JOYSTICK_TYPE_ARCADE_STICK = 3
SDL_JOYSTICK_TYPE_FLIGHT_STICK = 4
SDL_JOYSTICK_TYPE_DANCE_PAD = 5
SDL_JOYSTICK_TYPE_GUITAR = 6
SDL_JOYSTICK_TYPE_DRUM_KIT = 7
SDL_JOYSTICK_TYPE_ARCADE_PAD = 8
SDL_JOYSTICK_TYPE_THROTTLE = 9

SDL_IPHONE_MAX_GFORCE = 5.0

SDL_HAT_CENTERED = 0x00
SDL_HAT_UP = 0x01
SDL_HAT_RIGHT = 0x02
SDL_HAT_DOWN = 0x04
SDL_HAT_LEFT = 0x08
SDL_HAT_RIGHTUP = SDL_HAT_RIGHT | SDL_HAT_UP
SDL_HAT_RIGHTDOWN = SDL_HAT_RIGHT | SDL_HAT_DOWN
SDL_HAT_LEFTUP = SDL_HAT_LEFT | SDL_HAT_UP
SDL_HAT_LEFTDOWN = SDL_HAT_LEFT | SDL_HAT_DOWN

SDL_VIRTUAL_JOYSTICK_DESC_VERSION = 1


# Structs & typedefs

SDL_JoystickID = Sint32

class SDL_JoystickGUID(Structure):
    _fields_ = [("data", (Uint8 * 16))]

class SDL_Joystick(c_void_p):
    pass

# TODO: Document these somewhere
CFUNC_Update = CFUNCTYPE(None, c_void_p)
CFUNC_SetPlayerIndex = CFUNCTYPE(None, c_void_p, c_int)
CFUNC_Rumble = CFUNCTYPE(c_int, c_void_p, Uint16, Uint16)
CFUNC_RumbleTriggers = CFUNCTYPE(c_int, c_void_p, Uint16, Uint16)
CFUNC_SetLED = CFUNCTYPE(c_int, c_void_p, Uint8, Uint8, Uint8)
CFUNC_SendEffect = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int)

class SDL_VirtualJoystickDesc(Structure):
    _fields_ = [
        ("version", Uint16),
        ("type", Uint16),
        ("naxes", Uint16),
        ("nbuttons", Uint16),
        ("nhats", Uint16),
        ("vendor_id", Uint16),
        ("product_id", Uint16),
        ("padding", Uint16),
        ("button_mask", Uint32),
        ("axis_mask", Uint32),
        ("name", c_char_p),
        ("userdata", c_void_p),
        ("Update", CFUNC_Update),
        ("SetPlayerIndex", CFUNC_SetPlayerIndex),
        ("Rumble", CFUNC_Rumble),
        ("RumbleTriggers", CFUNC_RumbleTriggers),
        ("SetLED", CFUNC_SetLED),
        ("SendEffect", CFUNC_SendEffect),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_LockJoysticks", None, None, added='2.0.7'),
    SDLFunc("SDL_UnlockJoysticks", None, None, added='2.0.7'),
    SDLFunc("SDL_NumJoysticks", None, c_int),
    SDLFunc("SDL_JoystickNameForIndex", [c_int], c_char_p),
    SDLFunc("SDL_JoystickPathForIndex", [c_int], c_char_p, added='2.23.1'),
    SDLFunc("SDL_JoystickGetDevicePlayerIndex", [c_int], c_int, added='2.0.9'),
    SDLFunc("SDL_JoystickGetDeviceGUID", [c_int], SDL_JoystickGUID),
    SDLFunc("SDL_JoystickGetDeviceVendor", [c_int], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetDeviceProduct", [c_int], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetDeviceProductVersion", [c_int], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetDeviceType", [c_int], SDL_JoystickType, added='2.0.6'),
    SDLFunc("SDL_JoystickGetDeviceInstanceID", [c_int], SDL_JoystickID, added='2.0.6'),
    SDLFunc("SDL_JoystickOpen", [c_int], _P(SDL_Joystick)),
    SDLFunc("SDL_JoystickFromInstanceID", [SDL_JoystickID], _P(SDL_Joystick), added='2.0.4'),
    SDLFunc("SDL_JoystickFromPlayerIndex", [c_int], _P(SDL_Joystick), added='2.0.12'),
    SDLFunc("SDL_JoystickAttachVirtual",
        [SDL_JoystickType, c_int, c_int, c_int],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_JoystickAttachVirtualEx", [_P(SDL_VirtualJoystickDesc)], c_int, added='2.23.1'),
    SDLFunc("SDL_JoystickDetachVirtual", [c_int], c_int, added='2.0.14'),
    SDLFunc("SDL_JoystickIsVirtual", [c_int], SDL_bool, added='2.0.14'),
    SDLFunc("SDL_JoystickSetVirtualAxis",
        [_P(SDL_Joystick), c_int, Sint16],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_JoystickSetVirtualButton",
        [_P(SDL_Joystick), c_int, Uint8],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_JoystickSetVirtualHat", [_P(SDL_Joystick), c_int, Uint8], c_int, added='2.0.14'),
    SDLFunc("SDL_JoystickName", [_P(SDL_Joystick)], c_char_p),
    SDLFunc("SDL_JoystickPath", [_P(SDL_Joystick)], c_char_p, added='2.23.1'),
    SDLFunc("SDL_JoystickGetPlayerIndex", [_P(SDL_Joystick)], c_int, added='2.0.9'),
    SDLFunc("SDL_JoystickSetPlayerIndex", [_P(SDL_Joystick), c_int], added='2.0.12'),
    SDLFunc("SDL_JoystickGetGUID", [_P(SDL_Joystick)], SDL_JoystickGUID),
    SDLFunc("SDL_JoystickGetVendor", [_P(SDL_Joystick)], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetProduct", [_P(SDL_Joystick)], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetProductVersion", [_P(SDL_Joystick)], Uint16, added='2.0.6'),
    SDLFunc("SDL_JoystickGetFirmwareVersion", [_P(SDL_Joystick)], Uint16, added='2.23.1'),
    SDLFunc("SDL_JoystickGetSerial", [_P(SDL_Joystick)], c_char_p, added='2.0.14'),
    SDLFunc("SDL_JoystickGetType", [_P(SDL_Joystick)], SDL_JoystickType, added='2.0.6'),
    SDLFunc("SDL_JoystickGetGUIDString", [SDL_JoystickGUID, c_char_p, c_int]),
    SDLFunc("SDL_JoystickGetGUIDFromString", [c_char_p], SDL_JoystickGUID),
    SDLFunc("SDL_GetJoystickGUIDInfo",
        [SDL_JoystickGUID, _P(Uint16), _P(Uint16), _P(Uint16), _P(Uint16)],
        None, added = '2.26.0'
    ),
    SDLFunc("SDL_JoystickGetAttached", [_P(SDL_Joystick)], SDL_bool),
    SDLFunc("SDL_JoystickInstanceID", [_P(SDL_Joystick)], SDL_JoystickID),
    SDLFunc("SDL_JoystickNumAxes", [_P(SDL_Joystick)], c_int),
    SDLFunc("SDL_JoystickNumBalls", [_P(SDL_Joystick)], c_int),
    SDLFunc("SDL_JoystickNumHats", [_P(SDL_Joystick)], c_int),
    SDLFunc("SDL_JoystickNumButtons", [_P(SDL_Joystick)], c_int),
    SDLFunc("SDL_JoystickUpdate"),
    SDLFunc("SDL_JoystickEventState", [c_int], c_int),
    SDLFunc("SDL_JoystickGetAxis", [_P(SDL_Joystick), c_int], Sint16),
    SDLFunc("SDL_JoystickGetAxisInitialState",
        [_P(SDL_Joystick), c_int, _P(Sint16)],
        returns = SDL_bool, added = '2.0.6'
    ),
    SDLFunc("SDL_JoystickGetHat", [_P(SDL_Joystick), c_int], Uint8),
    SDLFunc("SDL_JoystickGetBall", [_P(SDL_Joystick), c_int, _P(c_int), _P(c_int)], c_int),
    SDLFunc("SDL_JoystickGetButton", [_P(SDL_Joystick), c_int], Uint8),
    SDLFunc("SDL_JoystickRumble",
        [_P(SDL_Joystick), Uint16, Uint16, Uint32],
        returns = c_int, added = '2.0.9'
    ),
    SDLFunc("SDL_JoystickRumbleTriggers",
        [_P(SDL_Joystick), Uint16, Uint16, Uint32],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_JoystickHasLED", [_P(SDL_Joystick)], SDL_bool, added='2.0.14'),
    SDLFunc("SDL_JoystickHasRumble", [_P(SDL_Joystick)], SDL_bool, added='2.0.18'),
    SDLFunc("SDL_JoystickHasRumbleTriggers", [_P(SDL_Joystick)], SDL_bool, added='2.0.18'),
    SDLFunc("SDL_JoystickSetLED", [_P(SDL_Joystick), Uint8, Uint8, Uint8], c_int, added='2.0.14'),
    SDLFunc("SDL_JoystickSendEffect", [_P(SDL_Joystick), c_void_p, c_int], c_int, added='2.0.16'),
    SDLFunc("SDL_JoystickClose", [_P(SDL_Joystick)]),
    SDLFunc("SDL_JoystickCurrentPowerLevel",
        [_P(SDL_Joystick)],
        returns = SDL_JoystickPowerLevel, added = '2.0.4'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_NumJoysticks = _ctypes["SDL_NumJoysticks"]
SDL_JoystickNameForIndex = _ctypes["SDL_JoystickNameForIndex"]
SDL_JoystickPathForIndex = _ctypes["SDL_JoystickPathForIndex"]
SDL_JoystickOpen = _ctypes["SDL_JoystickOpen"]
SDL_JoystickName = _ctypes["SDL_JoystickName"]
SDL_JoystickPath = _ctypes["SDL_JoystickPath"]
SDL_JoystickGetDeviceGUID = _ctypes["SDL_JoystickGetDeviceGUID"]
SDL_JoystickGetGUID = _ctypes["SDL_JoystickGetGUID"]
SDL_JoystickGetGUIDFromString = _ctypes["SDL_JoystickGetGUIDFromString"]
SDL_JoystickGetAttached = _ctypes["SDL_JoystickGetAttached"]
SDL_JoystickInstanceID = _ctypes["SDL_JoystickInstanceID"]
SDL_JoystickNumAxes = _ctypes["SDL_JoystickNumAxes"]
SDL_JoystickNumBalls = _ctypes["SDL_JoystickNumBalls"]
SDL_JoystickNumHats = _ctypes["SDL_JoystickNumHats"]
SDL_JoystickNumButtons = _ctypes["SDL_JoystickNumButtons"]
SDL_JoystickUpdate = _ctypes["SDL_JoystickUpdate"]
SDL_JoystickEventState = _ctypes["SDL_JoystickEventState"]
SDL_JoystickGetAxis = _ctypes["SDL_JoystickGetAxis"]
SDL_JoystickGetHat = _ctypes["SDL_JoystickGetHat"]
SDL_JoystickGetBall = _ctypes["SDL_JoystickGetBall"]
SDL_JoystickGetButton = _ctypes["SDL_JoystickGetButton"]
SDL_JoystickClose = _ctypes["SDL_JoystickClose"]
SDL_JoystickCurrentPowerLevel = _ctypes["SDL_JoystickCurrentPowerLevel"]
SDL_JoystickFromInstanceID = _ctypes["SDL_JoystickFromInstanceID"]
SDL_JoystickFromPlayerIndex = _ctypes["SDL_JoystickFromPlayerIndex"]
SDL_JoystickAttachVirtual = _ctypes["SDL_JoystickAttachVirtual"]
SDL_JoystickAttachVirtualEx = _ctypes["SDL_JoystickAttachVirtualEx"]
SDL_JoystickDetachVirtual = _ctypes["SDL_JoystickDetachVirtual"]
SDL_JoystickIsVirtual = _ctypes["SDL_JoystickIsVirtual"]
SDL_JoystickSetVirtualAxis = _ctypes["SDL_JoystickSetVirtualAxis"]
SDL_JoystickSetVirtualButton = _ctypes["SDL_JoystickSetVirtualButton"]
SDL_JoystickSetVirtualHat = _ctypes["SDL_JoystickSetVirtualHat"]
SDL_JoystickGetVendor = _ctypes["SDL_JoystickGetVendor"]
SDL_JoystickGetProduct = _ctypes["SDL_JoystickGetProduct"]
SDL_JoystickGetProductVersion = _ctypes["SDL_JoystickGetProductVersion"]
SDL_JoystickGetFirmwareVersion = _ctypes["SDL_JoystickGetFirmwareVersion"]
SDL_JoystickGetSerial = _ctypes["SDL_JoystickGetSerial"]
SDL_JoystickGetAxisInitialState = _ctypes["SDL_JoystickGetAxisInitialState"]
SDL_JoystickGetType = _ctypes["SDL_JoystickGetType"]
SDL_JoystickGetDeviceVendor = _ctypes["SDL_JoystickGetDeviceVendor"]
SDL_JoystickGetDeviceProduct = _ctypes["SDL_JoystickGetDeviceProduct"]
SDL_JoystickGetDeviceProductVersion = _ctypes["SDL_JoystickGetDeviceProductVersion"]
SDL_JoystickGetDeviceType = _ctypes["SDL_JoystickGetDeviceType"]
SDL_JoystickGetDeviceInstanceID = _ctypes["SDL_JoystickGetDeviceInstanceID"]
SDL_LockJoysticks = _ctypes["SDL_LockJoysticks"]
SDL_UnlockJoysticks = _ctypes["SDL_UnlockJoysticks"]
SDL_JoystickGetPlayerIndex = _ctypes["SDL_JoystickGetPlayerIndex"]
SDL_JoystickSetPlayerIndex = _ctypes["SDL_JoystickSetPlayerIndex"]
SDL_JoystickGetDevicePlayerIndex = _ctypes["SDL_JoystickGetDevicePlayerIndex"]
SDL_JoystickRumble = _ctypes["SDL_JoystickRumble"]
SDL_JoystickRumbleTriggers = _ctypes["SDL_JoystickRumbleTriggers"]
SDL_JoystickHasLED = _ctypes["SDL_JoystickHasLED"]
SDL_JoystickHasRumble = _ctypes["SDL_JoystickHasRumble"]
SDL_JoystickHasRumbleTriggers = _ctypes["SDL_JoystickHasRumbleTriggers"]
SDL_JoystickSetLED = _ctypes["SDL_JoystickSetLED"]
SDL_JoystickSendEffect = _ctypes["SDL_JoystickSendEffect"]

# Reimplemented in Python due to crash-causing ctypes bug (fixed in 3.8)
if sys.version_info >= (3, 8, 0, 'final'):
    SDL_JoystickGetGUIDString = _ctypes["SDL_JoystickGetGUIDString"]
else:
    def SDL_JoystickGetGUIDString(guid, pszGUID, cbGUID):
        s = ""
        for g in guid.data:
            s += "{:x}".format(g >> 4)
            s += "{:x}".format(g & 0x0F)
        s = s.encode('utf-8')
        pszGUID.value = s[:(cbGUID * 2)]

if sys.version_info >= (3, 7, 0, 'final'):
    SDL_GetJoystickGUIDInfo = _ctypes["SDL_GetJoystickGUIDInfo"]
else:
    def SDL_GetJoystickGUIDInfo(guid, vendor, product, version, crc16):
        # We can't modify ctypes arguments passed with byref in Python,
        # so to avoid a segfault on older Python versions we just do
        # nothing here since we can't replicate its functionality.
        pass
