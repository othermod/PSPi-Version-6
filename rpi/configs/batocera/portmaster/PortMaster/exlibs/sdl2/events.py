from ctypes import (
    c_char, c_char_p, c_float, c_void_p, c_int, Structure, Union, CFUNCTYPE, sizeof
)
from ctypes import POINTER as _P
from .dll import version as sdl_version
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Sint16, Sint32, Uint8, Uint16, Uint32, Uint64, SDL_bool
from .keyboard import SDL_Keysym
from .joystick import SDL_JoystickID, SDL_JoystickPowerLevel
from .touch import SDL_FingerID, SDL_TouchID
from .gesture import SDL_GestureID
from .syswm import SDL_SysWMmsg

__all__ = [
    # Structs, Unions, & Opaque Types
    "SDL_CommonEvent", "SDL_DisplayEvent", "SDL_WindowEvent", 
    "SDL_KeyboardEvent", "SDL_TextEditingEvent",
    "SDL_TextEditingExtEvent", "SDL_TextInputEvent",
    "SDL_MouseMotionEvent", "SDL_MouseButtonEvent", "SDL_MouseWheelEvent",
    "SDL_JoyAxisEvent", "SDL_JoyBallEvent", "SDL_JoyHatEvent",
    "SDL_JoyButtonEvent", "SDL_JoyDeviceEvent", "SDL_JoyBatteryEvent",
    "SDL_ControllerAxisEvent", "SDL_ControllerButtonEvent",
    "SDL_ControllerDeviceEvent", "SDL_ControllerTouchpadEvent",
    "SDL_ControllerSensorEvent",
    "SDL_AudioDeviceEvent",
    "SDL_TouchFingerEvent", "SDL_MultiGestureEvent", "SDL_DollarGestureEvent",
    "SDL_DropEvent", "SDL_QuitEvent", "SDL_OSEvent", "SDL_UserEvent", 
    "SDL_SysWMmsg", "SDL_SysWMEvent", "SDL_SensorEvent", "SDL_Event",

    # Defines
    "SDL_RELEASED", "SDL_PRESSED",
    "SDL_TEXTEDITINGEVENT_TEXT_SIZE", "SDL_TEXTINPUTEVENT_TEXT_SIZE",
    "SDL_QUERY", "SDL_IGNORE", "SDL_DISABLE", "SDL_ENABLE",

    # Enums
    "SDL_EventType",
    "SDL_FIRSTEVENT", "SDL_QUIT", "SDL_APP_TERMINATING", "SDL_APP_LOWMEMORY",
    "SDL_APP_WILLENTERBACKGROUND", "SDL_APP_DIDENTERBACKGROUND",
    "SDL_APP_WILLENTERFOREGROUND", "SDL_APP_DIDENTERFOREGROUND",
    "SDL_LOCALECHANGED", "SDL_DISPLAYEVENT",
    "SDL_WINDOWEVENT", "SDL_SYSWMEVENT",
    "SDL_KEYDOWN", "SDL_KEYUP", "SDL_TEXTEDITING", "SDL_TEXTINPUT",
    "SDL_KEYMAPCHANGED", "SDL_TEXTEDITING_EXT",
    "SDL_MOUSEMOTION", "SDL_MOUSEBUTTONDOWN",
    "SDL_MOUSEBUTTONUP", "SDL_MOUSEWHEEL",
    "SDL_JOYAXISMOTION", "SDL_JOYBALLMOTION",
    "SDL_JOYHATMOTION", "SDL_JOYBUTTONDOWN", "SDL_JOYBUTTONUP",
    "SDL_JOYDEVICEADDED", "SDL_JOYDEVICEREMOVED", "SDL_JOYBATTERYUPDATED",
    "SDL_CONTROLLERAXISMOTION", "SDL_CONTROLLERBUTTONDOWN",
    "SDL_CONTROLLERBUTTONUP", "SDL_CONTROLLERDEVICEADDED",
    "SDL_CONTROLLERDEVICEREMOVED", "SDL_CONTROLLERDEVICEREMAPPED",
    "SDL_CONTROLLERTOUCHPADDOWN", "SDL_CONTROLLERTOUCHPADMOTION",
    "SDL_CONTROLLERTOUCHPADUP", "SDL_CONTROLLERSENSORUPDATE",
    "SDL_FINGERDOWN", "SDL_FINGERUP", "SDL_FINGERMOTION",
    "SDL_DOLLARGESTURE", "SDL_DOLLARRECORD", "SDL_MULTIGESTURE",
    "SDL_CLIPBOARDUPDATE", "SDL_DROPFILE", "SDL_DROPTEXT",
    "SDL_DROPBEGIN", "SDL_DROPCOMPLETE",
    "SDL_AUDIODEVICEADDED", "SDL_AUDIODEVICEREMOVED", "SDL_SENSORUPDATE",
    "SDL_RENDER_TARGETS_RESET", "SDL_RENDER_DEVICE_RESET", "SDL_POLLSENTINEL",
    "SDL_USEREVENT", "SDL_LASTEVENT",

    "SDL_eventaction",
    "SDL_ADDEVENT", "SDL_PEEKEVENT", "SDL_GETEVENT", 
    
    # Macro Functions
    "SDL_GetEventState", "SDL_QuitRequested",

    # Callback Functions
    "SDL_EventFilter"
]


# Constants & enums

SDL_RELEASED = 0
SDL_PRESSED = 1

SDL_EventType = c_int
SDL_FIRSTEVENT = 0
SDL_QUIT = 0x100
SDL_APP_TERMINATING = 0x101
SDL_APP_LOWMEMORY = 0x102
SDL_APP_WILLENTERBACKGROUND = 0x103
SDL_APP_DIDENTERBACKGROUND = 0x104
SDL_APP_WILLENTERFOREGROUND = 0x105
SDL_APP_DIDENTERFOREGROUND = 0x106
SDL_LOCALECHANGED = 0x107
SDL_DISPLAYEVENT = 0x150
SDL_WINDOWEVENT = 0x200
SDL_SYSWMEVENT = 0x201
SDL_KEYDOWN = 0x300
SDL_KEYUP = 0x301
SDL_TEXTEDITING = 0x302
SDL_TEXTINPUT = 0x303
SDL_KEYMAPCHANGED = 0x304
SDL_TEXTEDITING_EXT = 0x305
SDL_MOUSEMOTION = 0x400
SDL_MOUSEBUTTONDOWN = 0x401
SDL_MOUSEBUTTONUP = 0x402
SDL_MOUSEWHEEL = 0x403
SDL_JOYAXISMOTION = 0x600
SDL_JOYBALLMOTION = 0x601
SDL_JOYHATMOTION = 0x602
SDL_JOYBUTTONDOWN = 0x603
SDL_JOYBUTTONUP = 0x604
SDL_JOYDEVICEADDED = 0x605
SDL_JOYDEVICEREMOVED = 0x606
SDL_JOYBATTERYUPDATED = 0x607
SDL_CONTROLLERAXISMOTION = 0x650
SDL_CONTROLLERBUTTONDOWN = 0x651
SDL_CONTROLLERBUTTONUP = 0x652
SDL_CONTROLLERDEVICEADDED = 0x653
SDL_CONTROLLERDEVICEREMOVED = 0x654
SDL_CONTROLLERDEVICEREMAPPED = 0x655
SDL_CONTROLLERTOUCHPADDOWN = 0x656
SDL_CONTROLLERTOUCHPADMOTION = 0x657
SDL_CONTROLLERTOUCHPADUP = 0x658
SDL_CONTROLLERSENSORUPDATE = 0x659
SDL_FINGERDOWN = 0x700
SDL_FINGERUP = 0x701
SDL_FINGERMOTION = 0x702
SDL_DOLLARGESTURE = 0x800
SDL_DOLLARRECORD = 0x801
SDL_MULTIGESTURE = 0x802
SDL_CLIPBOARDUPDATE = 0x900
SDL_DROPFILE = 0x1000
SDL_DROPTEXT = 0x1001
SDL_DROPBEGIN = 0x1002
SDL_DROPCOMPLETE = 0x1003
SDL_AUDIODEVICEADDED = 0x1100
SDL_AUDIODEVICEREMOVED = 0x1101
SDL_SENSORUPDATE = 0x1200
SDL_RENDER_TARGETS_RESET = 0x2000
SDL_RENDER_DEVICE_RESET = 0x2001
SDL_POLLSENTINEL = 0x7F00
SDL_USEREVENT = 0x8000
SDL_LASTEVENT = 0xFFFF

SDL_eventaction = c_int
SDL_ADDEVENT = 0
SDL_PEEKEVENT = 1
SDL_GETEVENT = 2

SDL_TEXTEDITINGEVENT_TEXT_SIZE = 32
SDL_TEXTINPUTEVENT_TEXT_SIZE = 32

SDL_QUERY = -1
SDL_IGNORE = 0
SDL_DISABLE = 0
SDL_ENABLE = 1


# Struct definintions

class SDL_CommonEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
    ]

class SDL_DisplayEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("display", Uint32),
        ("event", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("data1", Sint32),
    ]

class SDL_WindowEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("event", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("data1", Sint32),
        ("data2", Sint32),
    ]

class SDL_KeyboardEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("state", Uint8),
        ("repeat", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("keysym", SDL_Keysym),
    ]

class SDL_TextEditingEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("text", (c_char * SDL_TEXTEDITINGEVENT_TEXT_SIZE)),
        ("start", Sint32),
        ("length", Sint32),
    ]

class SDL_TextEditingExtEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("text", c_char_p),
        ("start", Sint32),
        ("length", Sint32),
    ]

class SDL_TextInputEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("text", (c_char * SDL_TEXTINPUTEVENT_TEXT_SIZE)),
    ]

class SDL_MouseMotionEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("which", Uint32),
        ("state", Uint32),
        ("x", Sint32),
        ("y", Sint32),
        ("xrel", Sint32),
        ("yrel", Sint32),
    ]

class SDL_MouseButtonEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("which", Uint32),
        ("button", Uint8),
        ("state", Uint8),
        ("clicks", Uint8),
        ("padding1", Uint8),
        ("x", Sint32),
        ("y", Sint32),
    ]

_mousewheel_fields = [
    ("type", Uint32),
    ("timestamp", Uint32),
    ("windowID", Uint32),
    ("which", Uint32),
    ("x", Sint32),
    ("y", Sint32),
    ("direction", Uint32),
]
if sdl_version >= 2018:
    _mousewheel_fields += [
        ("preciseX", c_float),
        ("preciseY", c_float)
    ]
if sdl_version >= 2260:
    _mousewheel_fields += [
        ("mouseX", Sint32),
        ("mouseY", Sint32)
    ]
class SDL_MouseWheelEvent(Structure):
    _fields_ = _mousewheel_fields

class SDL_JoyAxisEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("axis", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("value", Sint16),
        ("padding4", Uint16),
    ]

class SDL_JoyBallEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("ball", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("xrel", Sint16),
        ("yrel", Sint16),
    ]

class SDL_JoyHatEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("hat", Uint8),
        ("value", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
    ]

class SDL_JoyButtonEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("button", Uint8),
        ("state", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
    ]

class SDL_JoyDeviceEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", Sint32),
    ]

class SDL_JoyBatteryEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("level", SDL_JoystickPowerLevel),
    ]

class SDL_ControllerAxisEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("axis", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
        ("value", Sint16),
        ("padding4", Uint16),
    ]

class SDL_ControllerButtonEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("button", Uint8),
        ("state", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
    ]

class SDL_ControllerDeviceEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", Sint32),
    ]

class SDL_ControllerTouchpadEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", SDL_JoystickID),
        ("touchpad", Sint32),
        ("finger", Sint32),
        ("x", c_float),
        ("y", c_float),
        ("pressure", c_float),
    ]

_controller_sensor_fields = [
    ("type", Uint32),
    ("timestamp", Uint32),
    ("which", SDL_JoystickID),
    ("sensor", Sint32),
    ("data", c_float * 3),
]
if sdl_version >= 2260:
    _controller_sensor_fields += [
        ("timestamp_us", Uint64)
    ]
class SDL_ControllerSensorEvent(Structure):
    _fields_ = _controller_sensor_fields

class SDL_AudioDeviceEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("which", Uint32),
        ("iscapture", Uint8),
        ("padding1", Uint8),
        ("padding2", Uint8),
        ("padding3", Uint8),
    ]

_touchfinger_fields = [
    ("type", Uint32),
    ("timestamp", Uint32),
    ("touchId", SDL_TouchID),
    ("fingerId", SDL_FingerID),
    ("x", c_float),
    ("y", c_float),
    ("dx", c_float),
    ("dy", c_float),
    ("pressure", c_float),
]
if sdl_version >= 2012:
    _touchfinger_fields += [("windowID", Uint32)]
class SDL_TouchFingerEvent(Structure):
    _fields_ = _touchfinger_fields

class SDL_MultiGestureEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("touchId", SDL_TouchID),
        ("dTheta", c_float),
        ("dDist", c_float),
        ("x", c_float),
        ("y", c_float),
        ("numFingers", Uint16),
        ("padding", Uint16),
    ]

class SDL_DollarGestureEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("touchId", SDL_TouchID),
        ("gestureId", SDL_GestureID),
        ("numFingers", Uint32),
        ("error", c_float),
        ("x", c_float),
        ("y", c_float),
    ]

class SDL_DropEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("file", c_char_p),
        ("windowID", Uint32),
    ]

_sensor_fields = [
    ("type", Uint32),
    ("timestamp", Uint32),
    ("which", Sint32),
    ("data", (c_float * 6)),
]
if sdl_version >= 2260:
    _sensor_fields += [
        ("timestamp_us", Uint64)
    ]
class SDL_SensorEvent(Structure):
    _fields_ = _sensor_fields

class SDL_QuitEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
    ]

class SDL_OSEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
    ]

class SDL_UserEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("windowID", Uint32),
        ("code", Sint32),
        ("data1", c_void_p),
        ("data2", c_void_p),
    ]

class SDL_SysWMEvent(Structure):
    _fields_ = [
        ("type", Uint32),
        ("timestamp", Uint32),
        ("msg", _P(SDL_SysWMmsg)),
    ]

_event_pad_size = 56 if sizeof(c_void_p) <= 8 else 64
if sizeof(c_void_p) > 16:
    _event_pad_size = 3 * sizeof(c_void_p)

class SDL_Event(Union):
    _fields_ = [
        ("type", Uint32),
        ("common", SDL_CommonEvent),
        ("display", SDL_DisplayEvent),
        ("window", SDL_WindowEvent),
        ("key", SDL_KeyboardEvent),
        ("edit", SDL_TextEditingEvent),
        ("editExt", SDL_TextEditingExtEvent),
        ("text", SDL_TextInputEvent),
        ("motion", SDL_MouseMotionEvent),
        ("button", SDL_MouseButtonEvent),
        ("wheel", SDL_MouseWheelEvent),
        ("jaxis", SDL_JoyAxisEvent),
        ("jball", SDL_JoyBallEvent),
        ("jhat", SDL_JoyHatEvent),
        ("jbutton", SDL_JoyButtonEvent),
        ("jdevice", SDL_JoyDeviceEvent),
        ("jbattery", SDL_JoyBatteryEvent),
        ("caxis", SDL_ControllerAxisEvent),
        ("cbutton", SDL_ControllerButtonEvent),
        ("cdevice", SDL_ControllerDeviceEvent),
        ("ctouchpad", SDL_ControllerTouchpadEvent),
        ("csensor", SDL_ControllerSensorEvent),
        ("adevice", SDL_AudioDeviceEvent),
        ("sensor", SDL_SensorEvent),
        ("quit", SDL_QuitEvent),
        ("user", SDL_UserEvent),
        ("syswm", SDL_SysWMEvent),
        ("tfinger", SDL_TouchFingerEvent),
        ("mgesture", SDL_MultiGestureEvent),
        ("dgesture", SDL_DollarGestureEvent),
        ("drop", SDL_DropEvent),
        ("padding", (Uint8 * _event_pad_size)),
    ]


# Callback function definitions

SDL_EventFilter = CFUNCTYPE(c_int, c_void_p, _P(SDL_Event))


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_PumpEvents"),
    SDLFunc("SDL_PeepEvents", [_P(SDL_Event), c_int, SDL_eventaction, Uint32, Uint32], c_int),
    SDLFunc("SDL_HasEvent", [Uint32], SDL_bool),
    SDLFunc("SDL_HasEvents", [Uint32, Uint32], SDL_bool),
    SDLFunc("SDL_FlushEvent", [Uint32]),
    SDLFunc("SDL_FlushEvents", [Uint32, Uint32]),
    SDLFunc("SDL_PollEvent", [_P(SDL_Event)], c_int),
    SDLFunc("SDL_WaitEvent", [_P(SDL_Event)], c_int),
    SDLFunc("SDL_WaitEventTimeout", [_P(SDL_Event), c_int], c_int),
    SDLFunc("SDL_PushEvent", [_P(SDL_Event)], c_int),
    SDLFunc("SDL_SetEventFilter", [SDL_EventFilter, c_void_p]),
    SDLFunc("SDL_GetEventFilter", [_P(SDL_EventFilter), _P(c_void_p)], SDL_bool),
    SDLFunc("SDL_AddEventWatch", [SDL_EventFilter, c_void_p]),
    SDLFunc("SDL_DelEventWatch", [SDL_EventFilter, c_void_p]),
    SDLFunc("SDL_FilterEvents", [SDL_EventFilter, c_void_p]),
    SDLFunc("SDL_EventState", [Uint32, c_int], Uint8),
    SDLFunc("SDL_RegisterEvents", [c_int], Uint32),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_PumpEvents = _ctypes["SDL_PumpEvents"]
SDL_PeepEvents = _ctypes["SDL_PeepEvents"]
SDL_HasEvent = _ctypes["SDL_HasEvent"]
SDL_HasEvents = _ctypes["SDL_HasEvents"]
SDL_FlushEvent = _ctypes["SDL_FlushEvent"]
SDL_FlushEvents = _ctypes["SDL_FlushEvents"]
SDL_PollEvent = _ctypes["SDL_PollEvent"]
SDL_WaitEvent = _ctypes["SDL_WaitEvent"]
SDL_WaitEventTimeout = _ctypes["SDL_WaitEventTimeout"]
SDL_PushEvent = _ctypes["SDL_PushEvent"]
SDL_SetEventFilter = _ctypes["SDL_SetEventFilter"]
SDL_GetEventFilter = _ctypes["SDL_GetEventFilter"]
SDL_AddEventWatch = _ctypes["SDL_AddEventWatch"]
SDL_DelEventWatch = _ctypes["SDL_DelEventWatch"]
SDL_FilterEvents = _ctypes["SDL_FilterEvents"]
SDL_EventState = _ctypes["SDL_EventState"]
SDL_GetEventState = lambda t: SDL_EventState(t, SDL_QUERY)
SDL_RegisterEvents = _ctypes["SDL_RegisterEvents"]


# SDL_quit.h
def SDL_QuitRequested():
    SDL_PumpEvents()
    return SDL_PeepEvents(None, 0, SDL_PEEKEVENT, SDL_QUIT, SDL_QUIT) > 0
