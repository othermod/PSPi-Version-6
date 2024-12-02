import sys
import pytest
from ctypes import c_int, cast, byref, POINTER
import sdl2
from sdl2 import SDL_TRUE, SDL_FALSE, SDL_GetError
from sdl2 import rect, scancode, keycode, video

byteify = lambda x: x.encode("utf-8")

@pytest.fixture
def window(with_sdl):
    flag = video.SDL_WINDOW_INPUT_FOCUS
    w = video.SDL_CreateWindow(b"Test", 10, 40, 32, 24, flag)
    if not isinstance(w.contents, sdl2.SDL_Window):
        assert sdl2.SDL_GetError() == b""
        assert isinstance(w.contents, sdl2.SDL_Window)
    sdl2.SDL_ClearError()
    yield w
    video.SDL_DestroyWindow(w)


def test_SDL_Keysym():
    keysym = sdl2.SDL_Keysym()
    assert keysym.scancode == 0
    assert keysym.sym == 0
    assert keysym.mod == 0

    keysym = sdl2.SDL_Keysym(1, 2, 3, ord("b"))
    assert keysym.scancode == 1
    assert keysym.sym == 2
    assert keysym.mod == 3

    uval = "\u0220"
    if sys.version_info[0] < 3:
        uval = unichr(8224)
    keysym = sdl2.SDL_Keysym(17, 32, 88, ord(uval))
    assert keysym.scancode == 17
    assert keysym.sym == 32
    assert keysym.mod == 88


def test_SDL_GetKeyboardFocus(window):
    # NOTE: Would need to actually set keyboard focus for window to test,
    # which I can't seem to get working in pytest
    video.SDL_ShowWindow(window)
    focused_win = sdl2.SDL_GetKeyboardFocus()
    if focused_win:
        focused_id = video.SDL_GetWindowID(focused_win)
        assert video.SDL_GetWindowID(window) == focused_id

def test_SDL_GetKeyboardState(with_sdl):
    # NOTE: This function returns a pointer to an array, which we can use
    # directly as an array in Python since we know how long it is from numkeys
    states = (c_int * scancode.SDL_NUM_SCANCODES)()
    numkeys = c_int(0)
    keystates = sdl2.SDL_GetKeyboardState(byref(numkeys))
    assert numkeys.value > 0
    for key in keystates[:numkeys.value]:
        assert key in [0, 1]

@pytest.mark.skipif(sdl2.dll.version < 2240, reason="not available")
def test_SDL_ResetKeyboard(with_sdl):
    # Not entirely sure how to test this without user interaction
    sdl2.SDL_ResetKeyboard()

def test_SDL_GetSetModState(with_sdl):
    test_states = [
        keycode.KMOD_NUM | keycode.KMOD_CAPS | keycode.KMOD_MODE,
        keycode.KMOD_LCTRL | keycode.KMOD_LSHIFT,
        keycode.KMOD_CAPS,
    ]
    initial = sdl2.SDL_GetModState()
    for state in test_states:
        sdl2.SDL_SetModState(state)
        assert sdl2.SDL_GetModState() == state
    # Try resetting the modifier state to the initial value
    sdl2.SDL_SetModState(initial)
    assert sdl2.SDL_GetModState() == initial

def test_SDL_GetKeyFromScancode(with_sdl):
    # Test with letter keys
    scan_key_offset = 93
    for scan in range(scancode.SDL_SCANCODE_A, scancode.SDL_SCANCODE_Z + 1):
        key = sdl2.SDL_GetKeyFromScancode(scan)
        assert key == scan + scan_key_offset
    # Test with number keys
    scan_key_offset = 19
    for scan in range(scancode.SDL_SCANCODE_1, scancode.SDL_SCANCODE_9 + 1):
        key = sdl2.SDL_GetKeyFromScancode(scan)
        assert key == scan + scan_key_offset

def test_SDL_GetScancodeFromKey(with_sdl):
    # Test with letter keys
    scan_key_offset = 93
    for scan in range(scancode.SDL_SCANCODE_A, scancode.SDL_SCANCODE_Z + 1):
        key = scan + scan_key_offset
        assert sdl2.SDL_GetScancodeFromKey(key) == scan
    # Test with number keys
    scan_key_offset = 19
    for scan in range(scancode.SDL_SCANCODE_1, scancode.SDL_SCANCODE_9 + 1):
        key = scan + scan_key_offset
        assert sdl2.SDL_GetScancodeFromKey(key) == scan
    # Test with unknown key
    key = sdl2.SDL_GetScancodeFromKey(477)
    assert key == scancode.SDL_SCANCODE_UNKNOWN

def test_SDL_GetScancodeName(with_sdl):
    names = range(ord('A'), ord('Z'))
    xoff = 0
    for code in range(scancode.SDL_SCANCODE_A, scancode.SDL_SCANCODE_Z):
        name = sdl2.SDL_GetScancodeName(code)
        assert name == byteify(chr(names[xoff]))
        xoff += 1
    # Test with unknown scancode
    name = sdl2.SDL_GetScancodeName(0)
    assert name == b""

def test_SDL_GetScancodeFromName(with_sdl):
    codes = range(scancode.SDL_SCANCODE_A, scancode.SDL_SCANCODE_Z)
    xoff = 0
    for key in range(ord('a'), ord('z')):
        ch = chr(key)
        code = sdl2.SDL_GetScancodeFromName(byteify(ch))
        assert code == codes[xoff]
        xoff += 1
    # Test with invalid key name
    key = sdl2.SDL_GetScancodeFromName(b"")
    assert key == scancode.SDL_SCANCODE_UNKNOWN

def test_SDL_GetKeyName(with_sdl):
    x = 65  # SDL maps everything against upper-case letters
    for key in range(ord('a'), ord('z')):
        ch = chr(x)
        name = sdl2.SDL_GetKeyName(key)
        assert name == byteify(ch)
        x += 1

def test_SDL_GetKeyFromName(with_sdl):
    # Test with lower-case ASCII characters
    for x in range(26):
        key = sdl2.SDL_GetKeyFromName(byteify(chr(x + 97)))
        assert key == x + 97
    # Test with ASCII numbers
    for x in range(10):
        key = sdl2.SDL_GetKeyFromName(("%d" % x).encode("utf-8"))
        assert key == 48 + x
    # Test handling of unknown values
    val = sdl2.SDL_GetKeyFromName(b"not a key")
    assert val == keycode.SDLK_UNKNOWN

def test_SDL_StartStopTextInput(with_sdl):
    sdl2.SDL_StopTextInput()
    assert SDL_GetError() == b""
    assert sdl2.SDL_IsTextInputActive() == SDL_FALSE
    sdl2.SDL_StartTextInput()
    assert SDL_GetError() == b""
    assert sdl2.SDL_IsTextInputActive() == SDL_TRUE

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_ClearComposition(with_sdl):
    sdl2.SDL_ClearComposition() # Not sure how else to test

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_IsTextInputShown(with_sdl):
    ret = sdl2.SDL_IsTextInputShown()
    assert ret in [SDL_TRUE, SDL_FALSE]

def test_SDL_SetTextInputRect(with_sdl):
    sdl2.SDL_StartTextInput()
    coords = [(0, 0, 0, 0), (-10, -70, 3, 6), (10, 10, 10, 10)]
    for x, y, w, h in coords:
        r = rect.SDL_Rect(x, y, w, h)
        sdl2.SDL_SetTextInputRect(r)
        assert SDL_GetError() == b""

def test_SDL_HasScreenKeyboardSupport(with_sdl):
    ret = sdl2.SDL_HasScreenKeyboardSupport()
    assert ret in [SDL_TRUE, SDL_FALSE]

def test_SDL_IsScreenKeyboardShown(window):
    ret = sdl2.SDL_IsScreenKeyboardShown(window)
    assert ret in [SDL_TRUE, SDL_FALSE]
