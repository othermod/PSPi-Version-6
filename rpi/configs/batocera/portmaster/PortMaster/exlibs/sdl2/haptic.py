from ctypes import c_int, c_uint, c_float, c_char_p, c_void_p, Structure, Union
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint16, Uint32, Sint16, Sint32
from .joystick import SDL_Joystick

__all__ = [
    # Structs, Unions, & Opaque Types
    "SDL_Haptic", "SDL_HapticDirection", "SDL_HapticConstant", 
    "SDL_HapticPeriodic", "SDL_HapticCondition", "SDL_HapticRamp",
    "SDL_HapticLeftRight", "SDL_HapticCustom", "SDL_HapticEffect",

    # Defines
    "SDL_HAPTIC_CONSTANT", "SDL_HAPTIC_SINE", "SDL_HAPTIC_LEFTRIGHT",
    "SDL_HAPTIC_TRIANGLE", "SDL_HAPTIC_SAWTOOTHUP", "SDL_HAPTIC_SAWTOOTHDOWN",
    "SDL_HAPTIC_RAMP", "SDL_HAPTIC_SPRING", "SDL_HAPTIC_DAMPER",
    "SDL_HAPTIC_INERTIA", "SDL_HAPTIC_FRICTION", "SDL_HAPTIC_CUSTOM",
    "SDL_HAPTIC_GAIN", "SDL_HAPTIC_AUTOCENTER", "SDL_HAPTIC_STATUS",
    "SDL_HAPTIC_PAUSE", "SDL_HAPTIC_POLAR", "SDL_HAPTIC_CARTESIAN",
    "SDL_HAPTIC_SPHERICAL", "SDL_HAPTIC_STEERING_AXIS", "SDL_HAPTIC_INFINITY",
]


# Constants & enums

SDL_HAPTIC_CONSTANT = 1 << 0
SDL_HAPTIC_SINE = 1 << 1
SDL_HAPTIC_LEFTRIGHT = 1 << 2
SDL_HAPTIC_TRIANGLE = 1 << 3
SDL_HAPTIC_SAWTOOTHUP = 1 << 4
SDL_HAPTIC_SAWTOOTHDOWN = 1 << 5
SDL_HAPTIC_RAMP = 1 << 6
SDL_HAPTIC_SPRING = 1 << 7
SDL_HAPTIC_DAMPER = 1 << 8
SDL_HAPTIC_INERTIA = 1 << 9
SDL_HAPTIC_FRICTION = 1 << 10
SDL_HAPTIC_CUSTOM = 1 << 11
SDL_HAPTIC_GAIN = 1 << 12
SDL_HAPTIC_AUTOCENTER = 1 << 13
SDL_HAPTIC_STATUS = 1 << 14
SDL_HAPTIC_PAUSE = 1 << 15
SDL_HAPTIC_POLAR = 0
SDL_HAPTIC_CARTESIAN = 1
SDL_HAPTIC_SPHERICAL = 2
SDL_HAPTIC_STEERING_AXIS = 3
SDL_HAPTIC_INFINITY = 4294967295


# Structs & opaque typedefs

class SDL_Haptic(c_void_p):
    pass

class SDL_HapticDirection(Structure):
    _fields_ = [
        ("type", Uint8),
        ("dir", (Sint32 * 3))
    ]

class SDL_HapticConstant(Structure):
    _fields_ = [
        ("type", Uint16),
        ("direction", SDL_HapticDirection),
        ("length", Uint32),
        ("delay", Uint16),
        ("button", Uint16),
        ("interval", Uint16),
        ("level", Sint16),
        ("attack_length", Uint16),
        ("attack_level", Uint16),
        ("fade_length", Uint16),
        ("fade_level", Uint16),
    ]

class SDL_HapticPeriodic(Structure):
    _fields_ = [
        ("type", Uint16),
        ("direction", SDL_HapticDirection),
        ("length", Uint32),
        ("delay", Uint16),
        ("button", Uint16),
        ("interval", Uint16),
        ("period", Uint16),
        ("magnitude", Sint16),
        ("offset", Sint16),
        ("phase", Uint16),
        ("attack_length", Uint16),
        ("attack_level", Uint16),
        ("fade_length", Uint16),
        ("fade_level", Uint16),
    ]

class SDL_HapticCondition(Structure):
    """A conditionally running effect."""
    _fields_ = [
        ("type", Uint16),
        ("direction", SDL_HapticDirection),
        ("length", Uint32),
        ("delay", Uint16),
        ("button", Uint16),
        ("interval", Uint16),
        ("right_sat", (Uint16 * 3)),
        ("left_sat", (Uint16 * 3)),
        ("right_coeff", (Sint16 * 3)),
        ("left_coeff", (Sint16 * 3)),
        ("deadband", (Uint16 * 3)),
        ("center", (Sint16 * 3)),
    ]

class SDL_HapticRamp(Structure):
    """A ramp-like effect."""
    _fields_ = [
        ("type", Uint16),
        ("direction", SDL_HapticDirection),
        ("length", Uint32),
        ("delay", Uint16),
        ("button", Uint16),
        ("interval", Uint16),
        ("start", Sint16),
        ("end", Sint16),
        ("attack_length", Uint16),
        ("attack_level", Uint16),
        ("fade_length", Uint16),
        ("fade_level", Uint16),
    ]

class SDL_HapticLeftRight(Structure):
    """A left-right effect."""
    _fields_ = [
        ("type", Uint16),
        ("length", Uint32),
        ("large_magnitude", Uint16),
        ("small_magnitude", Uint16),
    ]

class SDL_HapticCustom(Structure):
    """A custom effect."""
    _fields_ = [
        ("type", Uint16),
        ("direction", SDL_HapticDirection),
        ("length", Uint32),
        ("delay", Uint16),
        ("button", Uint16),
        ("interval", Uint16),
        ("channels", Uint8),
        ("period", Uint16),
        ("samples", Uint16),
        ("data", _P(Uint16)),
        ("attack_length", Uint16),
        ("attack_level", Uint16),
        ("fade_length", Uint16),
        ("fade_level", Uint16),
    ]

class SDL_HapticEffect(Union):
    """A generic haptic effect, containing the concrete haptic effect."""
    _fields_ = [
        ("type", Uint16),
        ("constant", SDL_HapticConstant),
        ("periodic", SDL_HapticPeriodic),
        ("condition", SDL_HapticCondition),
        ("ramp", SDL_HapticRamp),
        ("leftright", SDL_HapticLeftRight),
        ("custom", SDL_HapticCustom),
    ]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_NumHaptics", None, c_int),
    SDLFunc("SDL_HapticName", [c_int], c_char_p),
    SDLFunc("SDL_HapticOpen", [c_int], _P(SDL_Haptic)),
    SDLFunc("SDL_HapticOpened", [c_int], c_int),
    SDLFunc("SDL_HapticIndex", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_MouseIsHaptic", None, c_int),
    SDLFunc("SDL_HapticOpenFromMouse", None, _P(SDL_Haptic)),
    SDLFunc("SDL_JoystickIsHaptic", [_P(SDL_Joystick)], c_int),
    SDLFunc("SDL_HapticOpenFromJoystick", [_P(SDL_Joystick)], _P(SDL_Haptic)),
    SDLFunc("SDL_HapticClose", [_P(SDL_Haptic)]),
    SDLFunc("SDL_HapticNumEffects", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticNumEffectsPlaying", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticQuery", [_P(SDL_Haptic)], c_uint),
    SDLFunc("SDL_HapticNumAxes", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticEffectSupported", [_P(SDL_Haptic), _P(SDL_HapticEffect)], c_int),
    SDLFunc("SDL_HapticNewEffect", [_P(SDL_Haptic), _P(SDL_HapticEffect)], c_int),
    SDLFunc("SDL_HapticUpdateEffect", [_P(SDL_Haptic), c_int, _P(SDL_HapticEffect)], c_int),
    SDLFunc("SDL_HapticRunEffect", [_P(SDL_Haptic), c_int, Uint32], c_int),
    SDLFunc("SDL_HapticStopEffect", [_P(SDL_Haptic), c_int], c_int),
    SDLFunc("SDL_HapticDestroyEffect", [_P(SDL_Haptic), c_int]),
    SDLFunc("SDL_HapticGetEffectStatus", [_P(SDL_Haptic), c_int], c_int),
    SDLFunc("SDL_HapticSetGain", [_P(SDL_Haptic), c_int], c_int),
    SDLFunc("SDL_HapticSetAutocenter", [_P(SDL_Haptic), c_int], c_int),
    SDLFunc("SDL_HapticPause", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticUnpause", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticStopAll", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticRumbleSupported", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticRumbleInit", [_P(SDL_Haptic)], c_int),
    SDLFunc("SDL_HapticRumblePlay", [_P(SDL_Haptic), c_float, Uint32], c_int),
    SDLFunc("SDL_HapticRumbleStop", [_P(SDL_Haptic)], c_int),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_NumHaptics = _ctypes["SDL_NumHaptics"]
SDL_HapticName = _ctypes["SDL_HapticName"]
SDL_HapticOpen = _ctypes["SDL_HapticOpen"]
SDL_HapticOpened = _ctypes["SDL_HapticOpened"]
SDL_HapticIndex = _ctypes["SDL_HapticIndex"]
SDL_MouseIsHaptic = _ctypes["SDL_MouseIsHaptic"]
SDL_HapticOpenFromMouse = _ctypes["SDL_HapticOpenFromMouse"]
SDL_JoystickIsHaptic = _ctypes["SDL_JoystickIsHaptic"]
SDL_HapticOpenFromJoystick = _ctypes["SDL_HapticOpenFromJoystick"]
SDL_HapticClose = _ctypes["SDL_HapticClose"]
SDL_HapticNumEffects = _ctypes["SDL_HapticNumEffects"]
SDL_HapticNumEffectsPlaying = _ctypes["SDL_HapticNumEffectsPlaying"]
SDL_HapticQuery = _ctypes["SDL_HapticQuery"]
SDL_HapticNumAxes = _ctypes["SDL_HapticNumAxes"]
SDL_HapticEffectSupported = _ctypes["SDL_HapticEffectSupported"]
SDL_HapticNewEffect = _ctypes["SDL_HapticNewEffect"]
SDL_HapticUpdateEffect = _ctypes["SDL_HapticUpdateEffect"]
SDL_HapticRunEffect = _ctypes["SDL_HapticRunEffect"]
SDL_HapticStopEffect = _ctypes["SDL_HapticStopEffect"]
SDL_HapticDestroyEffect = _ctypes["SDL_HapticDestroyEffect"]
SDL_HapticGetEffectStatus = _ctypes["SDL_HapticGetEffectStatus"]
SDL_HapticSetGain = _ctypes["SDL_HapticSetGain"]
SDL_HapticSetAutocenter = _ctypes["SDL_HapticSetAutocenter"]
SDL_HapticPause = _ctypes["SDL_HapticPause"]
SDL_HapticUnpause = _ctypes["SDL_HapticUnpause"]
SDL_HapticStopAll = _ctypes["SDL_HapticStopAll"]
SDL_HapticRumbleSupported = _ctypes["SDL_HapticRumbleSupported"]
SDL_HapticRumbleInit = _ctypes["SDL_HapticRumbleInit"]
SDL_HapticRumblePlay = _ctypes["SDL_HapticRumblePlay"]
SDL_HapticRumbleStop = _ctypes["SDL_HapticRumbleStop"]
