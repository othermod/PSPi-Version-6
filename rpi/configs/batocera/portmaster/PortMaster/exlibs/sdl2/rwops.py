import io
import sys
from ctypes import (
    c_int, c_size_t, c_void_p, c_char_p, memmove, string_at, CFUNCTYPE,
    Structure, Union, _Pointer
)
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict, version
from .stdinc import Sint64, Uint8, Uint16, Uint32, Uint64, SDL_bool

__all__ = [
    # Structs
    "SDL_RWops",

    # Defines
    "SDL_RWOPS_UNKNOWN", "SDL_RWOPS_WINFILE", "SDL_RWOPS_STDFILE",
    "SDL_RWOPS_JNIFILE", "SDL_RWOPS_MEMORY", "SDL_RWOPS_MEMORY_RO",
    "RW_SEEK_SET", "RW_SEEK_CUR", "RW_SEEK_END",
    
    # Python Functions
    "rw_from_object",
]

def _ptr2obj(ptr):
    """If a pointer, returns its contents. Otherwise, returns the passed object.
    """
    if isinstance(ptr, _Pointer):
        return ptr.contents
    return ptr


# Constants & enums

SDL_RWOPS_UNKNOWN = 0
SDL_RWOPS_WINFILE = 1
SDL_RWOPS_STDFILE = 2
SDL_RWOPS_JNIFILE = 3
SDL_RWOPS_MEMORY = 4
SDL_RWOPS_MEMORY_RO = 5

RW_SEEK_SET = 0
RW_SEEK_CUR = 1
RW_SEEK_END = 2


# Structs & opaque typedefs

class _hidden(Union):
    pass

class SDL_RWops(Structure):
    pass

_sdlsize = CFUNCTYPE(Sint64, _P(SDL_RWops))
_sdlseek = CFUNCTYPE(Sint64, _P(SDL_RWops), Sint64, c_int)
_sdlread = CFUNCTYPE(c_size_t, _P(SDL_RWops), c_void_p, c_size_t, c_size_t)
_sdlwrite = CFUNCTYPE(c_size_t, _P(SDL_RWops), c_void_p, c_size_t, c_size_t)
_sdlclose = CFUNCTYPE(c_int, _P(SDL_RWops))
SDL_RWops._fields_ = [
    ("size", _sdlsize),
    ("seek", _sdlseek),
    ("read", _sdlread),
    ("write", _sdlwrite),
    ("close", _sdlclose),
    ("type", Uint32),
    ("hidden", _hidden),
]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_RWFromFile", [c_char_p, c_char_p], _P(SDL_RWops)),
    SDLFunc("SDL_RWFromFP", [c_void_p, SDL_bool], _P(SDL_RWops)),
    SDLFunc("SDL_RWFromMem", [c_void_p, c_int], _P(SDL_RWops)),
    SDLFunc("SDL_RWFromConstMem", [c_void_p, c_int], _P(SDL_RWops)),
    SDLFunc("SDL_AllocRW", None, _P(SDL_RWops)),
    SDLFunc("SDL_FreeRW", [_P(SDL_RWops)]),
    SDLFunc("SDL_LoadFile_RW", [_P(SDL_RWops), _P(c_size_t), c_int], c_void_p, added='2.0.6'),
    SDLFunc("SDL_LoadFile", [c_char_p, _P(c_size_t)], c_void_p, added='2.0.10'),
    SDLFunc("SDL_RWsize", [_P(SDL_RWops)], Sint64, added='2.0.10'),
    SDLFunc("SDL_RWseek", [_P(SDL_RWops), Sint64, c_int], Sint64, added='2.0.10'),
    SDLFunc("SDL_RWtell", [_P(SDL_RWops)], Sint64, added='2.0.10'),
    SDLFunc("SDL_RWread", [_P(SDL_RWops), c_void_p, c_size_t, c_size_t], c_size_t, added='2.0.10'),
    SDLFunc("SDL_RWwrite",
        [_P(SDL_RWops), c_void_p, c_size_t, c_size_t],
        returns = c_size_t, added = '2.0.10'
    ),
    SDLFunc("SDL_RWclose", [_P(SDL_RWops)], c_int, added='2.0.10'),
    SDLFunc("SDL_ReadU8", [_P(SDL_RWops)], Uint8),
    SDLFunc("SDL_ReadLE16", [_P(SDL_RWops)], Uint16),
    SDLFunc("SDL_ReadBE16", [_P(SDL_RWops)], Uint16),
    SDLFunc("SDL_ReadLE32", [_P(SDL_RWops)], Uint32),
    SDLFunc("SDL_ReadBE32", [_P(SDL_RWops)], Uint32),
    SDLFunc("SDL_ReadLE64", [_P(SDL_RWops)], Uint64),
    SDLFunc("SDL_ReadBE64", [_P(SDL_RWops)], Uint64),
    SDLFunc("SDL_WriteU8", [_P(SDL_RWops), Uint8], c_size_t),
    SDLFunc("SDL_WriteLE16", [_P(SDL_RWops), Uint16], c_size_t),
    SDLFunc("SDL_WriteBE16", [_P(SDL_RWops), Uint16], c_size_t),
    SDLFunc("SDL_WriteLE32", [_P(SDL_RWops), Uint32], c_size_t),
    SDLFunc("SDL_WriteBE32", [_P(SDL_RWops), Uint32], c_size_t),
    SDLFunc("SDL_WriteLE64", [_P(SDL_RWops), Uint64], c_size_t),
    SDLFunc("SDL_WriteBE64", [_P(SDL_RWops), Uint64], c_size_t),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_RWFromFile = _ctypes["SDL_RWFromFile"]
SDL_RWFromFP = _ctypes["SDL_RWFromFP"]
SDL_RWFromMem = _ctypes["SDL_RWFromMem"]
SDL_RWFromConstMem = _ctypes["SDL_RWFromConstMem"]
SDL_AllocRW = _ctypes["SDL_AllocRW"]
SDL_FreeRW = _ctypes["SDL_FreeRW"]

SDL_LoadFile_RW = _ctypes["SDL_LoadFile_RW"]
# SDL_LoadFile was a macro in SDL <= 2.0.9, added as a function in 2.0.10
if version >= 2010:
    SDL_LoadFile = _ctypes["SDL_LoadFile"]
else:
    SDL_LoadFile = lambda fname, ds: SDL_LoadFile_RW(SDL_RWFromFile(fname, b"rb"), ds, 1)

# The following set of functions were macros in SDL <= 2.0.9 but became full
# functions in SDL 2.0.10. Lambda functions are to mimic macro behaviour with
# earlier SDL2 versions.
if version >= 2010:
    SDL_RWsize = _ctypes["SDL_RWsize"]
    SDL_RWseek = _ctypes["SDL_RWseek"]
    SDL_RWtell = _ctypes["SDL_RWtell"]
    SDL_RWread = _ctypes["SDL_RWread"]
    SDL_RWwrite = _ctypes["SDL_RWwrite"]
    SDL_RWclose = _ctypes["SDL_RWclose"]
else:
    _po = _ptr2obj # allow pointers to be passed directly to these functions
    SDL_RWsize = lambda ctx: _po(ctx).size(_po(ctx))
    SDL_RWseek = lambda ctx, offset, whence: _po(ctx).seek(_po(ctx), offset, whence)
    SDL_RWtell = lambda ctx: _po(ctx).seek(_po(ctx), 0, RW_SEEK_CUR)
    SDL_RWread = lambda ctx, ptr, size, n: _po(ctx).read(_po(ctx), ptr, size, n)
    SDL_RWwrite = lambda ctx, ptr, size, n: _po(ctx).write(_po(ctx), ptr, size, n)
    SDL_RWclose = lambda ctx: _po(ctx).close(_po(ctx))

SDL_ReadU8 = _ctypes["SDL_ReadU8"]
SDL_ReadLE16 = _ctypes["SDL_ReadLE16"]
SDL_ReadBE16 = _ctypes["SDL_ReadBE16"]
SDL_ReadLE32 = _ctypes["SDL_ReadLE32"]
SDL_ReadBE32 = _ctypes["SDL_ReadBE32"]
SDL_ReadLE64 = _ctypes["SDL_ReadLE64"]
SDL_ReadBE64 = _ctypes["SDL_ReadBE64"]

SDL_WriteU8 = _ctypes["SDL_WriteU8"]
SDL_WriteLE16 = _ctypes["SDL_WriteLE16"]
SDL_WriteBE16 = _ctypes["SDL_WriteBE16"]
SDL_WriteLE32 = _ctypes["SDL_WriteLE32"]
SDL_WriteBE32 = _ctypes["SDL_WriteBE32"]
SDL_WriteLE64 = _ctypes["SDL_WriteLE64"]
SDL_WriteBE64 = _ctypes["SDL_WriteBE64"]


# Additional Python functions (move to ext?)

if sys.version_info[0] >= 3:
    try:
	    from collections.abc import Callable
    except ImportError:
	    from collections import Callable
    callable = lambda x: isinstance(x, Callable)

def rw_from_object(obj):
    """Creats a SDL_RWops from any Python object.

    The Python object must at least support the following methods:

        read(length) -> data
            length is the size in bytes to be read. A call to len(data) must
            return the correct amount of bytes for the data, so that
            len(data) / [size in bytes for a single element from data] returns
            the amount of elements.
            Must raise an error on failure.

        seek(offset, whence) -> int
            offset denotes the offset to move the read/write pointer of the
            object to. whence indicates the movement behaviour and can be one
            of the following values:
                RW_SEEK_SET - move to offset from the start of the file
                RW_SEEK_CUR - move by offset from the relative location
                RW_SEEK_END - move to offset from the end of the file
            If it could not move read/write pointer to the desired location,
            an error must be raised.

        tell() -> int
            Must return the current offset. This method must only be
            provided, if seek() does not return any value.

        close() -> None
            Closes the object(or its internal data access methods). Must raise
            an error on failure.

        write(data) -> None
            Writes the passed data(which is a string of bytes) to the object.
            Must raise an error on failure.

        Note: The write() method is optional and only necessary, if the passed
        object should be able to write data.

    .. note:: Under Python 2.7, file objects created with ``open()`` can have
              problems with certain functions in newer versions of SDL2. If
              you encounter any issues, try using ``io.open()`` instead.

    The returned SDL_RWops is a pure Python object and must not be freed via
    free_rw().

    """
    if not hasattr(obj, "read"):
        raise TypeError("obj must have a read(len) -> data method")
    if not hasattr(obj, "seek") or not callable(obj.seek):
        raise TypeError("obj must have a seek(offset, whence) method")
    if not hasattr(obj, "close") or not callable(obj.close):
        raise TypeError("obj must have a close() -> int method")

    rwops = SDL_RWops()

    def _rwsize(context):
        try:
            if hasattr(obj, "size"):
                if callable(obj.size):
                    return obj.size()
                else:
                    return obj.size
            else:
                cur = obj.seek(0, RW_SEEK_CUR)
                length = obj.seek(0, RW_SEEK_END)
                obj.seek(cur, RW_SEEK_SET)
                return length
        except Exception:
            #print(e)
            return -1
    rwops.size = _sdlsize(_rwsize)

    def _rwseek(context, offset, whence):
        try:
            retval = obj.seek(offset, whence)
            if retval is None:
                retval = obj.tell()
            return retval
        except Exception:
            #print(e)
            return -1
    rwops.seek = _sdlseek(_rwseek)

    def _rwread(context, ptr, size, maxnum):
        try:
            data = obj.read(size * maxnum)
            num = len(data)
            memmove(ptr, data, num)
            return num // size
        except Exception:
            #print(e)
            return 0
    rwops.read = _sdlread(_rwread)

    def _rwclose(context):
        try:
            retval = obj.close()
            if retval is None:
                # No return value; we assume that everything is okay.
                return 0
            return retval
        except Exception:
            #print(e)
            return -1
    rwops.close = _sdlclose(_rwclose)

    def _rwwrite(context, ptr, size, num):
        try:
            # string_at feels wrong, since we access a raw byte buffer...
            retval = obj.write(string_at(ptr, size * num))
            if issubclass(type(obj), io.IOBase):
                if retval is None: # Means write error
                    return 0
                return retval // size
            # If not an io object, try to interpret retval as bytes written
            # and, failing that, just assume success if no exception raised
            # and return num
            try:
                return int(retval) // size
            except TypeError:
                return num
        except Exception:
            #print(e)
            return 0

    if hasattr(obj, "write") and callable(obj.write):
        rwops.write = _sdlwrite(_rwwrite)
    else:
        rwops.write = _sdlwrite()
    return rwops
