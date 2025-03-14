from ctypes import c_int, c_char_p, c_double, c_void_p, CFUNCTYPE, Structure
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .endian import SDL_BYTEORDER, SDL_LIL_ENDIAN
from .stdinc import Uint8, Uint16, Uint32
from .rwops import SDL_RWops, SDL_RWFromFile

__all__ = [
    # Structs & Opaque Types
    "SDL_AudioSpec", "SDL_AudioCVT",

    # Defines
    "SDL_AudioFormat", "SDL_AUDIO_MASK_BITSIZE", "SDL_AUDIO_MASK_DATATYPE",
    "SDL_AUDIO_MASK_ENDIAN", "SDL_AUDIO_MASK_SIGNED", "SDL_AUDIO_BITSIZE",
    "SDL_AUDIO_ISFLOAT",
    "AUDIO_U8", "AUDIO_S8",
    "AUDIO_U16LSB", "AUDIO_U16MSB", "AUDIO_U16", "AUDIO_U16SYS",
    "AUDIO_S16LSB", "AUDIO_S16MSB", "AUDIO_S16", "AUDIO_S16SYS",
    "AUDIO_S32LSB", "AUDIO_S32MSB", "AUDIO_S32", "AUDIO_S32SYS",
    "AUDIO_F32LSB", "AUDIO_F32MSB", "AUDIO_F32", "AUDIO_F32SYS",
    "SDL_AUDIO_ALLOW_FREQUENCY_CHANGE", "SDL_AUDIO_ALLOW_FORMAT_CHANGE",
    "SDL_AUDIO_ALLOW_CHANNELS_CHANGE", "SDL_AUDIO_ALLOW_SAMPLES_CHANGE",
    "SDL_AUDIO_ALLOW_ANY_CHANGE",
    "SDL_AUDIOCVT_MAX_FILTERS", "SDL_MIX_MAXVOLUME",

    # Enums
    "SDL_AudioStatus",
    "SDL_AUDIO_STOPPED", "SDL_AUDIO_PLAYING", "SDL_AUDIO_PAUSED", 

    # Macro Functions
    "SDL_AUDIO_ISBIGENDIAN", "SDL_AUDIO_ISSIGNED", "SDL_AUDIO_ISINT",
    "SDL_AUDIO_ISLITTLEENDIAN", "SDL_AUDIO_ISUNSIGNED", "SDL_LoadWAV",

    # Callback Functions
    "SDL_AudioCallback", "SDL_AudioFilter",

    # Convenience Variables
    "AUDIO_FORMATS"
]


# Constants & enums

SDL_AUDIO_MASK_BITSIZE = 0xFF
SDL_AUDIO_MASK_DATATYPE = 1 << 8
SDL_AUDIO_MASK_ENDIAN = 1 << 12
SDL_AUDIO_MASK_SIGNED = 1 << 15
SDL_AUDIO_BITSIZE = lambda x: (x & SDL_AUDIO_MASK_BITSIZE)
SDL_AUDIO_ISFLOAT = lambda x: (x & SDL_AUDIO_MASK_DATATYPE)
SDL_AUDIO_ISBIGENDIAN = lambda x: (x & SDL_AUDIO_MASK_ENDIAN)
SDL_AUDIO_ISSIGNED = lambda x: (x & SDL_AUDIO_MASK_SIGNED)
SDL_AUDIO_ISINT = lambda x: (not SDL_AUDIO_ISFLOAT(x))
SDL_AUDIO_ISLITTLEENDIAN = lambda x: (not SDL_AUDIO_ISBIGENDIAN(x))
SDL_AUDIO_ISUNSIGNED = lambda x: (not SDL_AUDIO_ISSIGNED(x))

AUDIO_U8 = 0x0008
AUDIO_S8 = 0x8008
AUDIO_U16LSB = 0x0010
AUDIO_S16LSB = 0x8010
AUDIO_U16MSB = 0x1010
AUDIO_S16MSB = 0x9010
AUDIO_U16 = AUDIO_U16LSB
AUDIO_S16 = AUDIO_S16LSB
AUDIO_S32LSB = 0x8020
AUDIO_S32MSB = 0x9020
AUDIO_S32 = AUDIO_S32LSB
AUDIO_F32LSB = 0x8120
AUDIO_F32MSB = 0x9120
AUDIO_F32 = AUDIO_F32LSB

# All of the audio formats should be in this set which is provided as a
# convenience to the end user for purposes of iteration and validation.
# (is the provided audio format in the supported set?)
FORMAT_NAME_MAP = {
    AUDIO_U8: "AUDIO_U8",
    AUDIO_S8: "AUDIO_S8",
    AUDIO_U16LSB: "AUDIO_U16LSB",
    AUDIO_S16LSB: "AUDIO_S16LSB",
    AUDIO_U16MSB: "AUDIO_U16MSB",
    AUDIO_S16MSB: "AUDIO_S16MSB",
    AUDIO_S32LSB: "AUDIO_S32LSB",
    AUDIO_S32MSB: "AUDIO_S32MSB",
    AUDIO_F32LSB: "AUDIO_F32LSB",
    AUDIO_F32MSB: "AUDIO_F32MSB",
}
AUDIO_FORMATS = set([
    AUDIO_U8, AUDIO_S8,
    AUDIO_U16LSB, AUDIO_U16MSB, AUDIO_U16,
    AUDIO_S16LSB, AUDIO_S16MSB, AUDIO_S16,
    AUDIO_S32LSB, AUDIO_S32MSB, AUDIO_S32,
    AUDIO_F32LSB, AUDIO_F32MSB, AUDIO_F32
])

if SDL_BYTEORDER == SDL_LIL_ENDIAN:
    AUDIO_U16SYS = AUDIO_U16LSB
    AUDIO_S16SYS = AUDIO_S16LSB
    AUDIO_S32SYS = AUDIO_S32LSB
    AUDIO_F32SYS = AUDIO_F32LSB
else:
    AUDIO_U16SYS = AUDIO_U16MSB
    AUDIO_S16SYS = AUDIO_S16MSB
    AUDIO_S32SYS = AUDIO_S32MSB
    AUDIO_F32SYS = AUDIO_F32MSB

SDL_AUDIO_ALLOW_FREQUENCY_CHANGE = 0x00000001
SDL_AUDIO_ALLOW_FORMAT_CHANGE = 0x00000002
SDL_AUDIO_ALLOW_CHANNELS_CHANGE = 0x00000004
SDL_AUDIO_ALLOW_SAMPLES_CHANGE = 0x00000008
SDL_AUDIO_ALLOW_ANY_CHANGE = (
    SDL_AUDIO_ALLOW_FREQUENCY_CHANGE | SDL_AUDIO_ALLOW_FORMAT_CHANGE |
    SDL_AUDIO_ALLOW_CHANNELS_CHANGE | SDL_AUDIO_ALLOW_SAMPLES_CHANGE
)

SDL_AudioStatus = c_int
SDL_AUDIO_STOPPED = 0
SDL_AUDIO_PLAYING = 1
SDL_AUDIO_PAUSED = 2

SDL_MIX_MAXVOLUME = 128
SDL_AUDIOCVT_MAX_FILTERS = 9


# Structs, typedefs, and callback definitions

SDL_AudioFormat = Uint16
SDL_AudioDeviceID = Uint32

SDL_AudioCallback = CFUNCTYPE(None, c_void_p, _P(Uint8), c_int)

class SDL_AudioSpec(Structure):
    _fields_ = [
        ("freq", c_int),
        ("format", SDL_AudioFormat),
        ("channels", Uint8),
        ("silence", Uint8),
        ("samples", Uint16),
        ("padding", Uint16),
        ("size", Uint32),
        ("callback", SDL_AudioCallback),
        ("userdata", c_void_p),
    ]
    def __init__(
        self, freq, aformat, channels, samples, callback=SDL_AudioCallback(),
        userdata=c_void_p(0)
    ):
        super(SDL_AudioSpec, self).__init__()
        self.freq = freq
        self.format = aformat
        self.channels = channels
        self.samples = samples
        self.callback = callback
        self.userdata = userdata

class SDL_AudioCVT(Structure):
    pass

SDL_AudioFilter = CFUNCTYPE(_P(SDL_AudioCVT), SDL_AudioFormat)

SDL_AudioCVT._fields_ = [
    ("needed", c_int),
    ("src_format", SDL_AudioFormat),
    ("dst_format", SDL_AudioFormat),
    ("rate_incr", c_double),
    ("buf", _P(Uint8)),
    ("len", c_int),
    ("len_cvt", c_int),
    ("len_mult", c_int),
    ("len_ratio", c_double),
    ("filters", (SDL_AudioFilter * (SDL_AUDIOCVT_MAX_FILTERS+1))),
    ("filter_index", c_int),
]

class SDL_AudioStream(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetNumAudioDrivers", None, c_int),
    SDLFunc("SDL_GetAudioDriver", [c_int], c_char_p),
    SDLFunc("SDL_AudioInit", [c_char_p], c_int),
    SDLFunc("SDL_AudioQuit"),
    SDLFunc("SDL_GetCurrentAudioDriver", None, c_char_p),
    SDLFunc("SDL_OpenAudio", [_P(SDL_AudioSpec), _P(SDL_AudioSpec)], c_int),
    SDLFunc("SDL_GetNumAudioDevices", [c_int], c_int),
    SDLFunc("SDL_GetAudioDeviceName", [c_int, c_int], c_char_p),
    SDLFunc("SDL_GetAudioDeviceSpec", [c_int, c_int, _P(SDL_AudioSpec)], c_int, added='2.0.16'),
    SDLFunc("SDL_GetDefaultAudioInfo",
        [_P(c_char_p), _P(SDL_AudioSpec), c_int],
        returns = c_int, added = '2.24.0'
    ),
    SDLFunc("SDL_OpenAudioDevice",
        [c_char_p, c_int, _P(SDL_AudioSpec), _P(SDL_AudioSpec), c_int],
        returns = SDL_AudioDeviceID
    ),
    SDLFunc("SDL_GetAudioStatus", None, SDL_AudioStatus),
    SDLFunc("SDL_GetAudioDeviceStatus", [SDL_AudioDeviceID], SDL_AudioStatus),
    SDLFunc("SDL_PauseAudio", [c_int]),
    SDLFunc("SDL_PauseAudioDevice", [SDL_AudioDeviceID, c_int]),
    SDLFunc("SDL_LoadWAV_RW",
        [_P(SDL_RWops), c_int, _P(SDL_AudioSpec), _P(_P(Uint8)), _P(Uint32)],
        returns = _P(SDL_AudioSpec)
    ),
    SDLFunc("SDL_FreeWAV", [_P(Uint8)]),
    SDLFunc("SDL_BuildAudioCVT",
        [_P(SDL_AudioCVT), SDL_AudioFormat, Uint8, c_int, SDL_AudioFormat, Uint8, c_int],
        returns = c_int
    ),
    SDLFunc("SDL_ConvertAudio", [_P(SDL_AudioCVT)], c_int),
    SDLFunc("SDL_MixAudio", [_P(Uint8), _P(Uint8), Uint32, c_int]),
    SDLFunc("SDL_MixAudioFormat", [_P(Uint8), _P(Uint8), SDL_AudioFormat, Uint32, c_int]),
    SDLFunc("SDL_LockAudio"),
    SDLFunc("SDL_LockAudioDevice", [SDL_AudioDeviceID]),
    SDLFunc("SDL_UnlockAudio"),
    SDLFunc("SDL_UnlockAudioDevice", [SDL_AudioDeviceID]),
    SDLFunc("SDL_CloseAudio"),
    SDLFunc("SDL_CloseAudioDevice", [SDL_AudioDeviceID]),
    SDLFunc("SDL_QueueAudio", [SDL_AudioDeviceID, c_void_p, Uint32], c_int, added='2.0.4'),
    SDLFunc("SDL_DequeueAudio", [SDL_AudioDeviceID, c_void_p, Uint32], Uint32, added='2.0.5'),
    SDLFunc("SDL_GetQueuedAudioSize", [SDL_AudioDeviceID], Uint32, added='2.0.4'),
    SDLFunc("SDL_ClearQueuedAudio", [SDL_AudioDeviceID], added='2.0.4'),
    SDLFunc("SDL_NewAudioStream",
        [SDL_AudioFormat, Uint8, c_int, SDL_AudioFormat, Uint8, c_int],
        returns = _P(SDL_AudioStream), added = '2.0.7'
    ),
    SDLFunc("SDL_AudioStreamPut", [_P(SDL_AudioStream), c_void_p, c_int], c_int, added='2.0.7'),
    SDLFunc("SDL_AudioStreamGet", [_P(SDL_AudioStream), c_void_p, c_int], c_int, added='2.0.7'),
    SDLFunc("SDL_AudioStreamAvailable", [_P(SDL_AudioStream)], c_int, added='2.0.7'),
    SDLFunc("SDL_AudioStreamClear", [_P(SDL_AudioStream)], added='2.0.7'),
    SDLFunc("SDL_FreeAudioStream", [_P(SDL_AudioStream)], added='2.0.7'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetNumAudioDrivers = _ctypes["SDL_GetNumAudioDrivers"]
SDL_GetAudioDriver = _ctypes["SDL_GetAudioDriver"]
SDL_AudioInit = _ctypes["SDL_AudioInit"]
SDL_AudioQuit = _ctypes["SDL_AudioQuit"]
SDL_GetCurrentAudioDriver = _ctypes["SDL_GetCurrentAudioDriver"]
SDL_OpenAudio = _ctypes["SDL_OpenAudio"]
SDL_GetNumAudioDevices = _ctypes["SDL_GetNumAudioDevices"]
SDL_GetAudioDeviceName = _ctypes["SDL_GetAudioDeviceName"]
SDL_GetAudioDeviceSpec = _ctypes["SDL_GetAudioDeviceSpec"]
SDL_GetDefaultAudioInfo = _ctypes["SDL_GetDefaultAudioInfo"]
SDL_OpenAudioDevice = _ctypes["SDL_OpenAudioDevice"]
SDL_GetAudioStatus = _ctypes["SDL_GetAudioStatus"]
SDL_GetAudioDeviceStatus = _ctypes["SDL_GetAudioDeviceStatus"]
SDL_PauseAudio = _ctypes["SDL_PauseAudio"]
SDL_PauseAudioDevice = _ctypes["SDL_PauseAudioDevice"]
SDL_LoadWAV_RW = _ctypes["SDL_LoadWAV_RW"]
SDL_LoadWAV = lambda f, s, ab, al: SDL_LoadWAV_RW(SDL_RWFromFile(f, b"rb"), 1, s, ab , al)
SDL_FreeWAV = _ctypes["SDL_FreeWAV"]
SDL_BuildAudioCVT = _ctypes["SDL_BuildAudioCVT"]
SDL_ConvertAudio = _ctypes["SDL_ConvertAudio"]
SDL_MixAudio = _ctypes["SDL_MixAudio"]
SDL_MixAudioFormat = _ctypes["SDL_MixAudioFormat"]
SDL_LockAudio = _ctypes["SDL_LockAudio"]
SDL_LockAudioDevice = _ctypes["SDL_LockAudioDevice"]
SDL_UnlockAudio = _ctypes["SDL_UnlockAudio"]
SDL_UnlockAudioDevice = _ctypes["SDL_UnlockAudioDevice"]
SDL_CloseAudio = _ctypes["SDL_CloseAudio"]
SDL_CloseAudioDevice = _ctypes["SDL_CloseAudioDevice"]
SDL_QueueAudio = _ctypes["SDL_QueueAudio"]
SDL_DequeueAudio = _ctypes["SDL_DequeueAudio"]
SDL_GetQueuedAudioSize = _ctypes["SDL_GetQueuedAudioSize"]
SDL_ClearQueuedAudio = _ctypes["SDL_ClearQueuedAudio"]
SDL_NewAudioStream = _ctypes["SDL_NewAudioStream"]
SDL_AudioStreamPut = _ctypes["SDL_AudioStreamPut"]
SDL_AudioStreamGet = _ctypes["SDL_AudioStreamGet"]
SDL_AudioStreamAvailable = _ctypes["SDL_AudioStreamAvailable"]
SDL_AudioStreamClear = _ctypes["SDL_AudioStreamClear"]
SDL_FreeAudioStream = _ctypes["SDL_FreeAudioStream"]
