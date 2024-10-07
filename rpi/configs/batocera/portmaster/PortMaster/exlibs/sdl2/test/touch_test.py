import pytest
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_QuitSubSystem
from sdl2.error import SDL_GetError, SDL_ClearError


# Check if we have any touch devices before running tests
devices = 0
sdl2.SDL_SetHint(sdl2.SDL_HINT_MOUSE_TOUCH_EVENTS, b"1")
ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
if ret == 0:
    devices = sdl2.SDL_GetNumTouchDevices()
SDL_Quit()

# Override the global fixture to enable trackpads as touch devices
@pytest.fixture(scope="module", autouse=True)
def with_sdl():
    sdl2.SDL_SetHint(sdl2.SDL_HINT_MOUSE_TOUCH_EVENTS, b"1")
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    yield
    sdl2.SDL_Quit()


def test_SDL_GetNumTouchDevices():
    assert sdl2.SDL_GetNumTouchDevices() >= 0

@pytest.mark.skipif(devices == 0, reason="No available touch devices")
def test_SDL_GetTouchDevice():
    count = sdl2.SDL_GetNumTouchDevices()
    for i in range(count):
        dev_id = sdl2.SDL_GetTouchDevice(i)
        assert SDL_GetError() == b""
        assert dev_id != 0

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
@pytest.mark.skipif(devices == 0, reason="No available touch devices")
def test_SDL_GetTouchName(with_sdl):
    count = sdl2.SDL_GetNumTouchDevices()
    for i in range(count):
        name = sdl2.SDL_GetTouchName(i)
        assert SDL_GetError() == b""
        assert len(name) > 0

@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
@pytest.mark.skipif(devices == 0, reason="No available touch devices")
def test_SDL_GetTouchDeviceType():
    types = [
        sdl2.SDL_TOUCH_DEVICE_INVALID, sdl2.SDL_TOUCH_DEVICE_DIRECT,
        sdl2.SDL_TOUCH_DEVICE_INDIRECT_ABSOLUTE,
        sdl2.SDL_TOUCH_DEVICE_INDIRECT_RELATIVE
    ]
    count = sdl2.SDL_GetNumTouchDevices()
    for i in range(count):
        dev_id = sdl2.SDL_GetTouchDevice(i)
        assert SDL_GetError() == b""
        assert dev_id != 0
        dev_type = sdl2.SDL_GetTouchDeviceType(dev_id)
        assert dev_type in types

@pytest.mark.skipif(devices == 0, reason="No available touch devices")
def test_SDL_GetNumTouchFingers():
    count = sdl2.SDL_GetNumTouchDevices()
    for i in range(count):
        dev_id = sdl2.SDL_GetTouchDevice(i)
        assert SDL_GetError() == b""
        assert dev_id != 0
        fingers = sdl2.SDL_GetNumTouchFingers(dev_id)
        assert SDL_GetError() == b""
        assert fingers >= 0

@pytest.mark.skipif(devices == 0, reason="No available touch devices")
def test_SDL_GetTouchFinger():
    count = sdl2.SDL_GetNumTouchDevices()
    for i in range(count):
        dev_id = sdl2.SDL_GetTouchDevice(i)
        assert SDL_GetError() == b""
        assert dev_id != 0
        fingers = sdl2.SDL_GetNumTouchFingers(dev_id)
        assert fingers >= 0
        for f in range(0, fingers):
            finger = sdl2.SDL_GetTouchFinger(dev_id, f)
            assert isinstance(finger.contents, sdl2.SDL_Finger)
            assert finger.contents.id >= 0
            assert 0 <= finger.contents.x <= 1
            assert 0 <= finger.contents.y <= 1
                