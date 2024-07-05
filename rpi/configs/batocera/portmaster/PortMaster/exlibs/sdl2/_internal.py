import warnings
from ctypes import POINTER, cast, addressof


# Defines a type of dict that allows getting (but not setting) keys as attributes
class AttributeDict(dict):
    def __getattr__(self, key):
        return self[key]


# Gets a usable pointer from an SDL2 ctypes object
def get_pointer(ctypes_obj):
    pointer_type = POINTER(type(ctypes_obj))
    return cast(addressof(ctypes_obj), pointer_type)


# Prints warning without stack or line info
def prettywarn(msg, warntype):
    """Prints a suppressable warning without stack or line info."""
    original = warnings.formatwarning
    def _pretty_fmt(message, category, filename, lineno, line=None):
        return "{0}: {1}\n".format(category.__name__, message)
    warnings.formatwarning = _pretty_fmt
    warnings.warn(msg, warntype)
    warnings.formatwarning = original
