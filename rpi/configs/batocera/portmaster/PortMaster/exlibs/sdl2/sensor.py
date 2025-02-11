from ctypes import c_char_p, c_int, c_float, c_void_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint64, Uint32


__all__ = [
    # Structs
    "SDL_Sensor",

    # Defines
    "SDL_SensorID", "SDL_STANDARD_GRAVITY",

    # Enums
    "SDL_SensorType",
    "SDL_SENSOR_INVALID", "SDL_SENSOR_UNKNOWN", "SDL_SENSOR_ACCEL",
    "SDL_SENSOR_GYRO", "SDL_SENSOR_ACCEL_L", "SDL_SENSOR_GYRO_L",
    "SDL_SENSOR_ACCEL_R", "SDL_SENSOR_GYRO_R",
]


# Constants & enums

SDL_SensorType = c_int
SDL_SENSOR_INVALID = -1
SDL_SENSOR_UNKNOWN = 0
SDL_SENSOR_ACCEL = 1
SDL_SENSOR_GYRO = 2
SDL_SENSOR_ACCEL_L = 3
SDL_SENSOR_GYRO_L = 4
SDL_SENSOR_ACCEL_R = 5
SDL_SENSOR_GYRO_R = 6

SDL_STANDARD_GRAVITY = 9.80665


# Structs & typedefs

SDL_SensorID = Uint32

class SDL_Sensor(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_LockSensors", None, None, added='2.0.14'),
    SDLFunc("SDL_UnlockSensors", None, None, added='2.0.14'),
    SDLFunc("SDL_NumSensors", None, c_int, added='2.0.9'),
    SDLFunc("SDL_SensorGetDeviceName", [c_int], c_char_p, added='2.0.9'),
    SDLFunc("SDL_SensorGetDeviceType", [c_int], SDL_SensorType, added='2.0.9'),
    SDLFunc("SDL_SensorGetDeviceNonPortableType", [c_int], c_int, added='2.0.9'),
    SDLFunc("SDL_SensorGetDeviceInstanceID", [c_int], SDL_SensorID, added='2.0.9'),
    SDLFunc("SDL_SensorOpen", [c_int], _P(SDL_Sensor), added='2.0.9'),
    SDLFunc("SDL_SensorFromInstanceID", [SDL_SensorID], _P(SDL_Sensor), added='2.0.9'),
    SDLFunc("SDL_SensorGetName", [_P(SDL_Sensor)], c_char_p, added='2.0.9'),
    SDLFunc("SDL_SensorGetType", [_P(SDL_Sensor)], SDL_SensorType, added='2.0.9'),
    SDLFunc("SDL_SensorGetNonPortableType", [_P(SDL_Sensor)], c_int, added='2.0.9'),
    SDLFunc("SDL_SensorGetInstanceID", [_P(SDL_Sensor)], SDL_SensorID, added='2.0.9'),
    SDLFunc("SDL_SensorGetData", [_P(SDL_Sensor), _P(c_float), c_int], c_int, added='2.0.9'),
    SDLFunc("SDL_SensorGetDataWithTimestamp",
        [_P(SDL_Sensor), _P(Uint64), _P(c_float), c_int],
        c_int, added = '2.26.0'
    ),
    SDLFunc("SDL_SensorClose", [_P(SDL_Sensor)], None, added='2.0.9'),
    SDLFunc("SDL_SensorUpdate", None, None, added='2.0.9'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_LockSensors = _ctypes["SDL_LockSensors"]
SDL_UnlockSensors = _ctypes["SDL_UnlockSensors"]
SDL_NumSensors = _ctypes["SDL_NumSensors"]
SDL_SensorGetDeviceName = _ctypes["SDL_SensorGetDeviceName"]
SDL_SensorGetDeviceType = _ctypes["SDL_SensorGetDeviceType"]
SDL_SensorGetDeviceNonPortableType = _ctypes["SDL_SensorGetDeviceNonPortableType"]
SDL_SensorGetDeviceInstanceID = _ctypes["SDL_SensorGetDeviceInstanceID"]
SDL_SensorOpen = _ctypes["SDL_SensorOpen"]
SDL_SensorFromInstanceID = _ctypes["SDL_SensorFromInstanceID"]
SDL_SensorGetName = _ctypes["SDL_SensorGetName"]
SDL_SensorGetType = _ctypes["SDL_SensorGetType"]
SDL_SensorGetNonPortableType = _ctypes["SDL_SensorGetNonPortableType"]
SDL_SensorGetInstanceID = _ctypes["SDL_SensorGetInstanceID"]
SDL_SensorGetData = _ctypes["SDL_SensorGetData"] # Needs testing
SDL_SensorGetDataWithTimestamp = _ctypes["SDL_SensorGetDataWithTimestamp"] # Needs testing
SDL_SensorClose = _ctypes["SDL_SensorClose"]
SDL_SensorUpdate = _ctypes["SDL_SensorUpdate"]
