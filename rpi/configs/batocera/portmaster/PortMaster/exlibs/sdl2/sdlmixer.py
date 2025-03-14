import os
from ctypes import Structure, CFUNCTYPE, c_int, c_char_p, c_void_p, c_double
from ctypes import POINTER as _P
from .dll import DLL, SDLFunc, AttributeDict
from .version import SDL_version, SDL_VERSIONNUM
from .audio import AUDIO_S16LSB, AUDIO_S16MSB, SDL_MIX_MAXVOLUME
from .stdinc import Uint8, Uint16, Uint32, Sint16, SDL_bool
from .endian import SDL_LIL_ENDIAN, SDL_BYTEORDER
from .rwops import SDL_RWops, SDL_RWFromFile
from .error import SDL_SetError, SDL_GetError, SDL_ClearError, SDL_OutOfMemory

__all__ = [
    # Structs
    "Mix_Chunk", "Mix_Music",

    # Defines
    "SDL_MIXER_MAJOR_VERSION", "SDL_MIXER_MINOR_VERSION",
    "SDL_MIXER_PATCHLEVEL", "MIX_MAJOR_VERSION", "MIX_MINOR_VERSION",
    "MIX_PATCHLEVEL", "MIX_CHANNELS", "MIX_DEFAULT_FREQUENCY",
    "MIX_DEFAULT_FORMAT", "MIX_DEFAULT_CHANNELS", "MIX_MAX_VOLUME",
    "MIX_CHANNEL_POST", "MIX_EFFECTSMAXSPEED",

    # Enums
    "MIX_InitFlags",
    "MIX_INIT_FLAC", "MIX_INIT_MOD", "MIX_INIT_MP3", "MIX_INIT_OGG",
    "MIX_INIT_MID", "MIX_INIT_OPUS",

    "Mix_Fading",
    "MIX_NO_FADING", "MIX_FADING_OUT", "MIX_FADING_IN",

    "Mix_MusicType",
    "MUS_NONE", "MUS_CMD", "MUS_WAV", "MUS_MOD", "MUS_MID", "MUS_OGG",
    "MUS_MP3", "MUS_MP3_MAD_UNUSED", "MUS_FLAC", "MUS_MODPLUG_UNUSED",
    "MUS_OPUS",
    
    # Macro Functions
    "SDL_MIXER_VERSION",  "MIX_VERSION", "SDL_MIXER_COMPILEDVERSION",
    "SDL_MIXER_VERSION_ATLEAST", "Mix_LoadWAV", "Mix_PlayChannel",
    "Mix_FadeInChannel",

    # Callback Functions
    "channel_finished", "music_finished", "mix_func", "soundfont_function",
    "Mix_EffectFunc_t", "Mix_EffectDone_t",

    # Function Aliases
    "Mix_SetError", "Mix_GetError", "Mix_ClearError",

    # Python Functions
    "get_dll_file",
]

try:
    dll = DLL("SDL2_mixer", ["SDL2_mixer", "SDL2_mixer-2.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)


def get_dll_file():
    """Gets the file name of the loaded SDL2_mixer library."""
    return dll.libfile

_bind = dll.bind_function


# Constants, enums, type definitions, and macros

SDL_MIXER_MAJOR_VERSION = 2
SDL_MIXER_MINOR_VERSION = 6
SDL_MIXER_PATCHLEVEL = 1

def SDL_MIXER_VERSION(x):
    x.major = SDL_MIXER_MAJOR_VERSION
    x.minor = SDL_MIXER_MINOR_VERSION
    x.patch = SDL_MIXER_PATCHLEVEL

MIX_MAJOR_VERSION = SDL_MIXER_MAJOR_VERSION
MIX_MINOR_VERSION = SDL_MIXER_MINOR_VERSION
MIX_PATCHLEVEL = SDL_MIXER_PATCHLEVEL
MIX_VERSION = SDL_MIXER_VERSION

SDL_MIXER_COMPILEDVERSION = SDL_VERSIONNUM(SDL_MIXER_MAJOR_VERSION, SDL_MIXER_MINOR_VERSION, SDL_MIXER_PATCHLEVEL)
SDL_MIXER_VERSION_ATLEAST = lambda x, y, z: (SDL_MIXER_COMPILEDVERSION >= SDL_VERSIONNUM(x, y, z))

MIX_InitFlags = c_int
MIX_INIT_FLAC = 0x00000001
MIX_INIT_MOD =  0x00000002
MIX_INIT_MP3 = 0x00000008
MIX_INIT_OGG = 0x000000010
MIX_INIT_MID = 0x00000020
MIX_INIT_OPUS = 0x00000040

Mix_Fading = c_int
MIX_NO_FADING = 0
MIX_FADING_OUT = 1
MIX_FADING_IN = 2

Mix_MusicType = c_int
MUS_NONE = 0
MUS_CMD = 1
MUS_WAV = 2
MUS_MOD = 3
MUS_MID = 4
MUS_OGG = 5
MUS_MP3 = 6
MUS_MP3_MAD_UNUSED = 7
MUS_FLAC = 9
MUS_MODPLUG_UNUSED = 10
MUS_OPUS = 11

MIX_CHANNELS = 8
MIX_DEFAULT_FREQUENCY = 44100
if SDL_BYTEORDER == SDL_LIL_ENDIAN:
    MIX_DEFAULT_FORMAT = AUDIO_S16LSB
else:
    MIX_DEFAULT_FORMAT = AUDIO_S16MSB
MIX_DEFAULT_CHANNELS = 2
MIX_MAX_VOLUME = SDL_MIX_MAXVOLUME

MIX_CHANNEL_POST = -2
MIX_EFFECTSMAXSPEED = "MIX_EFFECTSMAXSPEED"

class Mix_Chunk(Structure):
    """A loaded audio clip to use for playback with the mixer API.

    Chunk objects are created by the :func:`Mix_LoadWAV` and ``Mix_QuickLoad``
    functions, and should be freed using :func:`Mix_FreeChunk` when no longer
    needed.

    Attributes:
        allocated (int): Whether the associated audio buffer will be freed when
            the chunk is freed. ``1`` if the buffer is owned by the chunk, or
            ``0`` if it was allocated by a different function.
        abuf (POINTER(:obj:`~ctypes.c_ubyte`)): A pointer to the chunk's audio
            sample data, in the output format and sample rate of the current
            mixer.
        alen (int): The length of the chunk's audio buffer (in bytes).
        volume (int): The volume of the chunk, with 0 being 0% and 127 being
            100%.

    """
    _fields_ = [
        ("allocated", c_int),
        ("abuf", _P(Uint8)),
        ("alen", Uint32),
        ("volume", Uint8),
    ]

class Mix_Music(c_void_p):
    """The opaque data type representing a loaded music file.

    Music objects are created by the :func:`Mix_LoadMUS` family of functions and
    should be freed using :func:`Mix_FreeMusic` when no longer needed.
    
    """
    pass


# Callback function definitions for various methods 

mix_func = CFUNCTYPE(None, c_void_p, _P(Uint8), c_int)
music_finished = CFUNCTYPE(None)
channel_finished = CFUNCTYPE(None, c_int)
Mix_EffectFunc_t = CFUNCTYPE(None, c_int, c_void_p, c_int, c_void_p)
Mix_EffectDone_t = CFUNCTYPE(None, c_int, c_void_p)
soundfont_function = CFUNCTYPE(c_int, c_char_p, c_void_p)


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("Mix_Linked_Version", None, _P(SDL_version)),
    SDLFunc("Mix_Init", [c_int], c_int),
    SDLFunc("Mix_Quit"),
    SDLFunc("Mix_OpenAudio", [c_int, Uint16, c_int, c_int], c_int),
    SDLFunc("Mix_OpenAudioDevice", [c_int, Uint16, c_int, c_int, c_char_p, c_int], c_int, added='2.0.2'),
    SDLFunc("Mix_AllocateChannels", [c_int], c_int),
    SDLFunc("Mix_QuerySpec", [_P(c_int), _P(Uint16), _P(c_int)], c_int),
    SDLFunc("Mix_LoadWAV_RW", [_P(SDL_RWops), c_int], _P(Mix_Chunk)),
    SDLFunc("Mix_LoadMUS", [c_char_p], _P(Mix_Music)),
    SDLFunc("Mix_LoadMUS_RW", [_P(SDL_RWops)], _P(Mix_Music)),
    SDLFunc("Mix_LoadMUSType_RW", [_P(SDL_RWops), Mix_MusicType, c_int], _P(Mix_Music)),
    SDLFunc("Mix_QuickLoad_WAV", [_P(Uint8)], _P(Mix_Chunk)),
    SDLFunc("Mix_QuickLoad_RAW", [_P(Uint8), Uint32], _P(Mix_Chunk)),
    SDLFunc("Mix_FreeChunk", [_P(Mix_Chunk)]),
    SDLFunc("Mix_FreeMusic", [_P(Mix_Music)]),
    SDLFunc("Mix_GetNumChunkDecoders", None, c_int),
    SDLFunc("Mix_GetChunkDecoder", [c_int], c_char_p),
    SDLFunc("Mix_HasChunkDecoder", [c_char_p], SDL_bool, added='2.0.2'),
    SDLFunc("Mix_GetNumMusicDecoders", None, c_int),
    SDLFunc("Mix_GetMusicDecoder", [c_int], c_char_p),
    SDLFunc("Mix_HasMusicDecoder", [c_char_p], SDL_bool, added='2.6.0'),
    SDLFunc("Mix_GetMusicType", [_P(Mix_Music)], Mix_MusicType),
    SDLFunc("Mix_GetMusicTitle", [_P(Mix_Music)], c_char_p, added='2.6.0'),
    SDLFunc("Mix_GetMusicTitleTag", [_P(Mix_Music)], c_char_p, added='2.6.0'),
    SDLFunc("Mix_GetMusicArtistTag", [_P(Mix_Music)], c_char_p, added='2.6.0'),
    SDLFunc("Mix_GetMusicAlbumTag", [_P(Mix_Music)], c_char_p, added='2.6.0'),
    SDLFunc("Mix_GetMusicCopyrightTag", [_P(Mix_Music)], c_char_p, added='2.6.0'),
    SDLFunc("Mix_SetPostMix", [mix_func, c_void_p]),
    SDLFunc("Mix_HookMusic", [mix_func, c_void_p]),
    SDLFunc("Mix_HookMusicFinished", [music_finished]),
    SDLFunc("Mix_GetMusicHookData", None, c_void_p),
    SDLFunc("Mix_ChannelFinished", [channel_finished]),
    SDLFunc("Mix_RegisterEffect", [c_int, Mix_EffectFunc_t, Mix_EffectDone_t, c_void_p], c_int),
    SDLFunc("Mix_UnregisterEffect", [c_int, Mix_EffectFunc_t], c_int),
    SDLFunc("Mix_UnregisterAllEffects", [c_int]),
    SDLFunc("Mix_SetPanning", [c_int, Uint8, Uint8], c_int),
    SDLFunc("Mix_SetPosition", [c_int, Sint16, Uint8], c_int),
    SDLFunc("Mix_SetDistance", [c_int, Uint8]),
    SDLFunc("Mix_SetReverseStereo", [c_int, c_int], c_int),
    SDLFunc("Mix_ReserveChannels", [c_int], c_int),
    SDLFunc("Mix_GroupChannel", [c_int, c_int], c_int),
    SDLFunc("Mix_GroupChannels", [c_int, c_int, c_int], c_int),
    SDLFunc("Mix_GroupAvailable", [c_int], c_int),
    SDLFunc("Mix_GroupCount", [c_int], c_int),
    SDLFunc("Mix_GroupOldest", [c_int], c_int),
    SDLFunc("Mix_GroupNewer", [c_int], c_int),
    SDLFunc("Mix_PlayChannel", [c_int, _P(Mix_Chunk), c_int], c_int, added='2.6.0'),
    SDLFunc("Mix_PlayChannelTimed", [c_int, _P(Mix_Chunk), c_int, c_int], c_int),
    SDLFunc("Mix_PlayMusic", [_P(Mix_Music), c_int], c_int),
    SDLFunc("Mix_FadeInMusic", [_P(Mix_Music), c_int, c_int], c_int),
    SDLFunc("Mix_FadeInMusicPos", [_P(Mix_Music), c_int, c_int, c_double], c_int),
    SDLFunc("Mix_FadeInChannel", [c_int, _P(Mix_Chunk), c_int, c_int], c_int, added='2.6.0'),
    SDLFunc("Mix_FadeInChannelTimed", [c_int, _P(Mix_Chunk), c_int, c_int, c_int], c_int),
    SDLFunc("Mix_Volume", [c_int, c_int], c_int),
    SDLFunc("Mix_VolumeChunk", [_P(Mix_Chunk), c_int], c_int),
    SDLFunc("Mix_VolumeMusic", [c_int], c_int),
    SDLFunc("Mix_GetMusicVolume", [_P(Mix_Music)], c_int, added='2.6.0'),
    SDLFunc("Mix_MasterVolume", [c_int], c_int, added='2.6.0'),
    SDLFunc("Mix_HaltChannel", [c_int], c_int),
    SDLFunc("Mix_HaltGroup", [c_int], c_int),
    SDLFunc("Mix_HaltMusic", None, c_int),
    SDLFunc("Mix_ExpireChannel", [c_int, c_int], c_int),
    SDLFunc("Mix_FadeOutChannel", [c_int, c_int], c_int),
    SDLFunc("Mix_FadeOutGroup", [c_int, c_int], c_int),
    SDLFunc("Mix_FadeOutMusic", [c_int], c_int),
    SDLFunc("Mix_FadingMusic", None, Mix_Fading),
    SDLFunc("Mix_FadingChannel", [c_int], Mix_Fading),
    SDLFunc("Mix_Pause", [c_int]),
    SDLFunc("Mix_Resume", [c_int]),
    SDLFunc("Mix_Paused", [c_int], c_int),
    SDLFunc("Mix_PauseMusic"),
    SDLFunc("Mix_ResumeMusic"),
    SDLFunc("Mix_RewindMusic"),
    SDLFunc("Mix_PausedMusic", None, c_int),
    SDLFunc("Mix_ModMusicJumpToOrder", [c_int], c_int, added='2.6.0'),
    SDLFunc("Mix_SetMusicPosition", [c_double], c_int),
    SDLFunc("Mix_GetMusicPosition", [_P(Mix_Music)], c_double, added='2.6.0'),
    SDLFunc("Mix_MusicDuration", [_P(Mix_Music)], c_double, added='2.6.0'),
    SDLFunc("Mix_GetMusicLoopStartTime", [_P(Mix_Music)], c_double, added='2.6.0'),
    SDLFunc("Mix_GetMusicLoopEndTime", [_P(Mix_Music)], c_double, added='2.6.0'),
    SDLFunc("Mix_GetMusicLoopLengthTime", [_P(Mix_Music)], c_double, added='2.6.0'),
    SDLFunc("Mix_Playing", [c_int], c_int),
    SDLFunc("Mix_PlayingMusic", None, c_int),
    SDLFunc("Mix_SetMusicCMD", [c_char_p], c_int),
    SDLFunc("Mix_SetSynchroValue", [c_int], c_int),
    SDLFunc("Mix_GetSynchroValue", None, c_int),
    SDLFunc("Mix_SetSoundFonts", [c_char_p], c_int),
    SDLFunc("Mix_GetSoundFonts", None, c_char_p),
    SDLFunc("Mix_EachSoundFont", [soundfont_function, c_void_p], c_int),
    SDLFunc("Mix_SetTimidityCfg", [c_char_p], c_int, added='2.6.0'),
    SDLFunc("Mix_GetTimidityCfg", None, c_char_p, added='2.6.0'),
    SDLFunc("Mix_GetChunk", [c_int], _P(Mix_Chunk)),
    SDLFunc("Mix_CloseAudio"),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Python wrapper functions

def Mix_Linked_Version():
    """Gets the version of the dynamically-linked **SDL2_mixer** library.

    Returns:
        POINTER(:obj:`SDL_version`): A pointer to a structure containing the
        version of the SDL2_mixer library currently in use.

    """
    return _ctypes.Mix_Linked_Version()

def Mix_Init(flags):
    """Initializes the SDL2_mixer library.
    
    Calling this function enables support for various audio formats as requested
    by the init flags. All other audio file formats can be loaded or used
    regardless of whether this has been called.

    The following init flags are supported:

    ========== =================
    Format     Init flag
    ========== =================
    FLAC       ``MIX_INIT_FLAC``
    MOD        ``MIX_INIT_MID``
    MP3        ``MIX_INIT_MP3``
    MIDI       ``MIX_INIT_MID``
    Ogg Vorbis ``MIX_INIT_OGG``
    Opus       ``MIX_INIT_OPUS``
    ========== =================

    This can be called multiple times to enable support for these formats
    separately, or can initialize multiple formats at once by passing a set of
    flags as a bitwise OR. You can also call this function with 0 as a flag
    to check which audio decoding libraries have already been loaded, or to test
    whether a given decoder is available on the current system::

       # Initialize FLAC and MP3 support separately
       for flag in [MIX_INIT_FLAC, MIX_INIT_MP3]:
           Mix_Init(flag)
           err = Mix_GetError() # check for any errors loading library
           if len(err):
               print(err)

       # Initialize FLAC and MP3 support at the same time
       flags = MIX_INIT_FLAC | MIX_INIT_MP3
       Mix_Init(flags)
       if Mix_Init(0) != flags: # verify both libraries loaded properly
           print(Mix_GetError())

    .. note::
       This function is not guaranteed to set an error string on failure, so
       the return value should be used for error checking instead of just
       :func:`Mix_GetError`.

    Args:
        flags (int): A bitwise OR'd set of the flags of the audio formats to
            load support for.

    Returns:
        int: A bitmask of all the currently initialized audio decoders. 

    """
    return _ctypes["Mix_Init"](flags)

def Mix_Quit():
    """De-initializes the SDL_mixer library.
    
    Calling this function disables support for any formats initialized by
    :func:`Mix_Init` and frees all associated memory. You can re-initialize
    support for those decoders by calling :func:`Mix_Init` again with the
    corresponding init flags.

    You only need to call this function once, no matter how many times
    :func:`Mix_Init` was called.

    """
    return _ctypes["Mix_Quit"]()


def Mix_OpenAudio(frequency, format, channels, chunksize):
    """Opens the default audio output device for use with the mixer API.

    This function opens the default audio device with a given output channel
    count, audio sample format, sample rate, and audio buffer size, and
    initializes the mixer with 8 virtual channels::

       # Initialize a 44.1 kHz 16-bit stereo mixer with a 1024-byte buffer size
       ret = Mix_OpenAudio(44100, sdl2.AUDIO_S16SYS, 2, 1024)
       if ret < 0:
           err = Mix_GetError().decode("utf8")
           raise RuntimeError("Error initializing the mixer: {0}".format(err))

    A sample rate of 44100 Hz (CD quality) or 48000 Hz is recommended for any
    remotely modern computer. The chunk size must be a power of 8 (e.g. 512,
    1024, 2048), and specifies how much audio data to send to the output device
    at a time. Lower values will have lower latencies, but may introduce skips
    in the audio (2048 is a safe default). Supported channel counts are 1
    (mono), 2 (stereo), 4 (quad), and 6 (5.1 surround).

    For a full list of supported audio format flags, see the list of format
    values at the following link: https://wiki.libsdl.org/SDL_AudioSpec

    .. note::
       This should not be called if :func:`SDL_OpenAudio` has already opened the
       default audio device (and vice-versa).
    
    Args:
        frequency (int): The output sampling rate per channel (in Hz).
        format (int): A constant indicating the audio sample format to use
            with the device (e.g. ``sdl2.AUDIO_S16``).
        channels (int): The number of output channels to use for the device 
            (e.g. 2 for stereo, 1 for mono).
        chunksize (int): The size of the audio buffer (in bytes).

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["Mix_OpenAudio"](frequency, format, channels, chunksize)

def Mix_OpenAudioDevice(frequency, format, channels, chunksize, device, allowed_changes):
    """Opens a specific audio output device for use with the mixer API.

    A specific audio device can be opened by name using the output of the
    :func:`SDL_GetAudioDeviceName` function. Alternatively, passing ``None`` as
    the device name will make open the most reasonable default audio device.

    The ``allowed_changes`` flag specifies which output properties (channel
    count, frequency, sample format) are allowed to be be automatically changed
    if not supported by the chosen audio device. See the documentation for
    :func:`SDL_OpenAudioDevice` for the list of supported flags and more info.

    See :func:`Mix_OpenAudio` for more usage details.

    .. note::
       Once an output device has been opened with this function, it should not
       be opened again with :func:`SDL_OpenAudioDevice` (or vice-versa).

    Args:
        frequency (int): The output sampling rate per channel (in Hz).
        format (int): A constant indicating the audio sample format to use
            with the device (e.g. ``sdl2.AUDIO_S16``).
        channels (int): The number of output channels to use for the device 
            (e.g. 2 for stereo, 1 for mono).
        chunksize (int):
        device (bytes): A UTF-8 encoded bytestring of the name of the audio
            output device to open (or ``None`` for the default).
        allowed_changes (int): A bitmask of flags indicating the output
            properties allowed to be automatically changed to support the
            output device. If 0, no changes are allowed.

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["Mix_OpenAudioDevice"](
        frequency, format, channels, chunksize, device, allowed_changes
    )

def Mix_AllocateChannels(numchans):
    """Sets the number of channels to use for the mixer API.
    
    In this context, "channels" refers to the number of virtual channels used by
    the mixer API for playing multiple sounds simultaneously. It does not refer
    to the physical number of channels to use for the output device.
    
    This can be called multiple times, even with sounds playing. If ``numchans``
    is less than the current number of channels, the channels above the new number
    will be stopped, freed, and not mixed any longer. If any channels are
    deallocated, any callback set by  :func:`Mix_ChannelFinished` will be called
    when each channel is halted to be freed.

    If this function is called with a negative number (e.g. ``-1``), it will
    return the number of currently-allocated virtual mixer channels without
    changing anything. If called with 0, all mixer channels will be freed.

    This function has no effect on music playback.

    Args:
        numchans (int): The number of virtual channels to use for the mixer API,
            or a negative number to query the current allocated channel count.
    
    """
    return _ctypes["Mix_AllocateChannels"](numchans)

def Mix_QuerySpec(frequency, format, channels):
    """Retrieves the actual audio format in use by the current mixer device.

    This function returns the calculated info by reference, meaning that
    it needs to be called using pre-allocated ctypes variables::

       from ctypes import c_int, byref

       freq, fmt, chans = c_int(0), c_int(0), c_int(0)
       ret = Mix_QuerySpec(byref(freq), byref(fmt), byref(chans))
       if ret > 0:
           results = [x.value for x in (freq, fmt, chans)]

    The obtained values may or may not match the parameters you passed to
    :func:`Mix_OpenAudio`, depending on the audio configurations supported by
    the output device.

    Args:
        frequency (byref(:obj:`~ctypes.c_int`)): The output sampling rate per
            channel (in Hz).
        format (byref(:obj:`~ctypes.c_int`)): The output format used by the
            output device.
        channels (byref(:obj:`~ctypes.c_int`)): The number of output channels
            used by the device (e.g. 2 for stereo, 1 for mono).

    Returns:
        int: The number of times the mixer device has been opened, or 0 on
        error.

    """
    return _ctypes["Mix_QuerySpec"](frequency, format, channels)


def Mix_LoadWAV_RW(src, freesrc):
    """Loads an audio clip from an SDL2 file object.

    See :func:`Mix_GetChunkDecoder` for a list of supported file types.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used in order to determine the correct output format for playback.

    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid audio clip.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically after being loaded.

    Returns:
        POINTER(:obj:`Mix_Chunk`): A pointer to the chunk containing the loaded
        audio.

    """
    return _ctypes["Mix_LoadWAV_RW"](src, freesrc)

def Mix_LoadWAV(file):
    """Loads an audio clip from a file.

    See :func:`Mix_GetChunkDecoder` for a list of supported file types.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used in order to determine the correct output format for playback.

    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the audio
            clip to load.

    Returns:
        POINTER(:obj:`Mix_Chunk`): A pointer to the chunk containing the loaded
        audio.

    """
    return Mix_LoadWAV_RW(SDL_RWFromFile(file, b"rb"), 1)

def Mix_LoadMUS(file):
    """Loads music from a file.

    See :func:`Mix_GetMusicDecoder` for a list of supported file types.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used in order to determine the correct output format for playback.

    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the music
            file to load.

    Returns:
        POINTER(:obj:`Mix_Music`): A pointer to the object containing the loaded
        music.

    """
    return _ctypes["Mix_LoadMUS"](file)

def Mix_LoadMUS_RW(src, freesrc):
    """Loads music from an SDL2 file object.

    See :func:`Mix_GetMusicDecoder` for a list of supported file types.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used in order to determine the correct output format for playback.

    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid music format.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically after being loaded.

    Returns:
        POINTER(:obj:`Mix_Music`): A pointer to the object containing the loaded
        music.

    """
    return _ctypes["Mix_LoadMUS_RW"](src, freesrc)

def Mix_LoadMUSType_RW(src, type, freesrc):
    """Loads music from an SDL2 file object with a specific decoder.

    This function supports the following audio format constants:

    ================= =================
    Format            Constant
    ================= =================
    None (autodetect) ``MUS_NONE``
    External command  ``MUS_CMD``
    WAVE format       ``MUS_WAV``
    Amiga MOD format  ``MUS_MOD``
    MIDI format       ``MUS_MID``
    Ogg Vorbis        ``MUS_OGG``
    MP3 format        ``MUS_MP3``
    FLAC format       ``MUS_FLAC``
    Opus format       ``MUS_OPUS``
    ================= =================

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used in order to determine the correct output format for playback.

    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid music format.
        type (int): The decoder to use for loading the file object.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically after being loaded.

    Returns:
        POINTER(:obj:`Mix_Music`): A pointer to the object containing the loaded
        music.

    """
    return _ctypes["Mix_LoadMUSType_RW"](src, type, freesrc)

def Mix_QuickLoad_WAV(mem):
    """Loads a memory buffer as a WAV file.

    Unlike :func:`Mix_LoadWAV_RW`, this function performs no audio format
    conversion or error checking, and assumes that the WAV in the buffer is
    already in the correct output format for the mixer. Unless high performance
    is a must, :func:`Mix_LoadWAV_RW` is a more flexible and much safer option.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used.

    Args:
        mem (POINTER(:obj:`~ctypes.c_byte`)): A pointer to a memory buffer
            containing a valid WAVE audio file.

    Returns:
        POINTER(:obj:`Mix_Chunk`): A pointer to the chunk containing the loaded
        audio.

    """
    return _ctypes["Mix_QuickLoad_WAV"](mem)

def Mix_QuickLoad_RAW(mem, len):
    """Loads a memory buffer as a raw audio clip.

    This function performs no error checking and assumes that the data in the
    buffer is in the correct output format for the mixer.
    
    This can be used for converting Numpy arrays or other Python data types
    into audio clips for use with the mixer API. For example, to generate a
    pure sine wave tone at a given frequency, you could use the following code::

       import ctypes
       import numpy as np

       duration = 3      # Seconds of sound
       hz = 432          # Frequency of the generated tone
       dtype = np.int16  # Mixer output format is signed 16-bit int
       max_int = 32767   # The max/min value for a signed 16-bit int
       srate = 44100     # Sample rate for each channel is 44100 kHz
    
       # Generate a 3 sec. sine wave for a 2-channel, 44100 Hz, AUDIO_S16 mixer
       size = int((duration / 1000.0) * srate)
       arr = np.sin(np.pi * np.arange(size) / srate * hz) * max_int

       # Cast the array into ctypes format for use with mixer
       arr_bytes = arr.tostring()
       buflen = len(arr_bytes)
       c_buf = (ctypes.c_ubyte * buflen).from_buffer_copy(arr_bytes)

       # Convert the ctypes memory buffer into a mixer audio clip
       sine_chunk = Mix_QuickLoad_RAW(
           ctypes.cast(c_buf, ctypes.POINTER(ctypes.c_ubyte)), buflen
       )

    .. note::
       You `must` keep a reference to the created ctypes buffer as long as the
       resulting audio clip is in use. Otherwise, Python may automatically free
       the memory associated with the audio buffer, meaning that any subsequent
       attempts to play the clip will result in a segmentation fault.

    .. note::
        :func:`Mix_OpenAudioDevice` must be called before this function can be
        used.

    Args:
        mem (POINTER(:obj:`~ctypes.c_byte`)): A pointer to a memory buffer
            containing audio samples in the current output format.
        len (int): The length (in bytes) of the memory buffer to load.

    Returns:
        POINTER(:obj:`Mix_Chunk`): A pointer to the chunk containing the loaded
        audio.

    """
    return _ctypes["Mix_QuickLoad_RAW"](mem, len)

def Mix_FreeChunk(chunk):
    """Closes and frees the memory associated with a given audio clip.

    This function should be called on a chunk when you are done with it. A
    :obj:`Mix_Chunk` cannot be used after it has been closed.
   
    Args:
        chunk (:obj:`Mix_Chunk`): The chunk object to close.

    """
    return _ctypes["Mix_FreeChunk"](chunk)

def Mix_FreeMusic(music):
    """Closes and frees the memory associated with a given music object.

    This function should be called on a music object when you are done with it.
    A :obj:`Mix_Music` cannot be used after it has been closed.
   
    Args:
        music (:obj:`Mix_Music`): The music object to close.

    """
    return _ctypes["Mix_FreeMusic"](music)


def Mix_GetNumChunkDecoders():
    """Retrieves the number of available audio chunk decoders.
    
    The returned value can differ between runs of a program due to changes in
    the availability of the shared libraries required for supporting different
    formats.

    Returns:
        int: The number of available audio chunk decoders.

    """
    return _ctypes["Mix_GetNumChunkDecoders"]()

def Mix_GetChunkDecoder(index):
    """Retrieves the name of a given audio chunk decoder.
    
    The SDL_mixer library currently supports the following chunk decoders:

    ============  ============================= =============================
    Decoder Name  Format Type                   Notes
    ============  ============================= =============================
    b"FLAC"       Free Lossless Audio Codec
    b"MOD"        Amiga MOD format
    b"MP3"        MP3 format
    b"OGG"        Ogg Vorbis
    b"MID"        MIDI format                   Not always available on Linux
    b"OPUS"       Opus Interactive Audio Codec  Added in SDL_mixer 2.0.4
    b"WAVE"       Waveform Audio File Format
    b"AIFF"       Audio Interchange File Format
    b"VOC"        Creative Voice file
    ============  ============================= =============================

    Use the :func:`Mix_GetNumChunkDecoders` function to get the number of
    available chunk decoders.

    Returns:
        bytes: The name of the given chunk decoder, or ``None`` if the index is
        invalid.

    """
    return _ctypes["Mix_GetChunkDecoder"](index)

def Mix_HasChunkDecoder(name):
    """Checks whether a specific chunk decoder is available.

    See :func:`Mix_GetChunkDecoder` for a list of valid decoder names.

    Args:
        name (bytes): A bytestring of the name of the decoder to query.

    Returns:
        int: 1 if the decoder is present, or 0 if unavailable.

    """
    return _ctypes["Mix_HasChunkDecoder"](name)

def Mix_GetNumMusicDecoders():
    """Retrieves the number of available music decoders.
    
    The returned value can differ between runs of a program due to changes in
    the availability of the shared libraries required for supporting different
    formats.

    Returns:
        int: The number of available music decoders.

    """
    return _ctypes["Mix_GetNumMusicDecoders"]()

def Mix_GetMusicDecoder(index):
    """Retrieves the name of a given music decoder.
    
    The SDL_mixer library currently supports the following music decoders:

    ============= ============================= =============================
    Decoder Name  Format Type                   Notes
    ============= ============================= =============================
    b"FLAC"       Free Lossless Audio Codec
    b"MOD"        Amiga MOD
    b"MP3"        MP3 format
    b"OGG"        Ogg Vorbis
    b"MIDI"       MIDI format                   Not always available on Linux
    b"OPUS"       Opus Interactive Audio Codec  Added in SDL_mixer 2.0.4
    b"CMD         External music command        Not available on Windows
    b"WAVE"       Waveform Audio File Format
    ============= ============================= =============================

    Use the :func:`Mix_GetNumMusicDecoders` function to get the number of
    available chunk decoders.

    Returns:
        bytes: The name of the given music decoder, or ``None`` if the index is
        invalid.

    """
    return _ctypes["Mix_GetMusicDecoder"](index)

def Mix_HasMusicDecoder(name):
    """Checks whether a specific music decoder is available.

    See :func:`Mix_GetMusicDecoder` for a list of valid decoder names.

    Args:
        name (bytes): A bytestring of the name of the decoder to query.

    Returns:
        int: 1 if the decoder is present, or 0 if unavailable.

    """
    return _ctypes["Mix_HasMusicDecoder"](name)

def Mix_GetMusicType(music):
    """Gets the format of a given music object.

    See :func:`Mix_LoadMUSType_RW` for a list of the possible type constants.

    Args:
        music (:obj:`Mix_Music`): The music object for which the type will be
            retrieved.

    Returns:
        int: A constant indicating the format of the music object, or
        ``MUS_NONE`` (0) if the format could not be identified.

    """
    return _ctypes["Mix_GetMusicType"](music)

def Mix_GetMusicTitle(music):
    """Gets the song title for a given music object.

    If a title is not available in the music metadata, the file name will be
    returned instead. If no music is playing, this will return an empty string.

    Args:
        music (:obj:`Mix_Music`): The music object from which to retrieve the
            title.

    Returns:
        bytes: The song title of the music object.

    """
    return _ctypes["Mix_GetMusicTitle"](music)

def Mix_GetMusicTitleTag(music):
    """Gets the song title for a given music object.

    Unlike :func:`Mix_GetMusicTitle`, this function only checks for a title in
    the music metadata and will return an empty string instead of the file name
    if no title tag is present.
    
    If no music is playing, this will return an empty string.

    Args:
        music (:obj:`Mix_Music`): The music object from which to retrieve the
            title.

    Returns:
        bytes: The song title of the music object.

    """
    return _ctypes["Mix_GetMusicTitleTag"](music)

def Mix_GetMusicArtistTag(music):
    """Gets the artist name for a given music object.
    
    If the music metadata has no artist tag or no music is playing, this will
    return an empty string.

    Args:
        music (:obj:`Mix_Music`): The music object from which to retrieve the
            artist.

    Returns:
        bytes: The artist name for the music object.

    """
    return _ctypes["Mix_GetMusicArtistTag"](music)

def Mix_GetMusicAlbumTag(music):
    """Gets the album name for a given music object.
    
    If the music metadata has no album tag or no music is playing, this will
    return an empty string.

    Args:
        music (:obj:`Mix_Music`): The music object from which to retrieve the
            album name.

    Returns:
        bytes: The album name for the music object.

    """
    return _ctypes["Mix_GetMusicAlbumTag"](music)

def Mix_GetMusicCopyrightTag(music):
    """Gets the copyright text for a given music object.
    
    If the music metadata has no copyright tag or no music is playing, this will
    return an empty string.

    Args:
        music (:obj:`Mix_Music`): The music object from which to retrieve the
            copyright text.

    Returns:
        bytes: The copyright text for the music object.

    """
    return _ctypes["Mix_GetMusicCopyrightTag"](music)

def Mix_SetPostMix(mix_func, arg):
    return _ctypes["Mix_SetPostMix"](mix_func, arg)

def Mix_HookMusic(mix_func, arg):
    return _ctypes["Mix_HookMusic"](mix_func, arg)

def Mix_HookMusicFinished(music_finished):
    return _ctypes["Mix_HookMusicFinished"](music_finished)

def Mix_GetMusicHookData():
    return _ctypes["Mix_GetMusicHookData"]()

def Mix_ChannelFinished(channel_finished):
    return _ctypes["Mix_ChannelFinished"](channel_finished)


def Mix_RegisterEffect(chan, f, d, arg):
    return _ctypes["Mix_RegisterEffect"](chan, f, d, arg)

def Mix_UnregisterEffect(channel, f):
    return _ctypes["Mix_UnregisterEffect"](channel, f)

def Mix_UnregisterAllEffects(channel):
    return _ctypes["Mix_UnregisterAllEffects"](channel)


def Mix_SetPanning(channel, left, right):
    return _ctypes["Mix_SetPanning"](channel, left, right)

def Mix_SetPosition(channel, angle, distance):
    return _ctypes["Mix_SetPosition"](channel, angle, distance)

def Mix_SetDistance(channel, distance):
    return _ctypes["Mix_SetDistance"](channel, distance)

def Mix_SetReverseStereo(channel, flip):
    return _ctypes["Mix_SetReverseStereo"](channel, flip)

def Mix_ReserveChannels(num):
    return _ctypes["Mix_ReserveChannels"](num)


def Mix_GroupChannel(which, tag):
    return _ctypes["Mix_GroupChannel"](which, tag)

def Mix_GroupChannels(from_, to, tag):
    return _ctypes["Mix_GroupChannels"](from_, to, tag)

def Mix_GroupAvailable(tag):
    return _ctypes["Mix_GroupAvailable"](tag)

def Mix_GroupCount(tag):
    return _ctypes["Mix_GroupCount"](tag)

def Mix_GroupOldest(tag):
    return _ctypes["Mix_GroupOldest"](tag)

def Mix_GroupNewer(tag):
    return _ctypes["Mix_GroupNewer"](tag)


def Mix_PlayChannelTimed(channel, chunk, loops, ticks):
    """Play an audio chunk on a specific channel for a given duration.

    This function is the same as :func:`Mix_PlayChannel` except that you can
    specify the maximum number of milliseconds for the sound to be played before
    it is halted.

    Args:
        channel (int): The channel on which to play the new chunk.
        chunk (:obj:`Mix_Chunk`): The sound to play.
        loops (int): The number of times the chunk should loop (0 to play once,
            -1 to loop infinitely).
        ticks (int): The maximum number of milliseconds to play the chunk
            on the channel before halting.
    
    Returns:
        int: The index of the channel used to play the sound, or -1 if the sound
        could not be played.

    """
    return _ctypes["Mix_PlayChannelTimed"](channel, chunk, loops, ticks)

def Mix_PlayChannel(channel, chunk, loops):
    """Play an audio chunk on a specific channel.

    If the specified channel is -1, the chunk will be played on the first free
    channel (if no free channel is available, an error is returned).

    If a specific channel was requested and there is a chunk already playing
    there, that chunk will be halted and the new chunk will take its place.

    If ``loops`` is greater than zero, the chunk will loop the specified
    number of times. If ``loops`` is set to -1, the chunk will loop
    "infinitely" (~65000 times).

    Args:
        channel (int): The channel on which to play the new chunk.
        chunk (:obj:`Mix_Chunk`): The sound to play.
        loops (int): The number of times the chunk should loop (0 to play once,
            -1 to loop infinitely).
    
    Returns:
        int: The index of the channel used to play the sound, or -1 if the sound
        could not be played.

    """
    if dll.version_tuple >= (2, 6, 0):
        return _ctypes["Mix_PlayChannel"](channel, chunk, loops)
    else:
        return Mix_PlayChannelTimed(channel, chunk, loops, -1)

def Mix_PlayMusic(music, loops):
    """Play a new music object.

    In SDL_mixer there is only ever one music object playing at a time; if this
    is called while another music object is playing, the previous music will be
    replaced with the new music.

    Please note that if the currently-playing music is in the process of fading
    out (via :func:`Mix_FadeOutMusic`), this function will block until the fade
    completes. If you need to avoid this, be sure to call :func:`Mix_HaltMusic`
    before calling this function.

    Args:
        music (:obj:`Mix_Music`): The new music to play on the music channel.
        loops (int): The number of loops to play the music for (if 0, will only
            play once).

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["Mix_PlayMusic"](music, loops)


def Mix_FadeInMusic(music, loops, ms):
    return _ctypes["Mix_FadeInMusic"](music, loops, ms)

def Mix_FadeInMusicPos(music, loops, ms, position):
    return _ctypes["Mix_FadeInMusicPos"](music, loops, ms, position)

def Mix_FadeInChannelTimed(channel, chunk, loops, ms, ticks):
    return _ctypes["Mix_FadeInChannelTimed"](channel, chunk, loops, ms, ticks)

def Mix_FadeInChannel(channel, chunk, loops, ms):
    if dll.version_tuple >= (2, 6, 0):
        return _ctypes["Mix_FadeInChannel"](channel, chunk, loops, ms)
    else:
        return Mix_FadeInChannelTimed(channel, chunk, loops, ms, -1)


def Mix_Volume(channel, volume):
    return _ctypes["Mix_Volume"](channel, volume)

def Mix_VolumeChunk(chunk, volume):
    return _ctypes["Mix_VolumeChunk"](chunk, volume)

def Mix_VolumeMusic(volume):
    return _ctypes["Mix_VolumeMusic"](volume)

def Mix_GetMusicVolume(music):
    return _ctypes["Mix_GetMusicVolume"](music)

def Mix_MasterVolume(volume):
    return _ctypes["Mix_MasterVolume"](volume)


def Mix_HaltChannel(channel):
    """Halt playback of a particular channel.

    This will stop playback on the specified channel until a new chunk is
    played there. Specifying a channel of -1 will halt `all` non-music channels.

    Any halted channels will have any currently-registered effects deregistered,
    and will call any callback specified by :func:`Mix_ChannelFinished` before
    this function returns.

    Args:
        channel (int): The index of the channel to halt, or -1 to halt all
            channels.

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["Mix_HaltChannel"](channel)

def Mix_HaltGroup(tag):
    return _ctypes["Mix_HaltGroup"](tag)

def Mix_HaltMusic():
    """Halt playback of the music channel.

    This will stop playback on music channel until a new music object is played.

    Halting the music channnel will call any callback set by
    :func:`Mix_HookMusicFinished` before this function returns.

    Returns:
        int: 0, regardless of whether any music was halted.

    """
    return _ctypes["Mix_HaltMusic"]()

def Mix_ExpireChannel(channel, ticks):
    return _ctypes["Mix_ExpireChannel"](channel, ticks)


def Mix_FadeOutChannel(which, ms):
    return _ctypes["Mix_FadeOutChannel"](which, ms)

def Mix_FadeOutGroup(tag, ms):
    return _ctypes["Mix_FadeOutGroup"](tag, ms)

def Mix_FadeOutMusic(ms):
    return _ctypes["Mix_FadeOutMusic"](ms)

def Mix_FadingMusic():
    return _ctypes["Mix_FadingMusic"]()

def Mix_FadingChannel(which):
    return _ctypes["Mix_FadingChannel"](which)


def Mix_Pause(channel):
    """Pauses playback of a given mixer channel.

    This temporarily stops playback on the given channel. When resumed via
    :func:`Mix_Resume`, the channel will continue to play where it left off.

    Playing a new chunk on a channel when the channel is paused  will replace
    the the chunk and unpause the channel.
    
    Args:
        channel (int): The index of the channel to pause (or -1 to pause all
            channels).

    """
    return _ctypes["Mix_Pause"](channel)

def Mix_Resume(channel):
    """Resumes playback of a given mixer channel.

    This will resume playback of the channel if it has been paused. If the
    channel is already playing, this will have no effect.
    
    Args:
        channel (int): The index of the channel to resume (or -1 to resume all
            channels).

    """
    return _ctypes["Mix_Resume"](channel)

def Mix_Paused(channel):
    """Checks whether a given mixer channel is currently paused.

    Args:
        channel (int): The index of the channel to query (or -1 to count the
            total number of paused channels).

    Returns:
        int: 1 if the channel is paused, otherwise 0. Alternatively, if channel
        is ``-1``, returns the number of currently paused mixer channels.

    """
    return _ctypes["Mix_Paused"](channel)

def Mix_PauseMusic():
    """Pauses playback of the music channel.

    This temporarily stops playback on the music channel. When resumed via
    :func:`Mix_ResumeMusic`, the music will continue to play where it left off.
    
    Playing a new music object when the music channel is paused will replace
    the current music and unpause the music stream.

    """
    return _ctypes["Mix_PauseMusic"]()

def Mix_ResumeMusic():
    """Resumes playback of the music channel.

    This will resume playback of the music channel if it has been paused. If
    the music channel is already playing, this will have no effect.

    """
    return _ctypes["Mix_ResumeMusic"]()

def Mix_RewindMusic():
    """Sets the music channel to the beginning of the currently loaded music.

    This can be called regardless of whether music is currently playing.

    """
    return _ctypes["Mix_RewindMusic"]()

def Mix_PausedMusic():
    """Checks whether the music channel is currently paused.

    Returns:
        int: 1 if the music channel is paused, otherwise 0.

    """
    return _ctypes["Mix_PausedMusic"]()


def Mix_ModMusicJumpToOrder(order):
    return _ctypes["Mix_ModMusicJumpToOrder"](order)

def Mix_SetMusicPosition(position):
    return _ctypes["Mix_SetMusicPosition"](position)

def Mix_GetMusicPosition(music):
    return _ctypes["Mix_GetMusicPosition"](music)

def Mix_MusicDuration(music):
    return _ctypes["Mix_MusicDuration"](music)

def Mix_GetMusicLoopStartTime(music):
    return _ctypes["Mix_GetMusicLoopStartTime"](music)

def Mix_GetMusicLoopEndTime(music):
    return _ctypes["Mix_GetMusicLoopEndTime"](music)

def Mix_GetMusicLoopLengthTime(music):
    return _ctypes["Mix_GetMusicLoopLengthTime"](music)

def Mix_Playing(channel):
    """Checks whether a chunk has been loaded into a given channel.

    Note that this will return 1 even if the channel is paused: this only
    checks whether the channel is ready for playback or not. It will return 0
    if no chunk is currently loaded into the channel.

    Args:
        channel (int): The index of the channel to query (or -1 to count the
            total number of playback-ready channels).

    Returns:
        int: 1 if a chunk is loaded in the given channel, otherwise 0.
        Alternatively, if channel is ``-1``, returns the number of mixer
        channels ready for playback.

    """
    return _ctypes["Mix_Playing"](channel)

def Mix_PlayingMusic():
    """Checks whether music has been loaded into the music channel.

    Note that this will return 1 even if the channel is paused: this only
    checks whether the music channel is ready for playback or not. It will
    return 0 if no music is currently loaded into the channel.

    Returns:
        int: 1 if music is loaded in the music channel, otherwise 0.

    """
    return _ctypes["Mix_PlayingMusic"]()

def Mix_SetMusicCMD(command):
    return _ctypes["Mix_SetMusicCMD"](command)


def Mix_SetSynchroValue(value):
    return _ctypes["Mix_SetSynchroValue"](value)

def Mix_GetSynchroValue():
    return _ctypes["Mix_GetSynchroValue"]()

def Mix_SetSoundFonts(paths):
    return _ctypes["Mix_SetSoundFonts"](paths)

def Mix_GetSoundFonts():
    return _ctypes["Mix_GetSoundFonts"]()

def Mix_EachSoundFont(function, data):
    return _ctypes["Mix_EachSoundFont"](function, data)

def Mix_SetTimidityCfg(path):
    return _ctypes["Mix_SetTimidityCfg"](path)

def Mix_GetTimidityCfg():
    return _ctypes["Mix_GetTimidityCfg"]()


def Mix_GetChunk(channel):
    return _ctypes["Mix_GetChunk"](channel)

def Mix_CloseAudio():
    """Shuts down and de-initializes the mixer API.

    Calling this function stops all audio playback and closes the current mixer
    device. Once called, the mixer API should not be used until re-initialized
    with :func:`Mix_OpenAudioDevice`.

    .. note::
       If :func:`Mix_OpenAudioDevice` has been called multiple times, this must
       be called an equal number of times to actually de-initialize the API.

    """
    return _ctypes["Mix_CloseAudio"]()


Mix_SetError = SDL_SetError
Mix_GetError = SDL_GetError
Mix_ClearError = SDL_ClearError
Mix_OutOfMemory = SDL_OutOfMemory
