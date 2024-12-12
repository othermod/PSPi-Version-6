import sys
from ctypes import (
    c_int, c_char_p, c_void_p, c_float, Structure, Union, create_string_buffer
)
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .dll import version as sdl_version
from .stdinc import SDL_bool, Sint16, Uint64, Uint32, Uint16, Uint8
from .joystick import (SDL_JoystickGUID, SDL_Joystick, SDL_JoystickID,
    SDL_JoystickGetGUIDString)
from .rwops import SDL_RWops, SDL_RWFromFile
from .sensor import SDL_SensorType

__all__ = [
    # Structs & Opaque Types
    "SDL_GameController", "SDL_GameControllerButtonBind",

    # Enums
    "SDL_GameControllerType",
    "SDL_CONTROLLER_TYPE_UNKNOWN", "SDL_CONTROLLER_TYPE_XBOX360",
    "SDL_CONTROLLER_TYPE_XBOXONE", "SDL_CONTROLLER_TYPE_PS3",
    "SDL_CONTROLLER_TYPE_PS4", "SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO",
    "SDL_CONTROLLER_TYPE_VIRTUAL", "SDL_CONTROLLER_TYPE_PS5",
    "SDL_CONTROLLER_TYPE_AMAZON_LUNA", "SDL_CONTROLLER_TYPE_GOOGLE_STADIA",

    "SDL_GameControllerBindType",
    "SDL_CONTROLLER_BINDTYPE_NONE", "SDL_CONTROLLER_BINDTYPE_BUTTON",
    "SDL_CONTROLLER_BINDTYPE_AXIS", "SDL_CONTROLLER_BINDTYPE_HAT", 

    "SDL_GameControllerAxis",
    "SDL_CONTROLLER_AXIS_INVALID", "SDL_CONTROLLER_AXIS_LEFTX",
    "SDL_CONTROLLER_AXIS_LEFTY", "SDL_CONTROLLER_AXIS_RIGHTX",
    "SDL_CONTROLLER_AXIS_RIGHTY", "SDL_CONTROLLER_AXIS_TRIGGERLEFT",
    "SDL_CONTROLLER_AXIS_TRIGGERRIGHT", "SDL_CONTROLLER_AXIS_MAX",  

    "SDL_GameControllerButton",
    "SDL_CONTROLLER_BUTTON_INVALID", "SDL_CONTROLLER_BUTTON_A",
    "SDL_CONTROLLER_BUTTON_B", "SDL_CONTROLLER_BUTTON_X",
    "SDL_CONTROLLER_BUTTON_Y", "SDL_CONTROLLER_BUTTON_BACK",
    "SDL_CONTROLLER_BUTTON_GUIDE", "SDL_CONTROLLER_BUTTON_START",
    "SDL_CONTROLLER_BUTTON_LEFTSTICK", "SDL_CONTROLLER_BUTTON_RIGHTSTICK",
    "SDL_CONTROLLER_BUTTON_LEFTSHOULDER",
    "SDL_CONTROLLER_BUTTON_RIGHTSHOULDER",
    "SDL_CONTROLLER_BUTTON_DPAD_UP", "SDL_CONTROLLER_BUTTON_DPAD_DOWN",
    "SDL_CONTROLLER_BUTTON_DPAD_LEFT", "SDL_CONTROLLER_BUTTON_DPAD_RIGHT",
    "SDL_CONTROLLER_BUTTON_MISC1", "SDL_CONTROLLER_BUTTON_PADDLE1",
    "SDL_CONTROLLER_BUTTON_PADDLE2", "SDL_CONTROLLER_BUTTON_PADDLE3",
    "SDL_CONTROLLER_BUTTON_PADDLE4", "SDL_CONTROLLER_BUTTON_TOUCHPAD",
    "SDL_CONTROLLER_BUTTON_MAX",

    # Macro Functions
    "SDL_GameControllerAddMappingsFromFile",
]


# Constants & enums

SDL_GameControllerBindType = c_int
SDL_CONTROLLER_BINDTYPE_NONE = 0
SDL_CONTROLLER_BINDTYPE_BUTTON = 1
SDL_CONTROLLER_BINDTYPE_AXIS = 2
SDL_CONTROLLER_BINDTYPE_HAT = 3

SDL_GameControllerType = c_int
SDL_CONTROLLER_TYPE_UNKNOWN = 0
SDL_CONTROLLER_TYPE_XBOX360 = 1
SDL_CONTROLLER_TYPE_XBOXONE = 2
SDL_CONTROLLER_TYPE_PS3 = 3
SDL_CONTROLLER_TYPE_PS4 = 4
SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO = 5
SDL_CONTROLLER_TYPE_VIRTUAL = 6
SDL_CONTROLLER_TYPE_PS5 = 7
SDL_CONTROLLER_TYPE_AMAZON_LUNA = 8
SDL_CONTROLLER_TYPE_GOOGLE_STADIA = 9
SDL_CONTROLLER_TYPE_NVIDIA_SHIELD = 10
SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_LEFT = 11
SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_RIGHT = 12
SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_PAIR = 13

SDL_GameControllerAxis = c_int
SDL_CONTROLLER_AXIS_INVALID = -1
SDL_CONTROLLER_AXIS_LEFTX = 0
SDL_CONTROLLER_AXIS_LEFTY = 1
SDL_CONTROLLER_AXIS_RIGHTX = 2
SDL_CONTROLLER_AXIS_RIGHTY = 3
SDL_CONTROLLER_AXIS_TRIGGERLEFT = 4
SDL_CONTROLLER_AXIS_TRIGGERRIGHT = 5
SDL_CONTROLLER_AXIS_MAX = 6

SDL_GameControllerButton = c_int
SDL_CONTROLLER_BUTTON_INVALID = -1
SDL_CONTROLLER_BUTTON_A = 0
SDL_CONTROLLER_BUTTON_B = 1
SDL_CONTROLLER_BUTTON_X = 2
SDL_CONTROLLER_BUTTON_Y = 3
SDL_CONTROLLER_BUTTON_BACK = 4
SDL_CONTROLLER_BUTTON_GUIDE = 5
SDL_CONTROLLER_BUTTON_START = 6
SDL_CONTROLLER_BUTTON_LEFTSTICK = 7
SDL_CONTROLLER_BUTTON_RIGHTSTICK = 8
SDL_CONTROLLER_BUTTON_LEFTSHOULDER = 9
SDL_CONTROLLER_BUTTON_RIGHTSHOULDER = 10
SDL_CONTROLLER_BUTTON_DPAD_UP = 11
SDL_CONTROLLER_BUTTON_DPAD_DOWN = 12
SDL_CONTROLLER_BUTTON_DPAD_LEFT = 13
SDL_CONTROLLER_BUTTON_DPAD_RIGHT = 14
SDL_CONTROLLER_BUTTON_MISC1 = 15    
SDL_CONTROLLER_BUTTON_PADDLE1 = 16
SDL_CONTROLLER_BUTTON_PADDLE2 = 17
SDL_CONTROLLER_BUTTON_PADDLE3 = 18
SDL_CONTROLLER_BUTTON_PADDLE4 = 19
SDL_CONTROLLER_BUTTON_TOUCHPAD = 20
SDL_CONTROLLER_BUTTON_MAX = 21
if sdl_version < 2014:
    SDL_CONTROLLER_BUTTON_MAX = 15  # For backwards compatibility


# Structs & opaque typedefs

class _gchat(Structure):
    _fields_ = [("hat", c_int), ("hat_mask", c_int)]

class _gcvalue(Union):
    _fields_ = [("button", c_int), ("axis", c_int), ("hat", _gchat)]

class SDL_GameControllerButtonBind(Structure):
    _fields_ = [("bindType", SDL_GameControllerBindType), ("value", _gcvalue)]

class SDL_GameController(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GameControllerAddMappingsFromRW", [_P(SDL_RWops), c_int], c_int),
    SDLFunc("SDL_GameControllerAddMapping", [c_char_p], c_int),
    SDLFunc("SDL_GameControllerNumMappings", None, c_int, added='2.0.6'),
    SDLFunc("SDL_GameControllerMappingForIndex", [c_int], c_char_p, added='2.0.6'),
    SDLFunc("SDL_GameControllerMappingForGUID", [SDL_JoystickGUID], c_char_p),
    SDLFunc("SDL_GameControllerMapping", [_P(SDL_GameController)], c_char_p),
    SDLFunc("SDL_IsGameController", [c_int], SDL_bool),
    SDLFunc("SDL_GameControllerNameForIndex", [c_int], c_char_p),
    SDLFunc("SDL_GameControllerPathForIndex", [c_int], c_char_p, added='2.23.1'),
    SDLFunc("SDL_GameControllerTypeForIndex", [c_int], SDL_GameControllerType, added='2.0.12'),
    SDLFunc("SDL_GameControllerMappingForDeviceIndex", [c_int], c_char_p, added='2.0.9'),
    SDLFunc("SDL_GameControllerOpen", [c_int], _P(SDL_GameController)),
    SDLFunc("SDL_GameControllerFromInstanceID",
        [SDL_JoystickID],
        returns = _P(SDL_GameController), added = '2.0.4'
    ),
    SDLFunc("SDL_GameControllerFromPlayerIndex", [c_int], _P(SDL_GameController), added='2.0.12'),
    SDLFunc("SDL_GameControllerName", [_P(SDL_GameController)], c_char_p),
    SDLFunc("SDL_GameControllerPath", [_P(SDL_GameController)], c_char_p, added='2.23.1'),
    SDLFunc("SDL_GameControllerGetType",
        [_P(SDL_GameController)],
        returns = SDL_GameControllerType, added = '2.0.12'
    ),
    SDLFunc("SDL_GameControllerGetPlayerIndex", [_P(SDL_GameController)], c_int, added='2.0.9'),
    SDLFunc("SDL_GameControllerSetPlayerIndex", [_P(SDL_GameController), c_int], added='2.0.12'),
    SDLFunc("SDL_GameControllerGetVendor", [_P(SDL_GameController)], Uint16, added='2.0.6'),
    SDLFunc("SDL_GameControllerGetProduct", [_P(SDL_GameController)], Uint16, added='2.0.6'),
    SDLFunc("SDL_GameControllerGetProductVersion",
        [_P(SDL_GameController)],
        returns = Uint16, added = '2.0.6'
    ),
    SDLFunc("SDL_GameControllerGetFirmwareVersion",
        [_P(SDL_GameController)],
        returns = Uint16, added = '2.23.1'
    ),
    SDLFunc("SDL_GameControllerGetSerial", [_P(SDL_GameController)], c_char_p, added='2.0.14'),
    SDLFunc("SDL_GameControllerGetAttached", [_P(SDL_GameController)], SDL_bool),
    SDLFunc("SDL_GameControllerGetJoystick", [_P(SDL_GameController)], _P(SDL_Joystick)),
    SDLFunc("SDL_GameControllerEventState", [c_int], c_int),
    SDLFunc("SDL_GameControllerUpdate"),
    SDLFunc("SDL_GameControllerGetAxisFromString", [c_char_p], SDL_GameControllerAxis),
    SDLFunc("SDL_GameControllerGetStringForAxis", [SDL_GameControllerAxis], c_char_p),
    SDLFunc("SDL_GameControllerGetBindForAxis",
        [_P(SDL_GameController), SDL_GameControllerAxis],
        returns = SDL_GameControllerButtonBind
    ),
    SDLFunc("SDL_GameControllerHasAxis",
        [_P(SDL_GameController), SDL_GameControllerAxis],
        returns = SDL_bool, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerGetAxis", [_P(SDL_GameController), SDL_GameControllerAxis], Sint16),
    SDLFunc("SDL_GameControllerGetButtonFromString", [c_char_p], SDL_GameControllerButton),
    SDLFunc("SDL_GameControllerGetStringForButton", [SDL_GameControllerButton], c_char_p),
    SDLFunc("SDL_GameControllerGetBindForButton",
        [_P(SDL_GameController), SDL_GameControllerButton],
        returns = SDL_GameControllerButtonBind
    ),
    SDLFunc("SDL_GameControllerHasButton",
        [_P(SDL_GameController), SDL_GameControllerButton],
        returns = SDL_bool, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerGetButton",
        [_P(SDL_GameController), SDL_GameControllerButton],
        returns = Uint8
    ),
    SDLFunc("SDL_GameControllerGetNumTouchpads", [_P(SDL_GameController)], c_int, added='2.0.14'),
    SDLFunc("SDL_GameControllerGetNumTouchpadFingers",
        [_P(SDL_GameController), c_int],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerGetTouchpadFinger",
        [_P(SDL_GameController), c_int, c_int, _P(Uint8), _P(c_float), _P(c_float), _P(c_float)],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerHasSensor",
        [_P(SDL_GameController), SDL_SensorType],
        returns = SDL_bool, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerSetSensorEnabled",
        [_P(SDL_GameController), SDL_SensorType, SDL_bool],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerIsSensorEnabled",
        [_P(SDL_GameController), SDL_SensorType],
        returns = SDL_bool, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerGetSensorDataRate",
        [_P(SDL_GameController), SDL_SensorType],
        returns = c_float, added = '2.0.16'
    ),
    # TODO: Read how GetSensorData is implemented to figure out how the # of floats is determined
    SDLFunc("SDL_GameControllerGetSensorData",
        [_P(SDL_GameController), SDL_SensorType, _P(c_float), c_int],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerGetSensorDataWithTimestamp",
        [_P(SDL_GameController), SDL_SensorType, _P(Uint64), _P(c_float), c_int],
        returns = c_int, added = '2.26.0'
    ),
    SDLFunc("SDL_GameControllerRumble",
        [_P(SDL_GameController), Uint16, Uint16, Uint32],
        returns = c_int, added = '2.0.9'
    ),
    SDLFunc("SDL_GameControllerRumbleTriggers",
        [_P(SDL_GameController), Uint16, Uint16, Uint32],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerHasLED", [_P(SDL_GameController)], SDL_bool, added='2.0.14'),
    SDLFunc("SDL_GameControllerHasRumble", [_P(SDL_GameController)], SDL_bool, added='2.0.18'),
    SDLFunc("SDL_GameControllerHasRumbleTriggers",
        [_P(SDL_GameController)],
        returns = SDL_bool, added = '2.0.18'
    ),
    SDLFunc("SDL_GameControllerSetLED",
        [_P(SDL_GameController), Uint8, Uint8, Uint8],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("SDL_GameControllerSendEffect",
        [_P(SDL_GameController), c_void_p, c_int],
        returns = c_int, added = '2.0.16'
    ),
    SDLFunc("SDL_GameControllerClose", [_P(SDL_GameController)]),
    SDLFunc("SDL_GameControllerGetAppleSFSymbolsNameForButton",
        [_P(SDL_GameController), SDL_GameControllerButton],
        returns = c_char_p, added = '2.0.18'
    ),
    SDLFunc("SDL_GameControllerGetAppleSFSymbolsNameForAxis",
        [_P(SDL_GameController), SDL_GameControllerAxis],
        returns = c_char_p, added = '2.0.18'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GameControllerAddMapping = _ctypes["SDL_GameControllerAddMapping"]
SDL_GameControllerMapping = _ctypes["SDL_GameControllerMapping"]
SDL_IsGameController = _ctypes["SDL_IsGameController"]
SDL_GameControllerNameForIndex = _ctypes["SDL_GameControllerNameForIndex"]
SDL_GameControllerPathForIndex = _ctypes["SDL_GameControllerPathForIndex"]
SDL_GameControllerTypeForIndex = _ctypes["SDL_GameControllerTypeForIndex"]
SDL_GameControllerOpen = _ctypes["SDL_GameControllerOpen"]
SDL_GameControllerName = _ctypes["SDL_GameControllerName"]
SDL_GameControllerPath = _ctypes["SDL_GameControllerPath"]
SDL_GameControllerGetType = _ctypes["SDL_GameControllerGetType"]
SDL_GameControllerGetAttached = _ctypes["SDL_GameControllerGetAttached"]
SDL_GameControllerGetJoystick = _ctypes["SDL_GameControllerGetJoystick"]
SDL_GameControllerEventState = _ctypes["SDL_GameControllerEventState"]
SDL_GameControllerUpdate = _ctypes["SDL_GameControllerUpdate"]
SDL_GameControllerGetAxisFromString = _ctypes["SDL_GameControllerGetAxisFromString"]
SDL_GameControllerGetStringForAxis = _ctypes["SDL_GameControllerGetStringForAxis"]
SDL_GameControllerGetBindForAxis = _ctypes["SDL_GameControllerGetBindForAxis"]
SDL_GameControllerHasAxis = _ctypes["SDL_GameControllerHasAxis"]
SDL_GameControllerGetAxis = _ctypes["SDL_GameControllerGetAxis"]
SDL_GameControllerGetButtonFromString = _ctypes["SDL_GameControllerGetButtonFromString"]
SDL_GameControllerGetStringForButton = _ctypes["SDL_GameControllerGetStringForButton"]
SDL_GameControllerGetBindForButton = _ctypes["SDL_GameControllerGetBindForButton"]
SDL_GameControllerHasButton = _ctypes["SDL_GameControllerHasButton"]
SDL_GameControllerGetButton = _ctypes["SDL_GameControllerGetButton"]
SDL_GameControllerGetNumTouchpads = _ctypes["SDL_GameControllerGetNumTouchpads"]
SDL_GameControllerGetNumTouchpadFingers = _ctypes["SDL_GameControllerGetNumTouchpadFingers"]
SDL_GameControllerGetTouchpadFinger = _ctypes["SDL_GameControllerGetTouchpadFinger"]
SDL_GameControllerHasSensor = _ctypes["SDL_GameControllerHasSensor"]
SDL_GameControllerSetSensorEnabled = _ctypes["SDL_GameControllerSetSensorEnabled"]
SDL_GameControllerIsSensorEnabled = _ctypes["SDL_GameControllerIsSensorEnabled"]
SDL_GameControllerGetSensorDataRate = _ctypes["SDL_GameControllerGetSensorDataRate"]
SDL_GameControllerGetSensorData = _ctypes["SDL_GameControllerGetSensorData"]
SDL_GameControllerGetSensorDataWithTimestamp = _ctypes["SDL_GameControllerGetSensorDataWithTimestamp"]
SDL_GameControllerAddMappingsFromRW = _ctypes["SDL_GameControllerAddMappingsFromRW"]
SDL_GameControllerAddMappingsFromFile = lambda fname: SDL_GameControllerAddMappingsFromRW(SDL_RWFromFile(fname, b"rb"), 1)
SDL_GameControllerFromInstanceID = _ctypes["SDL_GameControllerFromInstanceID"]
SDL_GameControllerFromPlayerIndex = _ctypes["SDL_GameControllerFromPlayerIndex"]
SDL_GameControllerGetPlayerIndex = _ctypes["SDL_GameControllerGetPlayerIndex"]
SDL_GameControllerSetPlayerIndex = _ctypes["SDL_GameControllerSetPlayerIndex"]
SDL_GameControllerGetVendor = _ctypes["SDL_GameControllerGetVendor"]
SDL_GameControllerGetProduct = _ctypes["SDL_GameControllerGetProduct"]
SDL_GameControllerGetProductVersion = _ctypes["SDL_GameControllerGetProductVersion"]
SDL_GameControllerGetFirmwareVersion = _ctypes["SDL_GameControllerGetFirmwareVersion"]
SDL_GameControllerGetSerial = _ctypes["SDL_GameControllerGetSerial"]
SDL_GameControllerNumMappings = _ctypes["SDL_GameControllerNumMappings"]
SDL_GameControllerMappingForIndex = _ctypes["SDL_GameControllerMappingForIndex"]
SDL_GameControllerMappingForDeviceIndex = _ctypes["SDL_GameControllerMappingForDeviceIndex"]
SDL_GameControllerRumble = _ctypes["SDL_GameControllerRumble"]
SDL_GameControllerRumbleTriggers = _ctypes["SDL_GameControllerRumbleTriggers"]
SDL_GameControllerHasLED = _ctypes["SDL_GameControllerHasLED"]
SDL_GameControllerHasRumble = _ctypes["SDL_GameControllerHasRumble"]
SDL_GameControllerHasRumbleTriggers = _ctypes["SDL_GameControllerHasRumbleTriggers"]
SDL_GameControllerSetLED = _ctypes["SDL_GameControllerSetLED"]
SDL_GameControllerSendEffect = _ctypes["SDL_GameControllerSendEffect"]
SDL_GameControllerClose = _ctypes["SDL_GameControllerClose"]
SDL_GameControllerGetAppleSFSymbolsNameForButton = _ctypes["SDL_GameControllerGetAppleSFSymbolsNameForButton"]
SDL_GameControllerGetAppleSFSymbolsNameForAxis = _ctypes["SDL_GameControllerGetAppleSFSymbolsNameForAxis"]


# Reimplemented w/ other functions due to crash-causing ctypes bug (fixed in 3.8)
if sys.version_info >= (3, 8, 0, 'final'):
    SDL_GameControllerMappingForGUID = _ctypes["SDL_GameControllerMappingForGUID"]
else:
    def SDL_GameControllerMappingForGUID(guid):
        buff = create_string_buffer(33)
        SDL_JoystickGetGUIDString(guid, buff, 33) # Get GUID string
        guid_str = buff.value
        # Iterate over controller mappings and look for a GUID match
        # Note: iterates in reverse, so user-defined mappings are checked first
        num = SDL_GameControllerNumMappings()
        for i in range(num - 1, -1, -1): 
            m = SDL_GameControllerMappingForIndex(i)
            if m.split(b',')[0] == guid_str:
                return m
        return None
