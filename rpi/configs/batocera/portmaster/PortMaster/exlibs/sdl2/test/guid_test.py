from ctypes import create_string_buffer

import pytest
import sdl2


@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_GUIDToString():
    guid_str = b'030000007e050000060300001c3a0000' # Wiimote on macOS
    guid = sdl2.SDL_GUIDFromString(guid_str)
    buff = create_string_buffer(33)
    sdl2.SDL_GUIDToString(guid, buff, 33) # Get GUID string
    assert guid_str == buff.value

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_GUIDFromString():
    guid_str = b'030000007e050000060300001c3a0000' # Wiimote on macOS
    expected = [3, 0, 0, 0, 126, 5, 0, 0, 6, 3, 0, 0, 28, 58, 0, 0]
    guid = sdl2.SDL_GUIDFromString(guid_str)
    assert list(guid.data) == expected
