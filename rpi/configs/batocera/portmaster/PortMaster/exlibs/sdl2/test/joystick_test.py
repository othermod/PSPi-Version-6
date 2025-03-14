import sys
import pytest
from ctypes import create_string_buffer, byref, c_int, c_int16, c_uint16, CFUNCTYPE
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_JOYSTICK
from sdl2.events import SDL_QUERY, SDL_ENABLE, SDL_IGNORE
from sdl2.stdinc import SDL_TRUE, SDL_FALSE
from sdl2.error import SDL_GetError, SDL_ClearError

# Get status of joystick support/availability before running tests
any_joysticks = False
SDL_ClearError()
ret = SDL_Init(SDL_INIT_JOYSTICK)
joystick_works = ret == 0 and SDL_GetError() == b""
if joystick_works:
    devices = sdl2.SDL_NumJoysticks()
    if sdl2.dll.version >= 2014:
        # On 2.0.14 and above, we can test with a virtual joystick
        devices += 1
    any_joysticks = devices > 0
SDL_Quit()

pytestmark = pytest.mark.skipif(not joystick_works, reason="system unsupported")

joystick_types = [
    sdl2.SDL_JOYSTICK_TYPE_UNKNOWN,
    sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER,
    sdl2.SDL_JOYSTICK_TYPE_WHEEL,
    sdl2.SDL_JOYSTICK_TYPE_ARCADE_STICK,
    sdl2.SDL_JOYSTICK_TYPE_FLIGHT_STICK,
    sdl2.SDL_JOYSTICK_TYPE_DANCE_PAD,
    sdl2.SDL_JOYSTICK_TYPE_GUITAR,
    sdl2.SDL_JOYSTICK_TYPE_DRUM_KIT,
    sdl2.SDL_JOYSTICK_TYPE_ARCADE_PAD,
    sdl2.SDL_JOYSTICK_TYPE_THROTTLE,
]


# Overrides global fixture with one that initializes the joystick system
@pytest.fixture(scope="module")
def with_sdl():
    sdl2.SDL_ClearError()
    sdl2.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    # Also initialize a virtual joystick (if supported)
    if sdl2.dll.version >= 2014:
        virt_type = sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER
        virt_index = sdl2.SDL_JoystickAttachVirtual(virt_type, 2, 4, 1)
    yield
    sdl2.SDL_Quit()

@pytest.fixture()
def joysticks(with_sdl):
    devices = []
    count = sdl2.SDL_NumJoysticks()
    for i in range(count):
        stick = sdl2.SDL_JoystickOpen(i)
        assert sdl2.SDL_GetError() == b""
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        devices.append(stick)
    yield devices
    for stick in devices:
        sdl2.SDL_JoystickClose(stick)

def is_virtual(stick):
    virtual = False
    if isinstance(stick, int):
        if sdl2.dll.version >= 2014:
            virtual = sdl2.SDL_JoystickIsVirtual(stick) == SDL_TRUE
    elif isinstance(stick.contents, sdl2.SDL_Joystick):
        name = sdl2.SDL_JoystickName(stick)
        virtual = b"Virtual " in name
    return virtual


# TODO: Make one of the tests gather/print out current joystick info

def test_SDL_NumJoysticks():
    if SDL_Init(SDL_INIT_JOYSTICK) != 0:
        pytest.skip("joystick subsystem not supported")
    retval = sdl2.SDL_NumJoysticks()
    SDL_Quit()
    assert retval >= 0

@pytest.mark.skipif(sdl2.dll.version < 2007, reason="not available")
def test_SDL_LockUnlockJoysticks(with_sdl):
    # NOTE: Not sure how to test these more comprehensively
    sdl2.SDL_LockJoysticks()
    sdl2.SDL_UnlockJoysticks()

def test_SDL_JoystickNameForIndex(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        name = sdl2.SDL_JoystickNameForIndex(index)
        assert type(name) in (str, bytes)

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_JoystickPathForIndex(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        path = sdl2.SDL_JoystickPathForIndex(index)
        assert path == None or type(path) in (str, bytes)

@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_JoystickGetDevicePlayerIndex(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        player = sdl2.SDL_JoystickGetDevicePlayerIndex(index)
        assert player in [-1, 0, 1, 2, 3]

def test_SDL_JoystickGetDeviceGUID(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        guid = sdl2.SDL_JoystickGetDeviceGUID(index)
        assert isinstance(guid, sdl2.SDL_JoystickGUID)
        guidlist = list(guid.data)
        assert isinstance(guidlist[0], int)

def test_SDL_JoystickGetDeviceVendor(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        vid = sdl2.SDL_JoystickGetDeviceVendor(index)
        assert SDL_GetError() == b""
        if not is_virtual(index):
            assert vid > 0

def test_SDL_JoystickGetDeviceProduct(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        pid = sdl2.SDL_JoystickGetDeviceProduct(index)
        assert SDL_GetError() == b""
        if not is_virtual(index):
            assert pid > 0

def test_SDL_JoystickGetDeviceProductVersion(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        pver = sdl2.SDL_JoystickGetDeviceProductVersion(index)
        assert SDL_GetError() == b""
        assert pver >= 0

def test_SDL_JoystickGetDeviceType(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        jtype = sdl2.SDL_JoystickGetDeviceType(index)
        assert SDL_GetError() == b""
        assert jtype in joystick_types
        if is_virtual(index):
            assert jtype == sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER

@pytest.mark.skipif(sdl2.dll.version < 2006, reason="not available")
def test_SDL_JoystickGetDeviceInstanceID(joysticks):
    for index in range(len(joysticks)):
        iid = sdl2.SDL_JoystickGetDeviceInstanceID(index)
        assert SDL_GetError() == b""
        stick = joysticks[index]
        assert iid == sdl2.SDL_JoystickInstanceID(stick)

def test_SDL_JoystickOpenClose(with_sdl):
    count = sdl2.SDL_NumJoysticks()
    for index in range(count):
        stick = sdl2.SDL_JoystickOpen(index)
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        sdl2.SDL_JoystickClose(stick)

def test_SDL_JoystickFromInstanceID(joysticks):
    for stick in joysticks:
        iid = sdl2.SDL_JoystickInstanceID(stick)
        assert iid >= 0
        stick2 = sdl2.SDL_JoystickFromInstanceID(iid)
        name = sdl2.SDL_JoystickName(stick)
        assert sdl2.SDL_JoystickName(stick2) == name

@pytest.mark.skipif(sdl2.dll.version < 2012, reason="not available")
def test_SDL_JoystickFromPlayerIndex(joysticks):
    i = 0
    for stick in joysticks:
        sdl2.SDL_JoystickSetPlayerIndex(stick, i)
        stick2 = sdl2.SDL_JoystickFromPlayerIndex(i)
        name = sdl2.SDL_JoystickName(stick)
        assert sdl2.SDL_JoystickName(stick2) == name
        i += 1

@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_JoystickVirtual(with_sdl):
    jcount = sdl2.SDL_NumJoysticks()
    jtype = sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER
    index = sdl2.SDL_JoystickAttachVirtual(jtype, 1, 2, 1)
    assert index >= 0
    assert sdl2.SDL_JoystickIsVirtual(index) == SDL_TRUE
    assert sdl2.SDL_NumJoysticks() == (jcount + 1)
    stick = sdl2.SDL_JoystickOpen(index)

    # Test joystick configuration
    assert sdl2.SDL_JoystickNumAxes(stick) == 1
    assert sdl2.SDL_JoystickNumButtons(stick) == 2
    assert sdl2.SDL_JoystickNumHats(stick) == 1

    # Try setting and checking for some virtual values
    assert sdl2.SDL_JoystickSetVirtualAxis(stick, 0, 512) == 0
    assert sdl2.SDL_JoystickSetVirtualButton(stick, 0, 1) == 0
    assert sdl2.SDL_JoystickSetVirtualButton(stick, 1, 1) == 0
    assert sdl2.SDL_JoystickSetVirtualHat(stick, 0, sdl2.SDL_HAT_UP) == 0
    sdl2.SDL_JoystickUpdate()
    assert sdl2.SDL_JoystickGetAxis(stick, 0) == 512
    assert sdl2.SDL_JoystickGetButton(stick, 0) == 1
    assert sdl2.SDL_JoystickGetButton(stick, 1) == 1
    assert sdl2.SDL_JoystickGetHat(stick, 0) == sdl2.SDL_HAT_UP

    # Check that removing the virtual joystick works properly
    sdl2.SDL_JoystickClose(stick)
    jcount = sdl2.SDL_NumJoysticks()
    assert sdl2.SDL_JoystickDetachVirtual(index) == 0
    assert sdl2.SDL_NumJoysticks() == (jcount - 1)

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_JoystickAttachVirtualEx(with_sdl):
    # Initialize the custom virtual controller description
    virt = sdl2.SDL_VirtualJoystickDesc()
    virt.version = sdl2.SDL_VIRTUAL_JOYSTICK_DESC_VERSION
    virt.type = sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER
    virt.naxes = 4
    virt.nbuttons = 8
    virt.nhats = 1
    virt.name = b"PySDL2 Virtual Controller"

    # Define some custom functions for the virtual controller
    led_value = [0, 0, 0]
    rumble = [0, 0]

    def set_led(userdata, r, g, b):
        led_value[0] = r
        led_value[1] = g
        led_value[2] = b
        return 0

    def set_rumble(userdata, a, b):
        rumble[0] = a
        rumble[1] = b
        return 0

    virt.SetLED = sdl2.joystick.CFUNC_SetLED(set_led)
    virt.Rumble = sdl2.joystick.CFUNC_Rumble(set_rumble)
    virt.RumbleTriggers = sdl2.joystick.CFUNC_RumbleTriggers(set_rumble)

    # Open the custom joystick
    jcount = sdl2.SDL_NumJoysticks()
    index = sdl2.SDL_JoystickAttachVirtualEx(byref(virt))
    assert index >= 0
    assert sdl2.SDL_JoystickIsVirtual(index) == SDL_TRUE
    assert sdl2.SDL_NumJoysticks() == (jcount + 1)
    stick = sdl2.SDL_JoystickOpen(index)

    # Test joystick configuration
    assert sdl2.SDL_JoystickNumAxes(stick) == 4
    assert sdl2.SDL_JoystickNumButtons(stick) == 8
    assert sdl2.SDL_JoystickNumHats(stick) == 1
    assert sdl2.SDL_JoystickName(stick) == b"PySDL2 Virtual Controller"

    # Test callback functions
    sdl2.SDL_JoystickSetLED(stick, 32, 64, 128)
    assert led_value == [32, 64, 128]
    sdl2.SDL_JoystickRumble(stick, 1000, 2000, 500)
    assert rumble == [1000, 2000]
    sdl2.SDL_JoystickRumbleTriggers(stick, 1234, 4321, 500)
    assert rumble == [1234, 4321]

    # Check that removing the virtual joystick works properly
    sdl2.SDL_JoystickClose(stick)
    jcount = sdl2.SDL_NumJoysticks()
    assert sdl2.SDL_JoystickDetachVirtual(index) == 0
    assert sdl2.SDL_NumJoysticks() == (jcount - 1)

def test_SDL_JoystickName(joysticks):
    names = []
    for stick in joysticks:
        name = sdl2.SDL_JoystickName(stick)
        assert type(name) in (str, bytes)
        names.append(name.decode('utf-8'))
    print(names)

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_JoystickPath(joysticks):
    paths = []
    for stick in joysticks:
        path = sdl2.SDL_JoystickPath(stick)
        if not (is_virtual(stick) or sys.platform == "darwin"):
            assert type(path) in (str, bytes)
            paths.append(path.decode('utf-8'))
    if len(paths):
        print(paths)

@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_JoystickGetPlayerIndex(joysticks):
    for stick in joysticks:
        player = sdl2.SDL_JoystickGetPlayerIndex(stick)
        assert player in [-1, 0, 1, 2, 3]

@pytest.mark.skipif(sdl2.dll.version < 2012, reason="not available")
def test_SDL_JoystickSetPlayerIndex(joysticks):
    i = 0
    for stick in joysticks:
        sdl2.SDL_JoystickSetPlayerIndex(stick, i)
        player = sdl2.SDL_JoystickGetPlayerIndex(stick)
        assert player == i
        i += 1

def test_SDL_JoystickGetGUID(joysticks):
    for stick in joysticks:
        guid = sdl2.SDL_JoystickGetGUID(stick)
        assert isinstance(guid, sdl2.SDL_JoystickGUID)
        guidlist = list(guid.data)
        assert isinstance(guidlist[0], int)

def test_SDL_JoystickGetVendor(joysticks):
    for stick in joysticks:
        vid = sdl2.SDL_JoystickGetVendor(stick)
        assert SDL_GetError() == b""
        if not is_virtual(stick):
            assert vid > 0

def test_SDL_JoystickGetProduct(joysticks):
    for stick in joysticks:
        pid = sdl2.SDL_JoystickGetProduct(stick)
        assert SDL_GetError() == b""
        if not is_virtual(stick):
            assert pid > 0

def test_SDL_JoystickGetProductVersion(joysticks):
    for stick in joysticks:
        pver = sdl2.SDL_JoystickGetProductVersion(stick)
        assert SDL_GetError() == b""
        assert pver >= 0

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_JoystickGetFirmwareVersion(joysticks):
    for stick in joysticks:
        fw_ver = sdl2.SDL_JoystickGetFirmwareVersion(stick)
        assert SDL_GetError() == b""
        assert fw_ver >= 0

@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_JoystickGetSerial(joysticks):
    for stick in joysticks:
        serial = sdl2.SDL_JoystickGetSerial(stick)
        assert SDL_GetError() == b""
        assert serial == None or type(serial) in (str, bytes)

def test_SDL_JoystickGetType(joysticks):
    for stick in joysticks:
        jtype = sdl2.SDL_JoystickGetType(stick)
        assert SDL_GetError() == b""
        assert jtype in joystick_types
        if is_virtual(stick):
            assert jtype == sdl2.SDL_JOYSTICK_TYPE_GAMECONTROLLER

def test_SDL_JoystickGetGUIDString():
    guid_str = b'030000007e050000060300001c3a0000' # Wiimote on macOS
    guid = sdl2.SDL_JoystickGetGUIDFromString(guid_str)
    buff = create_string_buffer(33)
    sdl2.SDL_JoystickGetGUIDString(guid, buff, 33) # Get GUID string
    assert guid_str == buff.value

def test_SDL_JoystickGetGUIDFromString():
    guid_str = b'030000007e050000060300001c3a0000' # Wiimote on macOS
    expected = [3, 0, 0, 0, 126, 5, 0, 0, 6, 3, 0, 0, 28, 58, 0, 0]
    guid = sdl2.SDL_JoystickGetGUIDFromString(guid_str)
    assert list(guid.data) == expected

@pytest.mark.skipif(sdl2.dll.version < 2260, reason="not available")
@pytest.mark.xfail(sys.version_info < (3, 7, 0, 'final'), reason="ctypes bug")
def test_SDL_GetJoystickGUIDInfo():
    guid_str = b'030000007e050000060300001c3a0000' # Wiimote on macOS
    guid = sdl2.SDL_JoystickGetGUIDFromString(guid_str)
    # Try parsing field information from GUID
    vendor, product, version = c_uint16(0), c_uint16(0), c_uint16(0)
    crc16 = c_uint16(0)
    sdl2.SDL_GetJoystickGUIDInfo(
        guid, byref(vendor), byref(product), byref(version), byref(crc16)
    )
    assert vendor.value == 1406
    assert product.value > 0
    assert version.value > 0
    assert crc16.value == 0

def test_SDL_JoystickGetAttached(joysticks):
    for stick in joysticks:
        ret = sdl2.SDL_JoystickGetAttached(stick)
        assert ret in [SDL_FALSE, SDL_TRUE]

def test_SDL_JoystickInstanceID(joysticks):
    for stick in joysticks:
        ret = sdl2.SDL_JoystickInstanceID(stick)
        assert ret >= 0

def test_SDL_JoystickNumAxes(joysticks):
    for stick in joysticks:
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        axes = sdl2.SDL_JoystickNumAxes(stick)
        assert axes >= 0
        if is_virtual(stick):
            assert axes == 2

def test_SDL_JoystickNumBalls(joysticks):
    for stick in joysticks:
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        balls = sdl2.SDL_JoystickNumBalls(stick)
        assert balls >= 0

def test_SDL_JoystickNumHats(joysticks):
    for stick in joysticks:
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        hats = sdl2.SDL_JoystickNumHats(stick)
        assert hats >= 0
        if is_virtual(stick):
            assert hats == 1

def test_SDL_JoystickNumButtons(joysticks):
    for stick in joysticks:
        assert isinstance(stick.contents, sdl2.SDL_Joystick)
        buttons = sdl2.SDL_JoystickNumButtons(stick)
        assert buttons >= 0
        if is_virtual(stick):
            assert buttons == 4

def test_SDL_JoystickUpdate(with_sdl):
    # NOTE: Returns void, can't really test anything else
    sdl2.SDL_JoystickUpdate()
    assert SDL_GetError() == b""

def test_SDL_JoystickEventState(with_sdl):
    for state in (SDL_IGNORE, SDL_ENABLE):
        news = sdl2.SDL_JoystickEventState(state)
        assert news == state
        query = sdl2.SDL_JoystickEventState(SDL_QUERY)
        assert query == state

def test_SDL_JoystickGetAxis(joysticks):
    for stick in joysticks:
        for axis in range(sdl2.SDL_JoystickNumAxes(stick)):
            val = sdl2.SDL_JoystickGetAxis(stick, axis)
            assert -32768 <= val <= 32767

def test_SDL_JoystickGetAxisInitialState(joysticks):
    init_state = c_int16(0)
    for stick in joysticks:
        for axis in range(sdl2.SDL_JoystickNumAxes(stick)):
            ret = sdl2.SDL_JoystickGetAxisInitialState(
                stick, axis, byref(init_state)
            )
            assert SDL_GetError() == b""
            assert -32768 <= init_state.value <= 32767
            assert ret in [SDL_TRUE, SDL_FALSE]

def test_SDL_JoystickGetHat(joysticks):
    hatvals = [
        sdl2.SDL_HAT_UP, sdl2.SDL_HAT_DOWN, sdl2.SDL_HAT_LEFT,
        sdl2.SDL_HAT_RIGHT, sdl2.SDL_HAT_CENTERED,
        sdl2.SDL_HAT_LEFTUP, sdl2.SDL_HAT_LEFTDOWN,
        sdl2.SDL_HAT_RIGHTUP, sdl2.SDL_HAT_RIGHTDOWN
    ]
    for stick in joysticks:
        for hat in range(sdl2.SDL_JoystickNumHats(stick)):
            val = sdl2.SDL_JoystickGetHat(stick, hat)
            assert val in hatvals

def test_SDL_JoystickGetBall(joysticks):
    numball = [sdl2.SDL_JoystickNumBalls(s) for s in joysticks]
    if not any(numball):
        pytest.skip("no trackball on any connected controller")
    dx, dy = c_int(0), c_int(0)
    get_ball = sdl2.SDL_JoystickGetBall
    for stick in sticks:
        for ball in range(sdl2.SDL_JoystickNumBalls(stick)):
            ret = get_ball(stick, ball, byref(dx), byref(dy))
            assert SDL_GetError() == b""
            assert ret == 0

def test_SDL_JoystickGetButton(joysticks):
    for stick in joysticks:
        for button in range(sdl2.SDL_JoystickNumButtons(stick)):
            val = sdl2.SDL_JoystickGetButton(stick, button)
            assert val in [0, 1]

@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_JoystickRumble(joysticks):
    # If we ever add an interactive test suite, this should be moved there
    for stick in joysticks:
        # 50% strength low-frequency, 25% high-frequency rumble for 500ms
        ret = sdl2.SDL_JoystickRumble(stick, 32767, 16384, 500)
        assert ret in [-1, 0]

@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_JoystickRumbleTriggers(joysticks):
    # If we ever add an interactive test suite, this should be moved there
    for stick in joysticks:
        # 50% strength left trigger, 25% right trigger rumble for 500ms
        ret = sdl2.SDL_JoystickRumbleTriggers(stick, 32767, 16384, 500)
        assert ret in [-1, 0]

@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_JoystickHasSetLED(joysticks):
    # If we ever add an interactive test suite, this should be moved there
    for stick in joysticks:
        has_led = sdl2.SDL_JoystickHasLED(stick)
        assert has_led in [SDL_FALSE, SDL_TRUE]
        expected = -1 if has_led == SDL_FALSE else 0
        cols = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for r, g, b in cols:
            ret = sdl2.SDL_JoystickSetLED(stick, r, g, b)
            assert ret == expected

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_JoystickHasRumble(joysticks):
    # If we ever add an interactive test suite, this should be moved there
    for stick in joysticks:
        has_rumble = sdl2.SDL_JoystickHasRumble(stick)
        assert has_rumble in [SDL_FALSE, SDL_TRUE]

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_JoystickHasRumbleTriggers(joysticks):
    # If we ever add an interactive test suite, this should be moved there
    for stick in joysticks:
        has_rumble_triggers = sdl2.SDL_JoystickHasRumbleTriggers(stick)
        assert has_rumble_triggers in [SDL_FALSE, SDL_TRUE]

@pytest.mark.skip("not implemented")
@pytest.mark.skipif(sdl2.dll.version < 2016, reason="not available")
def test_SDL_JoystickSendEffect(joysticks):
    # NOTE: Not supported on macOS or Linux, and effect data would be specific
    # to each controller type, so can't easily test this.
    pass

def test_SDL_JoystickCurrentPowerLevel(joysticks):
    levels = [
        sdl2.SDL_JOYSTICK_POWER_UNKNOWN,
        sdl2.SDL_JOYSTICK_POWER_EMPTY,
        sdl2.SDL_JOYSTICK_POWER_LOW,
        sdl2.SDL_JOYSTICK_POWER_MEDIUM,
        sdl2.SDL_JOYSTICK_POWER_FULL,
        sdl2.SDL_JOYSTICK_POWER_WIRED,
        sdl2.SDL_JOYSTICK_POWER_MAX,
    ]
    for stick in joysticks:
        pwr = sdl2.SDL_JoystickCurrentPowerLevel(stick)
        assert SDL_GetError() == b""
        assert pwr in levels
