import sys
import ctypes
import pytest
import sdl2
from sdl2 import dll, __version__, version_info


def test__version_tuple():
    # Note that this is not public API.
    assert dll._version_tuple_to_int((2, 0, 18)) == 2018
    assert dll._version_tuple_to_int((2, 24, 1)) == 2241
    # Micro version stops at 9 in this encoding
    assert dll._version_tuple_to_int((2, 24, 15)) == 2249
    assert dll._version_tuple_to_int((2, 99, 9)) == 2999
    # Minor version stops at 99 in this encoding
    assert dll._version_tuple_to_int((2, 103, 6)) == 2999

def test_SDL_version():
    v = sdl2.SDL_version(0, 0, 0)
    assert v.major == 0
    assert v.minor == 0
    assert v.patch == 0

def test_SDL_GetVersion():
    v = sdl2.SDL_version()
    sdl2.SDL_GetVersion(ctypes.byref(v))
    assert type(v) == sdl2.SDL_version
    assert v.major == 2
    assert v.minor >= 0
    assert v.patch >= 0
    assert (v.major, v.minor, v.patch) >= (2, 0, 5)
    assert (v.major, v.minor, v.patch) == dll.version_tuple

def test_SDL_VERSIONNUM():
    assert sdl2.SDL_VERSIONNUM(1, 2, 3) == 1203
    assert sdl2.SDL_VERSIONNUM(4, 5, 6) == 4506
    assert sdl2.SDL_VERSIONNUM(2, 0, 0) == 2000
    assert sdl2.SDL_VERSIONNUM(17, 42, 3) == 21203

    # This is a bit weird now that SDL uses the minor version more often,
    # but does sort in the correct order against all versions of SDL 2.
    assert sdl2.SDL_VERSIONNUM(2, 23, 0) == 4300
    # This is the highest possible SDL 2 version
    assert sdl2.SDL_VERSIONNUM(2, 255, 99) == 27599

def test_SDL_VERSION_ATLEAST():
    assert sdl2.SDL_VERSION_ATLEAST(1, 2, 3)
    assert sdl2.SDL_VERSION_ATLEAST(2, 0, 0)
    assert sdl2.SDL_VERSION_ATLEAST(2, 0, 1)
    assert sdl2.SDL_VERSION_ATLEAST(
        sdl2.SDL_MAJOR_VERSION, sdl2.SDL_MINOR_VERSION, sdl2.SDL_PATCHLEVEL
    )
    assert not sdl2.SDL_VERSION_ATLEAST(4, 0, 0)

def test_SDL_GetRevision():
    rev = sdl2.SDL_GetRevision()
    # If revision not empty string (e.g. Conda), test the prefix
    if len(rev):
        if dll.version_tuple >= (2, 0, 16):
            if rev[0:4] not in (b"http", b"SDL-"):
                pytest.xfail("no API guarantee about the format of this string")
        else:
            assert rev[0:3] == b"hg-"

def test_SDL_GetRevisionNumber():
    if sys.platform in ("win32",) or dll.version_tuple >= (2, 0, 16):
        # HG tip on Win32 does not set any revision number
        assert sdl2.SDL_GetRevisionNumber() >= 0
    else:
        assert sdl2.SDL_GetRevisionNumber() >= 7000
