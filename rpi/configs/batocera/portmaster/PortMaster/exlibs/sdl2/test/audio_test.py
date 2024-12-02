import os
import sys
import ctypes
import pytest
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_InitSubSystem, SDL_QuitSubSystem, \
    SDL_INIT_AUDIO
from sdl2.audio import FORMAT_NAME_MAP
from sdl2.error import SDL_GetError, SDL_ClearError

# NOTE: This module is missing a lot of tests, but is also going to be tricky
# to write more tests for.

# Get original audio driver, if one was set in the environment
original_driver = os.getenv("SDL_AUDIODRIVER", None)

@pytest.fixture
def with_sdl_audio():
    # Reset original audio driver in the environment (if there was one)
    if original_driver:
        os.environ["SDL_AUDIODRIVER"] = original_driver
    # Initialize SDL2 with video and audio subsystems
    sdl2.SDL_Quit()
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    yield
    sdl2.SDL_Quit()
    # Reset original audio driver in environment
    os.environ.pop("SDL_AUDIODRIVER", None)
    if original_driver:
        os.environ["SDL_AUDIODRIVER"] = original_driver

@pytest.fixture
def with_default_driver(with_sdl_audio):
    driver = sdl2.SDL_GetCurrentAudioDriver()
    if driver == None or sdl2.SDL_GetNumAudioDevices(False) == 0:
        sdl2.SDL_QuitSubSystem(SDL_INIT_AUDIO)
        os.environ["SDL_AUDIODRIVER"] = b'dummy'
        sdl2.SDL_InitSubSystem(SDL_INIT_AUDIO)
        driver = sdl2.SDL_GetCurrentAudioDriver()
    yield driver

def _get_audio_drivers():
    drivers = []
    for index in range(sdl2.SDL_GetNumAudioDrivers()):
        name = sdl2.SDL_GetAudioDriver(index)
        drivers.append(name.decode('utf-8'))
    return drivers


# Test macro functions

def test_SDL_AUDIO_BITSIZE():
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_U8) == 8
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S8) == 8
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_U16LSB) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S16LSB) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_U16MSB) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S16MSB) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_U16) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S16) == 16
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S32LSB) == 32
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S32MSB) == 32
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_S32) == 32
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_F32LSB) == 32
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_F32MSB) == 32
    assert sdl2.SDL_AUDIO_BITSIZE(sdl2.AUDIO_F32) == 32

def test_SDL_AUDIO_ISFLOAT():
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_U8)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S8)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_U16LSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S16LSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_U16MSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S16MSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_U16)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S16)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S32LSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S32MSB)
    assert not sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_S32)
    assert sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_F32LSB)
    assert sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_F32MSB)
    assert sdl2.SDL_AUDIO_ISFLOAT(sdl2.AUDIO_F32)

def test_SDL_AUDIO_ISBIGENDIAN():
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_U8)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S8)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_U16LSB)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S16LSB)
    assert sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_U16MSB)
    assert sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S16MSB)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_U16)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S16)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S32LSB)
    assert sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S32MSB)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_S32)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_F32LSB)
    assert sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_F32MSB)
    assert not sdl2.SDL_AUDIO_ISBIGENDIAN(sdl2.AUDIO_F32)

def test_SDL_AUDIO_ISSIGNED():
    assert not sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_U8)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S8)
    assert not sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_U16LSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S16LSB)
    assert not sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_U16MSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S16MSB)
    assert not sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_U16)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S16)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S32LSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S32MSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_S32)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_F32LSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_F32MSB)
    assert sdl2.SDL_AUDIO_ISSIGNED(sdl2.AUDIO_F32)

def test_SDL_AUDIO_ISINT():
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_U8)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S8)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_U16LSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S16LSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_U16MSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S16MSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_U16)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S16)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S32LSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S32MSB)
    assert sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_S32)
    assert not sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_F32LSB)
    assert not sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_F32MSB)
    assert not sdl2.SDL_AUDIO_ISINT(sdl2.AUDIO_F32)

def test_SDL_AUDIO_ISLITTLEENDIAN():
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_U8)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S8)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_U16LSB)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S16LSB)
    assert not sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_U16MSB)
    assert not sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S16MSB)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_U16)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S16)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S32LSB)
    assert not sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S32MSB)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_S32)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_F32LSB)
    assert not sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_F32MSB)
    assert sdl2.SDL_AUDIO_ISLITTLEENDIAN(sdl2.AUDIO_F32)

def test_SDL_AUDIO_ISUNSIGNED():
    assert sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_U8)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S8)
    assert sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_U16LSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S16LSB)
    assert sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_U16MSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S16MSB)
    assert sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_U16)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S16)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S32LSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S32MSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_S32)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_F32LSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_F32MSB)
    assert not sdl2.SDL_AUDIO_ISUNSIGNED(sdl2.AUDIO_F32)


# Test structs and objects

@pytest.mark.skip("not implemented")
def test_SDL_AudioSpec():
    pass

@pytest.mark.skip("not implemented")
def test_SDL_AudioCVT():
    pass

@pytest.mark.skip("not implemented")
def test_SDL_AudioStream():
    pass


# Test actual function bindings

@pytest.mark.skip("not implemented")
def test_SDL_AudioInitQuit():
    pass

def test_SDL_GetNumAudioDrivers(with_sdl_audio):
    count = sdl2.SDL_GetNumAudioDrivers()
    assert count >= 1

def test_SDL_GetAudioDriver(with_sdl_audio):
    founddummy = False
    drivercount = sdl2.SDL_GetNumAudioDrivers()
    for index in range(drivercount):
        drivername = sdl2.SDL_GetAudioDriver(index)
        assert isinstance(drivername, (str, bytes))
        if drivername == b"dummy":
            founddummy = True
    assert founddummy

def test_SDL_GetCurrentAudioDriver(with_sdl_audio):
    success = 0
    # Reset audio subsystem
    SDL_Quit()
    SDL_Init(0)
    for index in range(sdl2.SDL_GetNumAudioDrivers()):
        drivername = sdl2.SDL_GetAudioDriver(index)
        os.environ["SDL_AUDIODRIVER"] = drivername.decode("utf-8")
        # Certain drivers fail without bringing up the correct
        # return value, such as the esd, if it is not running.
        SDL_InitSubSystem(SDL_INIT_AUDIO)
        driver = sdl2.SDL_GetCurrentAudioDriver()
        SDL_QuitSubSystem(SDL_INIT_AUDIO)
        # Do not handle wrong return values.
        if driver is not None:
            assert drivername == driver
            success += 1
    assert success >= 1

def test_SDL_OpenCloseAudio(with_sdl_audio):
    # TODO: Add test that checks which audio formats are supported for each
    # audio device?
    fmt = sdl2.AUDIO_F32 if sys.platform == "darwin" else sdl2.AUDIO_U16
    reqspec = sdl2.SDL_AudioSpec(44100, fmt, 2, 1024)
    spec = sdl2.SDL_AudioSpec(0, 0, 0, 0)
    ret = sdl2.SDL_OpenAudio(reqspec, ctypes.byref(spec))
    assert ret == 0
    assert spec.format > 0  # Can't guarantee we'll get requested format
    assert spec.freq == reqspec.freq
    assert spec.channels == reqspec.channels
    sdl2.SDL_CloseAudio()

def test_SDL_GetNumAudioDevices(with_sdl_audio):
    outnum = sdl2.SDL_GetNumAudioDevices(False)
    assert outnum >= 1
    innum = sdl2.SDL_GetNumAudioDevices(True)
    assert innum >= 0

def test_SDL_GetAudioDeviceName(with_sdl_audio):
    # NOTE: Check & print errors for drivers that failed to load?
    backends = []
    devices = {}
    # Reset audio subsystem
    SDL_Quit()
    SDL_Init(0)
    for drivername in _get_audio_drivers():
        # Get input/output device names for each audio driver
        backends.append(drivername)
        os.environ["SDL_AUDIODRIVER"] = drivername
        # Need to reinitialize subsystem for each driver
        SDL_InitSubSystem(SDL_INIT_AUDIO)
        driver = sdl2.SDL_GetCurrentAudioDriver()
        if driver is not None:
            driver = driver.decode("utf-8")
            devices[driver] = {'input': [], 'output': []}
            outnum = sdl2.SDL_GetNumAudioDevices(False)
            innum = sdl2.SDL_GetNumAudioDevices(True)
            for x in range(outnum):
                name = sdl2.SDL_GetAudioDeviceName(x, False)
                assert name is not None
                devices[driver]['output'].append(name.decode('utf-8'))
            for x in range(innum):
                name = sdl2.SDL_GetAudioDeviceName(x, True)
                assert name is not None
                devices[driver]['input'].append(name.decode('utf-8'))
        SDL_QuitSubSystem(SDL_INIT_AUDIO)
    print("Audio backends supported by current SDL2 binary:")
    print(backends)
    print("\nAvailable audio drivers and devices:")
    for driver in devices.keys():
        print(driver)
        print(" - input: {0}".format(str(devices[driver]['input'])))
        print(" - output: {0}".format(str(devices[driver]['output'])))

@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_GetAudioDeviceSpec(with_default_driver):
    driver = with_default_driver
    drivername = driver.decode('utf-8')
    # Get name and spec of first output device
    outspec = sdl2.SDL_AudioSpec(0, 0, 0, 0)
    outname = sdl2.SDL_GetAudioDeviceName(0, False).decode('utf-8')
    ret = sdl2.SDL_GetAudioDeviceSpec(0, False, ctypes.byref(outspec))
    assert ret == 0
    # Validate frequency and channel count were set
    hz = outspec.freq
    fmt = FORMAT_NAME_MAP[outspec.format] if outspec.format > 0 else 'unknown'
    chans = outspec.channels
    bufsize = outspec.samples if outspec.samples > 0 else 'unknown'
    if driver != b"dummy":
        assert hz > 0
        assert chans > 0
        # Print out device spec info
        msg = "Audio device spec for {0} with '{1}' driver:"
        msg2 = "{0} Hz, {1} channels, {2} format, {3} sample buffer size"
        print(msg.format(outname, drivername))
        print(msg2.format(hz, chans, fmt, bufsize))

@pytest.mark.skipif(sdl2.dll.version < 2240, reason="not available")
def test_SDL_GetDefaultAudioInfo(with_default_driver):
    driver = with_default_driver
    drivername = driver.decode('utf-8')
    # Get name and spec of first output device
    outspec = sdl2.SDL_AudioSpec(0, 0, 0, 0)
    outname = ctypes.c_char_p()
    ret = sdl2.SDL_GetDefaultAudioInfo(ctypes.byref(outname), ctypes.byref(outspec), 0)
    # If method isn't implemented for the current back end, just skip
    if ret < 0 and b"not supported" in sdl2.SDL_GetError():
        pytest.skip("not supported by driver")
    assert ret == 0
    # Validate frequency and channel count were set
    hz = outspec.freq
    fmt = FORMAT_NAME_MAP[outspec.format] if outspec.format > 0 else 'unknown'
    chans = outspec.channels
    bufsize = outspec.samples if outspec.samples > 0 else 'unknown'
    assert hz > 0
    assert chans > 0
    # Print out device spec info
    outname = outname.value.decode('utf-8')
    msg = "Default audio spec for {0} with '{1}' driver:"
    msg2 = "{0} Hz, {1} channels, {2} format, {3} sample buffer size"
    print(msg.format(outname, drivername))
    print(msg2.format(hz, chans, fmt, bufsize))

def test_SDL_OpenCloseAudioDevice(with_sdl_audio):
    #TODO: Add tests for callback
    fmt = sdl2.AUDIO_F32 if sys.platform == "darwin" else sdl2.AUDIO_U16
    reqspec = sdl2.SDL_AudioSpec(44100, fmt, 2, 1024)
    outnum = sdl2.SDL_GetNumAudioDevices(0)
    for x in range(outnum):
        spec = sdl2.SDL_AudioSpec(0, 0, 0, 0)
        name = sdl2.SDL_GetAudioDeviceName(x, 0)
        assert name is not None
        deviceid = sdl2.SDL_OpenAudioDevice(
            name, 0, reqspec, ctypes.byref(spec),
            sdl2.SDL_AUDIO_ALLOW_ANY_CHANGE
        )
        err = SDL_GetError()
        assert deviceid >= 2
        assert isinstance(spec, sdl2.SDL_AudioSpec)
        assert spec.format in sdl2.AUDIO_FORMATS
        assert spec.freq > 0
        assert spec.channels > 0
        assert spec.samples > 0
        sdl2.SDL_CloseAudioDevice(deviceid)

@pytest.mark.skip("not implemented")
def test_SDL_GetAudioStatus(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_GetAudioDeviceStatus(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_PauseAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_PauseAudioDevice(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_LoadWAV_RW(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_LoadWAV(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_FreeWAV(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_BuildAudioCVT(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_ConvertAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_MixAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_MixAudioFormat(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_LockUnlockAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_LockUnlockAudioDevice(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_QueueAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_GetQueuedAudioSize(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_ClearQueuedAudio(self):
    pass

@pytest.mark.skip("not implemented")
def test_SDL_DequeueAudio(self):
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_NewAudioStream():
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_AudioStreamPut():
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_AudioStreamGet():
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_AudioStreamAvailable():
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_AudioStreamClear():
    pass

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_FreeAudioStream():
    pass
