import sys
import array
import ctypes
import struct
import pytest
from sdl2.ext import array as sdlextarray

BIG_ENDIAN = sys.byteorder == "big"

singlebyteseq = [x for x in range(0x100)]
doublebyteseq = [x for x in range(0x10000)]
quadbyteseq = [
    0x00000000,
    0x000000FF,
    0x0000FF00,
    0x0000FFFF,
    0x00FF0000,
    0x00FF00FF,
    0x00FFFF00,
    0x00FFFFFF,
    0xFF000000,
    0xFF0000FF,
    0xFF00FF00,
    0xFFFF0000,
    0xFFFF00FF,
    0xFFFFFF00,
    0xFFFFFFFF,
]

singlebytebuf = array.array("B", singlebyteseq)
doublebytebuf = array.array("H", doublebyteseq)
quadbytebuf = array.array("I", quadbyteseq)

USHORT_SIZE = struct.calcsize("H")
UINT_SIZE = struct.calcsize("I")
UBYTE_SIZE = struct.calcsize("B")

def create_16b(seq, offset):
    if sys.byteorder == 'little':
        return (seq[offset] | seq[offset + 1] << 8)
    else:
        return (seq[offset] << 8 | seq[offset + 1])

def create_32b(seq, size, offset):
    if sys.byteorder == 'little':
        if size == 1:
            return (seq[offset] |
                    seq[offset + 1] << 8 |
                    seq[offset + 2] << 16 |
                    seq[offset + 3] << 24)
        elif size == 2:
            return (seq[offset] | seq[offset + 1] << 16)
    else:
        if size == 1:
            return (seq[offset] << 24 |
                    seq[offset + 1] << 16 |
                    seq[offset + 2] << 8 |
                    seq[offset + 3])
        elif size == 2:
            return (seq[offset] << 16 | seq[offset + 1])

def create_64b(seq, size, offset):
    if sys.byteorder == 'little':
        if size == 1:
            return (seq[offset] |
                    seq[offset + 1] << 8 |
                    seq[offset + 2] << 16 |
                    seq[offset + 3] << 24 |
                    seq[offset + 4] << 32 |
                    seq[offset + 5] << 40 |
                    seq[offset + 6] << 48 |
                    seq[offset + 7] << 56)
        elif size == 2:
            return (seq[offset] |
                    seq[offset + 1] << 16 |
                    seq[offset + 2] << 32 |
                    seq[offset + 3] << 48)
        elif size == 4:
            return (seq[offset] | seq[offset + 1] << 32)

    else:
        if size == 1:
            return (seq[offset] << 56 |
                    seq[offset + 1] << 48 |
                    seq[offset + 2] << 40 |
                    seq[offset + 3] << 32 |
                    seq[offset + 4] << 24 |
                    seq[offset + 5] << 16 |
                    seq[offset + 6] << 8 |
                    seq[offset + 7])
        elif size == 2:
            return (seq[offset] << 48 |
                    seq[offset + 1] << 32 |
                    seq[offset + 2] << 16 |
                    seq[offset + 3])
        elif size == 4:
            return (seq[offset] << 32 | seq[offset + 1])

def lobyte16(val):
    return val & 0x00FF

def hibyte16(val):
    return val >> 8 & 0x00FF

def lobytes32(val):
    return val & 0x0000FFFF

def hibytes32(val):
    return val >> 16 & 0x0000FFFF

def ltrbyte32(val, pos):
    if sys.byteorder == 'little':
        if pos == 0:
            return val & 0x000000FF
        elif pos == 1:
            return (val & 0x0000FF00) >> 8
        elif pos == 2:
            return (val & 0x00FF0000) >> 16
        elif pos == 3:
            return (val & 0xFF000000) >> 24
        else:
            raise IndexError("invalid position")
    else:
        if pos == 3:
            return (val & 0x000000FF)
        elif pos == 2:
            return (val & 0x0000FF00) >> 8
        elif pos == 1:
            return (val & 0x00FF0000) >> 16
        elif pos == 0:
            return (val & 0xFF000000) >> 24
        else:
            raise IndexError("invalid position")


def test_to_ctypes():
    for seq, dtype in (
        (singlebyteseq, ctypes.c_ubyte),
        (singlebytebuf, ctypes.c_ubyte),
        (doublebyteseq, ctypes.c_ushort),
        (doublebytebuf, ctypes.c_ushort),
        (quadbyteseq, ctypes.c_uint),
        (quadbytebuf, ctypes.c_uint),
    ):
        bytebuf, size = sdlextarray.to_ctypes(seq, dtype)
        assert size == len(seq)
        for index, x in enumerate(bytebuf):
            assert x == seq[index]


class TestExtCTypesView(object):
    __tags__ = ["sdl2ext"]

    def test__singlebytes(self):
        buf1 = sdlextarray.CTypesView(singlebyteseq, docopy=True)
        buf2 = sdlextarray.CTypesView(singlebytebuf, docopy=False)
        for singlebytes, shared in ((buf1, False), (buf2, True)):
            assert isinstance(singlebytes, sdlextarray.CTypesView)
            assert singlebytes.is_shared == shared
            assert singlebytes.bytesize == len(singlebyteseq)
            for index, val in enumerate(singlebytes.to_bytes()):
                assert val == singlebyteseq[index]

            offset = 0
            for val in singlebytes.to_uint16():
                seqval = create_16b(singlebyteseq, offset)
                assert val == seqval
                offset += 2

            offset = 0
            for val in singlebytes.to_uint32():
                seqval = create_32b(singlebyteseq, 1, offset)
                assert val == seqval
                offset += 4

            offset = 0
            for val in singlebytes.to_uint64():
                seqval = create_64b(singlebyteseq, 1, offset)
                assert val == seqval
                offset += 8

    def test_doublebytes(self):
        buf1 = sdlextarray.CTypesView(doublebyteseq, USHORT_SIZE, docopy=True)
        buf2 = sdlextarray.CTypesView(doublebytebuf, USHORT_SIZE, docopy=False)
        for singlebytes, shared in ((buf1, False), (buf2, True)):
            assert isinstance(singlebytes, sdlextarray.CTypesView)
            assert singlebytes.is_shared == shared
            assert singlebytes.bytesize == len(doublebyteseq) * 2
            offset = 0
            cnt = 0
            for val in singlebytes.to_bytes():
                hi = hibyte16(doublebyteseq[offset])
                lo = lobyte16(doublebyteseq[offset])
                if cnt > 0:
                    assert val == (lo if BIG_ENDIAN else hi)
                    cnt = 0
                    offset += 1
                else:
                    assert val == (hi if BIG_ENDIAN else lo)
                    cnt += 1

            offset = 0
            for val in singlebytes.to_uint16():
                assert val == doublebyteseq[offset]
                offset += 1

            offset = 0
            for val in singlebytes.to_uint32():
                seqval = create_32b(doublebyteseq, 2, offset)
                assert val == seqval
                offset += 2

            offset = 0
            for val in singlebytes.to_uint64():
                seqval = create_64b(doublebyteseq, 2, offset)
                assert val == seqval
                offset += 4

    def test_quadbytes(self):
        buf1 = sdlextarray.CTypesView(quadbyteseq, UINT_SIZE, docopy=True)
        buf2 = sdlextarray.CTypesView(quadbytebuf, UINT_SIZE, docopy=False)
        for singlebytes, shared in ((buf1, False), (buf2, True)):
            assert isinstance(singlebytes, sdlextarray.CTypesView)
            assert singlebytes.is_shared == shared
            assert singlebytes.bytesize == len(quadbyteseq) * 4
            offset = 0
            cnt = 0
            for val in singlebytes.to_bytes():
                assert val == ltrbyte32(quadbyteseq[offset], cnt)
                if cnt == 3:
                    offset += 1
                    cnt = 0
                else:
                    cnt += 1

            cnt = 0
            offset = 0
            for val in singlebytes.to_uint16():
                hi = hibytes32(quadbyteseq[offset])
                lo = lobytes32(quadbyteseq[offset])
                if cnt > 0:
                    assert val == (lo if BIG_ENDIAN else hi)
                    cnt = 0
                    offset += 1
                else:
                    assert val == (hi if BIG_ENDIAN else lo)
                    cnt += 1

            offset = 0
            for val in singlebytes.to_uint32():
                assert val == quadbyteseq[offset]
                offset += 1

            offset = 0
            for val in singlebytes.to_uint64():
                seqval = create_64b(quadbyteseq, 4, offset)
                assert val == seqval
                offset += 2

    def test___repr__(self):
        seqs = (
            (singlebyteseq, UBYTE_SIZE, 1, False),
            (doublebyteseq, USHORT_SIZE, 2, False),
            (quadbyteseq, UINT_SIZE, 4, False),
            (singlebytebuf, UBYTE_SIZE, 1, True),
            (doublebytebuf, USHORT_SIZE, 2, True),
            (quadbytebuf, UINT_SIZE, 4, True),
        )
        for seq, size, factor, shared in seqs:
            buf = sdlextarray.CTypesView(seq, size, not shared)
            otype = type(seq).__name__
            if not shared:
                otype = 'array'
            text = "CTypesView(type=%s, bytesize=%d, shared=%s)" % \
                (otype, len(seq) * factor, shared)
            assert text == repr(buf)


class TestExtMemoryView(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        with pytest.raises(TypeError):
            sdlextarray.MemoryView(5, 1, (1,))
        with pytest.raises(TypeError):
            sdlextarray.MemoryView(None, 1, (1,))

        source = "Example buffer"
        view = sdlextarray.MemoryView(source, 1, (len(source),))
        for index, val in enumerate(view):
            assert val == source[index]

        # Test negative indexing support
        assert view[-1] == "r"
        assert view[-3] == "f"

        view = sdlextarray.MemoryView(source, 1, (2, 7))
        word1 = view[0]  # "Example"
        word2 = view[1]  # " buffer"
        assert len(view) == 2
        assert len(word1) == 7
        assert len(word2) == 7
        for index, val in enumerate(word1):
            assert val == source[index]
        for index, val in enumerate(word2):
            assert val == source[index + 7]
        # TODO: more tests

        # Test exceptions on bad input
        with pytest.raises(IndexError):
            view[1:5]
        with pytest.raises(IndexError):
            view[10]

    def test_ndim_strides(self):
        source = "Example buffer"
        view = sdlextarray.MemoryView(source, 1, (len(source),))
        assert view.ndim == 1
        assert view.strides == (len(source),)
        view = sdlextarray.MemoryView(source, 1, (2, 7))
        assert view.ndim == 2
        assert view.strides == (2, 7)
        view = sdlextarray.MemoryView(source, 1, (7, 2))
        assert view.ndim == 2
        assert view.strides == (7, 2)
        view = sdlextarray.MemoryView(source, 1, (2, 2, 2))
        assert view.ndim == 3
        assert view.strides == (2, 2, 2)

    def test_itemsize(self):
        source = "Example buffer"
        view = sdlextarray.MemoryView(source, 1, (len(source),))
        assert view.itemsize == 1
        view = sdlextarray.MemoryView(source, 7, (1, 7))
        assert view.itemsize == 7

    def test_size(self):
        source = "Example buffer"
        view = sdlextarray.MemoryView(source, 1, (len(source),))
        assert view.size == len(source)
        view = sdlextarray.MemoryView(source, 7, (1, 7))
        assert view.size == len(source)

    def test_source(self):
        source = "Example buffer"
        view = sdlextarray.MemoryView(source, 1, (len(source),))
        assert view.source == source


def test_to_tuple():
    ar = (ctypes.c_int * 20)()
    for i in range(20):
        ar[i] = i
    vtuple = sdlextarray.to_tuple(ar)
    assert isinstance(vtuple, tuple)
    for index, value in enumerate(vtuple):
        assert value == ar[index]

def test_to_list():
    ar = (ctypes.c_int * 20)()
    for i in range(20):
        ar[i] = i
    vlist = sdlextarray.to_list(ar)
    assert isinstance(vlist, list)
    for index, value in enumerate(vlist):
        assert value == ar[index]

def test_create_array():
    barr = bytes(bytearray(singlebyteseq))
    for i in (1, 2, 4, 8):
        parr = sdlextarray.create_array(barr, i)
        assert isinstance(parr, array.array)
        if i == 1:
            assert parr[0] == 0x0
        elif i == 2:
            assert parr[0] == struct.unpack("=H", barr[0:2])[0]
        elif i == 4:
            assert parr[0] == struct.unpack("=I", barr[0:4])[0]
    for i in (0, 3, 5, 6, 7, 9, 10, 12, "test"):
        with pytest.raises(TypeError):
            sdlextarray.create_array(barr, i)
