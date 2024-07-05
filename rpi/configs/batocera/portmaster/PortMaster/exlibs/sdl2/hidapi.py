from ctypes import (
    c_char_p, c_wchar_p, c_int, c_ubyte, c_ushort, c_size_t, c_void_p, Structure
)
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint32, SDL_bool


__all__ = [
    # Structs
    "SDL_hid_device", "SDL_hid_device_info",
]


# Structs & opaque typedefs

class SDL_hid_device(c_void_p):
    pass

class SDL_hid_device_info(Structure):
    pass

SDL_hid_device_info._fields_ = [
    ("path", c_char_p),
    ("vendor_id", c_ushort),
    ("product_id", c_ushort),
    ("serial_number", c_wchar_p),
    ("release_number", c_ushort),
    ("manufacturer_string", c_wchar_p),
    ("product_string", c_wchar_p),
    ("usage_page", c_ushort),
    ("usage", c_ushort),
    ("interface_number", c_int),
    ("interface_class", c_int),
    ("interface_subclass", c_int),
    ("interface_protocol", c_int),
    ("next", _P(SDL_hid_device_info))
]


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_hid_init", None, c_int, added='2.0.18'),
    SDLFunc("SDL_hid_exit", None, c_int, added='2.0.18'),
    SDLFunc("SDL_hid_device_change_count", None, Uint32, added='2.0.18'),
    SDLFunc("SDL_hid_enumerate", [c_ushort, c_ushort], _P(SDL_hid_device_info), added='2.0.18'),
    SDLFunc("SDL_hid_free_enumeration", [_P(SDL_hid_device_info)], None, added='2.0.18'),
    SDLFunc("SDL_hid_open", [c_ushort, c_ushort, c_wchar_p], _P(SDL_hid_device), added='2.0.18'),
    SDLFunc("SDL_hid_open_path", [c_char_p, c_int], _P(SDL_hid_device), added='2.0.18'),
    # NOTE: not sure if _P(c_ubyte) is right for SDL_hid_write, need to test
    SDLFunc("SDL_hid_write", [_P(SDL_hid_device), _P(c_ubyte), c_size_t], c_int, added='2.0.18'),
    SDLFunc("SDL_hid_read_timeout",
        [_P(SDL_hid_device), _P(c_ubyte), c_size_t, c_int],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_read", [_P(SDL_hid_device), _P(c_ubyte), c_size_t], c_int, added='2.0.18'),
    SDLFunc("SDL_hid_set_nonblocking", [_P(SDL_hid_device), c_int], c_int, added='2.0.18'),
    SDLFunc("SDL_hid_send_feature_report",
        [_P(SDL_hid_device), _P(c_ubyte), c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_get_feature_report",
        [_P(SDL_hid_device), _P(c_ubyte), c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_close", [_P(SDL_hid_device)], None, added='2.0.18'),
    SDLFunc("SDL_hid_get_manufacturer_string",
        [_P(SDL_hid_device), c_wchar_p, c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_get_product_string",
        [_P(SDL_hid_device), c_wchar_p, c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_get_serial_number_string",
        [_P(SDL_hid_device), c_wchar_p, c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_get_indexed_string",
        [_P(SDL_hid_device), c_int, c_wchar_p, c_size_t],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_hid_ble_scan", [SDL_bool], None, added='2.0.18'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_hid_init = _ctypes["SDL_hid_init"]
SDL_hid_exit = _ctypes["SDL_hid_exit"]
SDL_hid_device_change_count = _ctypes["SDL_hid_device_change_count"]
SDL_hid_enumerate = _ctypes["SDL_hid_enumerate"]
SDL_hid_free_enumeration = _ctypes["SDL_hid_free_enumeration"]
SDL_hid_open = _ctypes["SDL_hid_open"]
SDL_hid_open_path = _ctypes["SDL_hid_open_path"]

SDL_hid_write = _ctypes["SDL_hid_write"]
SDL_hid_read_timeout = _ctypes["SDL_hid_read_timeout"]
SDL_hid_read = _ctypes["SDL_hid_read"]

SDL_hid_set_nonblocking = _ctypes["SDL_hid_set_nonblocking"]
SDL_hid_send_feature_report = _ctypes["SDL_hid_send_feature_report"]
SDL_hid_get_feature_report = _ctypes["SDL_hid_get_feature_report"]
SDL_hid_close = _ctypes["SDL_hid_close"]
SDL_hid_get_manufacturer_string = _ctypes["SDL_hid_get_manufacturer_string"]
SDL_hid_get_product_string = _ctypes["SDL_hid_get_product_string"]
SDL_hid_get_serial_number_string = _ctypes["SDL_hid_get_serial_number_string"]
SDL_hid_get_indexed_string = _ctypes["SDL_hid_get_indexed_string"]
SDL_hid_ble_scan = _ctypes["SDL_hid_ble_scan"]
