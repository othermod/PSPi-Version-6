import os
import sys
import pytest
import operator
from ctypes import byref, c_int, c_uint16
import sdl2
from sdl2.stdinc import SDL_TRUE, SDL_FALSE
from sdl2 import SDL_Init, SDL_Quit, rwops, version, audio
if sys.version_info[0] >= 3:
    from functools import reduce

sdlmixer = pytest.importorskip("sdl2.sdlmixer")


# TODO: Add actual tests for most functions (can base off of SDL_Mixer docs)

def _get_sound_path(fmt):
    fname = "soundtest.{0}".format(fmt)
    testdir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(testdir, "resources", fname)

def _has_decoder(decoder):
    decoders = []
    num = sdlmixer.Mix_GetNumChunkDecoders()
    for i in range(0, num):
        name = sdlmixer.Mix_GetChunkDecoder(i)
        decoders.append(name.decode('utf-8'))
    return decoder.upper() in decoders

@pytest.fixture(scope="module")
def with_sdl_mixer():
    # Initialize SDL2 with video and audio subsystems
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    # Initialize SDL_mixer and open an audio device
    flags = (
        sdlmixer.MIX_INIT_FLAC | sdlmixer.MIX_INIT_MOD | sdlmixer.MIX_INIT_MP3 |
        sdlmixer.MIX_INIT_OGG | sdlmixer.MIX_INIT_MID | sdlmixer.MIX_INIT_OPUS
    )
    sdlmixer.Mix_Init(flags)
    ret = sdlmixer.Mix_OpenAudio(48000, sdlmixer.MIX_DEFAULT_FORMAT, 2, 1024)
    assert ret == 0
    yield
    sdlmixer.Mix_CloseAudio()
    sdlmixer.Mix_Quit()
    sdl2.SDL_Quit()

@pytest.fixture
def with_mixchunk(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    chk = sdlmixer.Mix_LoadWAV(fpath.encode("utf-8"))
    err = sdlmixer.Mix_GetError()
    sdlmixer.Mix_ClearError()
    assert isinstance(chk.contents, sdlmixer.Mix_Chunk)
    yield chk
    sdlmixer.Mix_FreeChunk(chk)

@pytest.fixture
def with_music(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    mus = sdlmixer.Mix_LoadMUS(fpath.encode("utf-8"))
    err = sdlmixer.Mix_GetError()
    sdlmixer.Mix_ClearError()
    assert isinstance(mus.contents, sdlmixer.Mix_Music)
    yield mus
    sdlmixer.Mix_FreeMusic(mus)
    

def test_Mix_Linked_Version():
    v = sdlmixer.Mix_Linked_Version()
    assert isinstance(v.contents, version.SDL_version)
    assert v.contents.major == 2
    assert v.contents.minor >= 0
    assert v.contents.patch >= 0
    t = (v.contents.major, v.contents.minor, v.contents.patch)
    assert t >= (2, 0, 0)
    assert t == sdlmixer.dll.version_tuple

@pytest.mark.skipif(sdlmixer.dll.version_tuple < (2, 0, 4), reason="Broken in official binaries")
def test_Mix_InitQuit():
    SDL_Init(sdl2.SDL_INIT_AUDIO)
    supported = []
    libs = {
        'FLAC': sdlmixer.MIX_INIT_FLAC,
        'MOD': sdlmixer.MIX_INIT_MOD,
        'MP3': sdlmixer.MIX_INIT_MP3,
        'OGG': sdlmixer.MIX_INIT_OGG,
        'MID': sdlmixer.MIX_INIT_MID,
        'OPUS': sdlmixer.MIX_INIT_OPUS
    }
    for lib in libs.keys():
        flags = libs[lib]
        ret = sdlmixer.Mix_Init(flags)
        err = sdlmixer.Mix_GetError()
        if ret & flags == flags:
            supported.append(lib)
        sdlmixer.Mix_Quit()
    assert len(supported) # only fail if none supported
    print("Supported formats:")
    print(supported)
    SDL_Quit()

def test_Mix_OpenCloseAudio():
    SDL_Init(sdl2.SDL_INIT_AUDIO)
    sdlmixer.Mix_Init(0)
    ret = sdlmixer.Mix_OpenAudio(22050, sdlmixer.MIX_DEFAULT_FORMAT, 2, 1024)
    assert ret == 0
    sdlmixer.Mix_CloseAudio()
    sdlmixer.Mix_Quit()
    SDL_Quit()

@pytest.mark.skipif(sdlmixer.dll.version < 2002, reason="Added in 2.0.2")
def test_Mix_OpenAudioDevice():
    SDL_Init(sdl2.SDL_INIT_AUDIO)
    sdlmixer.Mix_Init(0)
    # Get names of all audio output devices for current driver
    ndevices = audio.SDL_GetNumAudioDevices(0)
    devices = [audio.SDL_GetAudioDeviceName(i, 0) for i in range(0, ndevices)]
    # Open and close each avaliable output device
    fmt = sdlmixer.MIX_DEFAULT_FORMAT
    flags = audio.SDL_AUDIO_ALLOW_ANY_CHANGE
    for device in devices:
        ret = sdlmixer.Mix_OpenAudioDevice(22050, fmt, 2, 1024, device, flags)
        assert ret == 0
        sdlmixer.Mix_CloseAudio()
    sdlmixer.Mix_Quit()
    SDL_Quit()

def test_Mix_AllocateChannels(with_sdl_mixer):
    # Get number currently allocated
    current = sdlmixer.Mix_AllocateChannels(-1)
    assert current > 0
    # Try allocating a single channel
    sdlmixer.Mix_AllocateChannels(1)
    assert sdlmixer.Mix_AllocateChannels(-1) == 1
    # Reset allocated channels
    sdlmixer.Mix_AllocateChannels(current)

def test_Mix_QuerySpec(with_sdl_mixer):
    freq, channels = c_int(0), c_int(0)
    fmt = c_uint16(0)
    ret = sdlmixer.Mix_QuerySpec(byref(freq), byref(fmt), byref(channels))
    assert ret != 0
    assert freq.value > 0 
    assert channels.value > 0
    assert fmt.value in audio.AUDIO_FORMATS

def test_Mix_LoadFreeWAV(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    chk = sdlmixer.Mix_LoadWAV(fpath.encode("utf-8"))
    assert isinstance(chk.contents, sdlmixer.Mix_Chunk)
    assert sdlmixer.Mix_GetError() == b""
    sdlmixer.Mix_FreeChunk(chk)

def test_Mix_LoadWAV_RW(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    rw = sdl2.SDL_RWFromFile(fpath.encode("utf-8"), b"r")
    chk = sdlmixer.Mix_LoadWAV_RW(rw, 1)
    assert isinstance(chk.contents, sdlmixer.Mix_Chunk)
    assert sdlmixer.Mix_GetError() == b""
    sdlmixer.Mix_FreeChunk(chk)

def test_Mix_LoadFreeMUS(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    mus = sdlmixer.Mix_LoadMUS(fpath.encode("utf-8"))
    assert isinstance(mus.contents, sdlmixer.Mix_Music)
    assert sdlmixer.Mix_GetError() == b""
    sdlmixer.Mix_FreeMusic(mus)

def test_Mix_LoadMUS_RW(with_sdl_mixer):
    if not _has_decoder("mp3"):
        pytest.skip("No MP3 decoder available for SDL_mixer")
    fpath = _get_sound_path("mp3")
    rw = sdl2.SDL_RWFromFile(fpath.encode("utf-8"), b"r")
    mus = sdlmixer.Mix_LoadMUS_RW(rw, 1)
    assert isinstance(mus.contents, sdlmixer.Mix_Music)
    assert sdlmixer.Mix_GetError() == b""
    sdlmixer.Mix_FreeMusic(mus)

@pytest.mark.skip("not implemented")
def test_Mix_LoadMUSType_RW(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_QuickLoad_WAV(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_QuickLoad_RAW(with_sdl_mixer):
    pass

def test_Mix_ChunkDecoders(with_sdl_mixer):
    decoders = []
    num = sdlmixer.Mix_GetNumChunkDecoders()
    assert num > 0
    for i in range(0, num):
        name = sdlmixer.Mix_GetChunkDecoder(i)
        assert name is not None
        decoders.append(name.decode('utf-8'))
    print("Available MixChunk decoders:\n{0}".format(str(decoders)))

@pytest.mark.skipif(sdlmixer.dll.version < 2002, reason="Added in 2.0.2")
def test_Mix_HasChunkDecoder(with_sdl_mixer):
    num = sdlmixer.Mix_GetNumChunkDecoders()
    assert num > 0
    for i in range(0, num):
        name = sdlmixer.Mix_GetChunkDecoder(i)
        assert name is not None
        assert sdlmixer.Mix_HasChunkDecoder(name) == SDL_TRUE
    assert sdlmixer.Mix_HasChunkDecoder(b'blah') == SDL_FALSE

def test_Mix_MusicDecoders(with_sdl_mixer):
    decoders = []
    num = sdlmixer.Mix_GetNumMusicDecoders()
    assert num > 0
    for i in range(0, num):
        name = sdlmixer.Mix_GetMusicDecoder(i)
        assert name is not None
        decoders.append(name.decode('utf-8'))
    print("Available MixMusic decoders:\n{0}".format(str(decoders)))

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_HasMusicDecoder(with_sdl_mixer):
    num = sdlmixer.Mix_GetNumMusicDecoders()
    assert num > 0
    for i in range(0, num):
        name = sdlmixer.Mix_GetMusicDecoder(i)
        assert name is not None
        assert sdlmixer.Mix_HasMusicDecoder(name) == SDL_TRUE
    assert sdlmixer.Mix_HasMusicDecoder(b'blah') == SDL_FALSE

def test_Mix_GetMusicType(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicType(mus) == sdlmixer.MUS_MP3

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_GetMusicTitle(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicTitle(mus) == b"Hop"

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_GetMusicTitleTag(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicTitleTag(mus) == b"Hop"

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_GetMusicArtistTag(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicArtistTag(mus) == b"OwlishMedia"

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_GetMusicAlbumTag(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicAlbumTag(mus) == b"8-bit Sound Effect Pack"

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_GetMusicCopyrightTag(with_music):
    mus = with_music
    assert sdlmixer.Mix_GetMusicCopyrightTag(mus) == b"2018 CC0"

@pytest.mark.skip("not implemented")
def test_Mix_SetPostMix(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_HookMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_HookMusicFinished(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicHookData(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_ChannelFinished(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_RegisterEffect(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_UnregisterEffect(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_UnregisterAllEffects(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetPanning(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetPosition(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetDistance(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetReverseStereo(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_ReserveChannels(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupChannels(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupAvailable(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupCount(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupOldest(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GroupNewer(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PlayChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PlayChannelTimed(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PlayMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeInMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeInMusicPos(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeInChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeInChannelTimed(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_Volume(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_VolumeChunk(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_VolumeMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicVolume(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_MasterVolume(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_HaltChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_HaltGroup(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_HaltMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_ExpireChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeOutChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeOutGroup(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadeOutMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadingMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_FadingChannel(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_Pause(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_Resume(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_Paused(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PauseMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_ResumeMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_RewindMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PausedMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_ModMusicJumpToOrder(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetMusicPosition(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicPosition(with_sdl_mixer):
    pass

@pytest.mark.skipif(sdlmixer.dll.version < 2060, reason="Added in 2.6.0")
def test_Mix_MusicDuration(with_music):
    mus = with_music
    duration = sdlmixer.Mix_MusicDuration(mus)
    assert duration != 0
    # NOTE: Actually about 0.15s, but the dr_mp3 backend in SDL_mixer
    # reports it as just over 0.2s
    assert 0.14 < duration < 0.21

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicLoopStartTime(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicLoopEndTime(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetMusicLoopLengthTime(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_Playing(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_PlayingMusic(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetMusicCMD(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetSynchroValue(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetSynchroValue(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetSoundFonts(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetSoundFonts(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_EachSoundFont(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_SetTimidityCfg(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetTimidityCfg(with_sdl_mixer):
    pass

@pytest.mark.skip("not implemented")
def test_Mix_GetChunk(with_sdl_mixer):
    pass
