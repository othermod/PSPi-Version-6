import os
import sys
import ctypes
import pytest
from io import BytesIO
import sdl2


if sys.version_info[0] >= 3:
    byteify = bytes
    stringify = lambda x, enc: x.decode(enc)
else:
    byteify = lambda x, enc: x.encode(enc)
    stringify = lambda x, enc: str(x)

@pytest.fixture
def testfile_path():
    testdir = os.path.dirname(os.path.abspath(__file__))
    testfile = os.path.join(testdir, "resources", "rwopstest.txt")
    testfile = testfile.encode("utf-8")
    yield testfile

@pytest.fixture
def with_test_rw():
    sdl2.SDL_ClearError()
    buf = ctypes.create_string_buffer(b"abcdefghijklmnop")
    rw = sdl2.SDL_RWFromMem(buf, len(buf))
    assert sdl2.SDL_GetError() == b""
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    yield (rw, buf)
    sdl2.SDL_RWclose(rw)

@pytest.fixture
def test_buf():
    buf = BytesIO()
    buf.write(b"abcdefghijklmnop")
    buf.seek(0, os.SEEK_SET)
    yield buf


def test_SDL_RWops():
    rw = sdl2.SDL_RWops()
    assert isinstance(rw, sdl2.SDL_RWops)

def test_SDL_RWFromFile(testfile_path):
    rw = sdl2.SDL_RWFromFile(testfile_path, b"r")
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    # Read the first 36 bytes(sic!). It should be:
    # 'This is a test file for sdl2.rwops!'
    length = 36
    buf = BytesIO()
    while length >= 2:
        # Reading in two bytes - we have plain text (1-byte encoding), so
        # we read in 2 characters at a time. This means that the first
        # character is always stored in the low byte.
        ch = sdl2.SDL_ReadLE16(rw)
        buf.write(byteify(chr(ch & 0x00FF), "utf-8"))
        buf.write(byteify(chr(ch >> 8), "utf-8"))
        length -= 2
    expected = "This is a test file for  sdl2.rwops!"
    assert stringify(buf.getvalue(), "utf-8") == expected

@pytest.mark.skip("not implemented")
def test_SDL_RWFromFP():
    # Requires a C stdio.h file pointer as input, not worth testing
    pass

def test_SDL_RWFromMem():
    buf = ctypes.create_string_buffer(b"1234")
    rw = sdl2.SDL_RWFromMem(buf, len(buf))
    assert sdl2.SDL_GetError() == b""
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    # Make sure it's writable
    value = (
        (ord("a")) | (ord("b") << 8)
    )
    assert sdl2.SDL_WriteLE16(rw, value) == 1
    assert buf.value == b"ab34"

def test_SDL_RWFromConstMem():
    buf = ctypes.create_string_buffer(b"1234")
    rw = sdl2.SDL_RWFromConstMem(buf, len(buf))
    assert sdl2.SDL_GetError() == b""
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    # Make sure it isn't writable
    value = (
        (ord("a")) | (ord("b") << 8)
    )
    assert sdl2.SDL_WriteLE16(rw, value) == 0
    assert buf.value == b"1234"

def test_SDL_RWsize(with_test_rw):
    rw, buf = with_test_rw
    assert sdl2.SDL_RWsize(rw) == len(buf)

def test_SDL_RWSeekTell(with_test_rw):
    rw, buf = with_test_rw
    seek_tests = [
        (sdl2.RW_SEEK_END, 0, len(buf)), # Seek to end of RW
        (sdl2.RW_SEEK_SET, 0, 0), # Seek to start of RW
        (sdl2.RW_SEEK_CUR, 8, 8), # Seek 8 bytes forward from current pos
        (sdl2.RW_SEEK_CUR, -3, 5), # Seek 3 bytes back from current pos
        (sdl2.RW_SEEK_END, -4, len(buf) - 4), # Seek 4 bytes back from end
    ]
    for whence, offset, expected in seek_tests:
        pos1 = sdl2.SDL_RWseek(rw, offset, whence)
        pos2 = sdl2.SDL_RWtell(rw)
        assert pos1 == pos2
        assert pos1 == expected

def test_SDL_RWread(with_test_rw):
    rw, buf = with_test_rw
    # Read the first two characters
    readbuf = ctypes.create_string_buffer(2)
    read = sdl2.SDL_RWread(rw, readbuf, 1, 2)
    assert read == 2
    assert readbuf.raw == b"ab"
    # Read the next 5 characters
    readbuf = ctypes.create_string_buffer(5)
    read = sdl2.SDL_RWread(rw, readbuf, 1, 5)
    assert read == 5
    assert readbuf.raw == b"cdefg"

def test_SDL_RWwrite(with_test_rw):
    rw, buf = with_test_rw
    # Overwrite first 2 characters
    writebuf = ctypes.create_string_buffer(b"12")
    written = sdl2.SDL_RWwrite(rw, writebuf, 1, 2)
    assert written == 2
    assert buf.value == b"12cdefghijklmnop"
    # Overwrite last 4 characters
    writebuf = ctypes.create_string_buffer(b"TEST")
    sdl2.SDL_RWseek(rw, -5, sdl2.RW_SEEK_END) # NOTE: -5 here b/c of end byte
    written = sdl2.SDL_RWwrite(rw, writebuf, 1, 4)
    assert written == 4
    assert buf.value == b"12cdefghijklTEST"

def test_SDL_RWclose():
    buf = ctypes.create_string_buffer(b"abcdefghijklmnop")
    rw = sdl2.SDL_RWFromMem(buf, len(buf))
    assert sdl2.SDL_GetError() == b""
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    # Close the RW object and check for any errors
    assert sdl2.SDL_RWsize(rw) == len(buf)
    ret = sdl2.SDL_RWclose(rw)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0

def test_SDL_AllocFreeRW():
    rw = sdl2.SDL_AllocRW()
    assert sdl2.SDL_GetError() == b""
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    sdl2.SDL_FreeRW(rw)
    assert sdl2.SDL_GetError() == b""

@pytest.mark.skipif(sdl2.dll.version < 2006, reason="not available")
def test_SDL_LoadFile_RW(testfile_path):
    rw = sdl2.SDL_RWFromFile(testfile_path, b"r")
    assert isinstance(rw.contents, sdl2.SDL_RWops)
    datasize = ctypes.c_size_t(0)
    data_p = sdl2.SDL_LoadFile_RW(rw, ctypes.byref(datasize), 0)
    assert sdl2.SDL_GetError() == b""
    assert datasize.value > 0
    data = ctypes.string_at(data_p, datasize.value)
    assert data[:19] == b"This is a test file"

@pytest.mark.skipif(sdl2.dll.version < 2006, reason="not available")
def test_SDL_LoadFile(testfile_path):
    datasize = ctypes.c_size_t(0)
    data_p = sdl2.SDL_LoadFile(testfile_path, ctypes.byref(datasize))
    assert sdl2.SDL_GetError() == b""
    assert datasize.value > 0
    data = ctypes.string_at(data_p, datasize.value)
    assert data[:19] == b"This is a test file"


# SDL RW Read tests

def test_SDL_ReadU8(with_test_rw):
    rw, buf = with_test_rw
    assert chr(sdl2.SDL_ReadU8(rw)) == "a"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    assert chr(sdl2.SDL_ReadU8(rw)) == "i"

def test_SDL_ReadLE16(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadLE16(rw)
    assert chr(ch & 0x00FF) == "a"
    assert chr(ch >> 8) == "b"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadLE16(rw)
    assert chr(ch & 0x00FF) == "i"
    assert chr(ch >> 8) == "j"

def test_SDL_ReadBE16(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadBE16(rw)
    assert chr(ch & 0x00FF) == "b"
    assert chr(ch >> 8) == "a"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadBE16(rw)
    assert chr(ch & 0x00FF) == "j"
    assert chr(ch >> 8) == "i"

def test_SDL_ReadLE32(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadLE32(rw)
    assert chr(ch & 0x000000FF) == "a"
    assert chr((ch & 0x0000FF00) >> 8) == "b"
    assert chr((ch & 0x00FF0000) >> 16) == "c"
    assert chr((ch & 0xFF000000) >> 24) == "d"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadLE32(rw)
    assert chr(ch & 0x000000FF) == "i"
    assert chr((ch & 0x0000FF00) >> 8) == "j"
    assert chr((ch & 0x00FF0000) >> 16) == "k"
    assert chr((ch & 0xFF000000) >> 24) == "l"

def test_SDL_ReadBE32(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadBE32(rw)
    assert chr(ch & 0x000000FF) == "d"
    assert chr((ch & 0x0000FF00) >> 8) == "c"
    assert chr((ch & 0x00FF0000) >> 16) == "b"
    assert chr((ch & 0xFF000000) >> 24) == "a"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadBE32(rw)
    assert chr(ch & 0x000000FF) == "l"
    assert chr((ch & 0x0000FF00) >> 8) == "k"
    assert chr((ch & 0x00FF0000) >> 16) == "j"
    assert chr((ch & 0xFF000000) >> 24) == "i"

def test_SDL_ReadLE64(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadLE64(rw)
    assert chr(ch & 0x00000000000000FF) == "a"
    assert chr((ch & 0x000000000000FF00) >> 8) == "b"
    assert chr((ch & 0x0000000000FF0000) >> 16) == "c"
    assert chr((ch & 0x00000000FF000000) >> 24) == "d"
    assert chr((ch & 0x000000FF00000000) >> 32) == "e"
    assert chr((ch & 0x0000FF0000000000) >> 40) == "f"
    assert chr((ch & 0x00FF000000000000) >> 48) == "g"
    assert chr((ch & 0xFF00000000000000) >> 56) == "h"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadLE64(rw)
    assert chr(ch & 0x00000000000000FF) == "i"
    assert chr((ch & 0x000000000000FF00) >> 8) == "j"
    assert chr((ch & 0x0000000000FF0000) >> 16) == "k"
    assert chr((ch & 0x00000000FF000000) >> 24) == "l"
    assert chr((ch & 0x000000FF00000000) >> 32) == "m"
    assert chr((ch & 0x0000FF0000000000) >> 40) == "n"
    assert chr((ch & 0x00FF000000000000) >> 48) == "o"
    assert chr((ch & 0xFF00000000000000) >> 56) == "p"

def test_SDL_ReadBE64(with_test_rw):
    rw, buf = with_test_rw
    ch = sdl2.SDL_ReadBE64(rw)
    assert chr(ch & 0x00000000000000FF) == "h"
    assert chr((ch & 0x000000000000FF00) >> 8) == "g"
    assert chr((ch & 0x0000000000FF0000) >> 16) == "f"
    assert chr((ch & 0x00000000FF000000) >> 24) == "e"
    assert chr((ch & 0x000000FF00000000) >> 32) == "d"
    assert chr((ch & 0x0000FF0000000000) >> 40) == "c"
    assert chr((ch & 0x00FF000000000000) >> 48) == "b"
    assert chr((ch & 0xFF00000000000000) >> 56) == "a"
    pos = sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert pos == 8
    ch = sdl2.SDL_ReadBE64(rw)
    assert chr(ch & 0x00000000000000FF) == "p"
    assert chr((ch & 0x000000000000FF00) >> 8) == "o"
    assert chr((ch & 0x0000000000FF0000) >> 16) == "n"
    assert chr((ch & 0x00000000FF000000) >> 24) == "m"
    assert chr((ch & 0x000000FF00000000) >> 32) == "l"
    assert chr((ch & 0x0000FF0000000000) >> 40) == "k"
    assert chr((ch & 0x00FF000000000000) >> 48) == "j"
    assert chr((ch & 0xFF00000000000000) >> 56) == "i"


# SDL RW Write tests

def test_SDL_WriteU8(with_test_rw):
    rw, buf = with_test_rw
    assert sdl2.SDL_WriteU8(rw, ord("1")) == 1
    assert buf.value == b"1bcdefghijklmnop"
    sdl2.SDL_RWseek(rw, 6, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteU8(rw, ord("1")) == 1
    assert buf.value == b"1bcdef1hijklmnop"

def test_SDL_WriteLE16(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 8) | (ord("2"))
    )
    assert sdl2.SDL_WriteLE16(rw, value) == 1
    assert buf.value == b"21cdefghijklmnop"
    sdl2.SDL_RWseek(rw, 6, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteLE16(rw, value) == 1
    assert buf.value == b"21cdef21ijklmnop"

def test_SDL_WriteBE16(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 8) | (ord("2"))
    )
    assert sdl2.SDL_WriteBE16(rw, value) == 1
    assert buf.value == b"12cdefghijklmnop"
    sdl2.SDL_RWseek(rw, 6, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteBE16(rw, value) == 1
    assert buf.value == b"12cdef12ijklmnop"

def test_SDL_WriteLE32(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 24) |
        (ord("2") << 16) |
        (ord("3") << 8)  |
        (ord("4"))
    )
    assert sdl2.SDL_WriteLE32(rw, value) == 1
    assert buf.value == b"4321efghijklmnop"
    sdl2.SDL_RWseek(rw, 6, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteLE32(rw, value) == 1
    assert buf.value == b"4321ef4321klmnop"

def test_SDL_WriteBE32(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 24) |
        (ord("2") << 16) |
        (ord("3") << 8)  |
        (ord("4"))
    )
    assert sdl2.SDL_WriteBE32(rw, value) == 1
    assert buf.value == b"1234efghijklmnop"
    sdl2.SDL_RWseek(rw, 6, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteBE32(rw, value) == 1
    assert buf.value == b"1234ef1234klmnop"

def test_SDL_WriteLE64(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 56) |
        (ord("2") << 48) |
        (ord("3") << 40) |
        (ord("4") << 32) |
        (ord("5") << 24) |
        (ord("6") << 16) |
        (ord("7") << 8)  |
        (ord("8"))
    )
    assert sdl2.SDL_WriteLE64(rw, value) == 1
    assert buf.value == b"87654321ijklmnop"
    sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteLE64(rw, value) == 1
    assert buf.value == b"8765432187654321"

def test_SDL_WriteBE64(with_test_rw):
    rw, buf = with_test_rw
    value = (
        (ord("1") << 56) |
        (ord("2") << 48) |
        (ord("3") << 40) |
        (ord("4") << 32) |
        (ord("5") << 24) |
        (ord("6") << 16) |
        (ord("7") << 8)  |
        (ord("8"))
    )
    assert sdl2.SDL_WriteBE64(rw, value) == 1
    assert buf.value == b"12345678ijklmnop"
    sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
    assert sdl2.SDL_WriteBE64(rw, value) == 1
    assert buf.value == b"1234567812345678"


class TestPythonRWops(object):

    def test_init(self, testfile_path):
        # Try creating an RWops from a BytesIO
        buf = BytesIO()
        rw = sdl2.rw_from_object(buf)
        assert isinstance(rw, sdl2.SDL_RWops)
        # Try creating an RWops from a file object
        fileobj = open(testfile_path, "rb")
        rw2 = sdl2.rw_from_object(fileobj)
        assert isinstance(rw2, sdl2.SDL_RWops)
        # NOTE: add to this? Not sure what else is useful to test.

    def test_size(self, test_buf):
        rw = sdl2.rw_from_object(test_buf)
        assert sdl2.SDL_RWsize(rw) == len(test_buf.getvalue())
        # Make sure querying size doesn't change the seek position
        assert sdl2.SDL_RWtell(rw) == 0
        assert sdl2.SDL_RWseek(rw, 8, sdl2.RW_SEEK_SET)
        assert sdl2.SDL_RWsize(rw) == len(test_buf.getvalue())
        assert sdl2.SDL_RWtell(rw) == 8
        
    def test_seek(self, test_buf):
        rw = sdl2.rw_from_object(test_buf)
        buflen = len(test_buf.getvalue())
        seek_tests = [
            (sdl2.RW_SEEK_END, 0, buflen), # Seek to end of RW
            (sdl2.RW_SEEK_SET, 0, 0), # Seek to start of RW
            (sdl2.RW_SEEK_CUR, 8, 8), # Seek 8 bytes forward from current pos
            (sdl2.RW_SEEK_CUR, -3, 5), # Seek 3 bytes back from current pos
            (sdl2.RW_SEEK_END, -4, buflen - 4), # Seek 4 bytes back from end
        ]
        for whence, offset, expected in seek_tests:
            pos1 = sdl2.SDL_RWseek(rw, offset, whence)
            pos2 = sdl2.SDL_RWtell(rw)
            pos3 = test_buf.tell() # Get actual buffer's tell as well
            assert pos1 == pos2
            assert pos1 == pos3
            assert pos1 == expected

    def test_read(self, test_buf):
        rw = sdl2.rw_from_object(test_buf)
        # Read the first two characters
        readbuf = ctypes.create_string_buffer(2)
        read = sdl2.SDL_RWread(rw, readbuf, 1, 2)
        assert read == 2
        assert readbuf.raw == b"ab"
        # Read the next 5 characters
        readbuf = ctypes.create_string_buffer(5)
        read = sdl2.SDL_RWread(rw, readbuf, 1, 5)
        assert read == 5
        assert readbuf.raw == b"cdefg"

    def test_close(self, test_buf):
        rw = sdl2.rw_from_object(test_buf)
        assert not test_buf.closed
        sdl2.SDL_RWclose(rw)
        assert test_buf.closed

    def test_write(self, test_buf):
        rw = sdl2.rw_from_object(test_buf)
        # Overwrite first 2 characters
        writebuf = ctypes.create_string_buffer(b"12")
        written = sdl2.SDL_RWwrite(rw, writebuf, 1, 2)
        assert written == 2
        assert bytes(test_buf.getvalue()) == b"12cdefghijklmnop"
        # Overwrite last 4 characters
        writebuf = ctypes.create_string_buffer(b"TEST")
        sdl2.SDL_RWseek(rw, -4, sdl2.RW_SEEK_END)
        written = sdl2.SDL_RWwrite(rw, writebuf, 1, 4)
        assert written == 4
        assert bytes(test_buf.getvalue()) == b"12cdefghijklTEST"
