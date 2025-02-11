import sys
import pytest
import sdl2
from ctypes import create_string_buffer, byref

# Override global cleanup fixture since it calls SDL_ClearError
@pytest.fixture(autouse=True)
def sdl_cleanup():
    yield


def test_SDL_GetSetClearError():
    sdl2.SDL_SetError(b"Hi there!")
    assert sdl2.SDL_GetError() == b"Hi there!"
    sdl2.SDL_SetError(b"Error 2");
    assert sdl2.SDL_GetError() == b"Error 2"
    sdl2.SDL_ClearError();
    assert sdl2.SDL_GetError() == b""

@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_GetErrorMsg():
    sdl2.SDL_SetError(b"123456789")
    assert sdl2.SDL_GetError() == b"123456789"
    buf = create_string_buffer(10)
    assert sdl2.SDL_GetErrorMsg(buf, 10) == b"123456789"
    assert buf.value == b"123456789"
    buf2 = create_string_buffer(5)
    assert sdl2.SDL_GetErrorMsg(buf2, 5) == b"1234"
    assert buf2.value == b"1234"
    sdl2.SDL_ClearError()
