import sys
import warnings
try:
	from collections.abc import Callable, Iterable
except ImportError:
	from collections import Callable, Iterable

__all__ = ["ISPYTHON2", "ISPYTHON3", "utf8", "stringify", "byteify",
           "isiterable", "platform_is_64bit", "deprecated", "deprecation",
           "UnsupportedError", "ExperimentalWarning", "experimental",
           ]

ISPYTHON2 = False
ISPYTHON3 = False

if sys.version_info[0] < 3:
    ISPYTHON2 = True
else:
    __all__ += ["long", "unichr", "callable", "unicode"]
    ISPYTHON3 = True
    long = int
    unichr = chr
    callable = lambda x: isinstance(x, Callable)
    unicode = str


def _to_unicode(x, enc):
    if ISPYTHON2:
        if type(x) in (str, bytes):
            return x.decode(enc)
        else:
            return unicode(x)
    else:
        if type(x) == bytes:
            return x.decode(enc)
        else:
            return str(x)


def _is_text(x):
    return isinstance(x, (str, bytes, unicode))


def utf8(x):
    """Converts input to a unicode string in a Python 2/3 agnostic manner.

    If a :obj:`bytes` object is passed, it will be decoded as UTF-8. This
    function returns :obj:`unicode` for Python 2 and :obj:`str` for Python 3.

    Args:
        x: Input to convert to a unicode string.

    Returns:
        :obj:`str` on Python 3.x, or :obj:`unicode` on Python 2.7.

    """
    return _to_unicode(x, 'utf-8')


def stringify(x, enc='utf-8'):
    """Converts input to a :obj:`str` in a Python 2/3 agnostic manner.

    If the input is :obj:`unicode` and the Python version is 2.7, the ``enc``
    parameter indicates the encoding to use when converting the input to
    a non-unicode string. If the input is :obj:`bytes` and the Python version
    is 3.x, the ``enc`` parameter indicates the encoding to use to decode the
    input into a unicode string.
    
    Args:
        x: Input to convert to a :obj:`str`.
        enc (str, optional): The encoding type used to encode or decode the
            input, depending on the input type and the major Python version.
            Defaults to UTF-8.

    """
    if ISPYTHON2:
        if type(x) == unicode:
            return x.encode(enc)
        else:
            return str(x)
    else:
        return _to_unicode(x, enc)


def byteify(x, enc='utf-8'):
    """Converts input to :obj:`bytes` in a Python 2/3 agnostic manner.

    If the input is a unicode string, the ``enc`` parameter indicates
    the encoding to use when encoding the input to :obj:`bytes`.
    
    Args:
        x: Input to convert to :obj:`bytes`.
        enc (str, optional): The encoding type used to encode any unicode
            string input. Defaults to UTF-8.

    """
    unicode_str = unicode if ISPYTHON2 else str
    if type(x) == unicode_str:
        return x.encode(enc)
    else:
        return bytes(x)


def isiterable(x):
    """Checks whether the input is a non-string iterable.

    Args:
        x: The object to check for iterability.

    Returns:
        bool: True if the input is a valid iterable, otherwise False.

    """
    return hasattr(x, "__iter__") and not hasattr(x, "upper")


def platform_is_64bit():
    """Checks whether the Python interpreter is 64-bit.
    
    Returns:
        bool: True if running on 64-bit Python, otherwise False.

    """
    return sys.maxsize > 2 ** 32


def deprecated(func):
    # A simple decorator to mark functions and methods as deprecated
    def wrapper(*fargs, **kw):
        warnings.warn("%s is deprecated." % func.__name__,
                      category=DeprecationWarning, stacklevel=2)
        return func(*fargs, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper


def deprecation(message):
    # Prints a deprecation message
    warnings.warn(message, category=DeprecationWarning, stacklevel=2)


class UnsupportedError(RuntimeError):
    # Indicates that a certain class, function or behaviour is not supported
    pass


class ExperimentalWarning(Warning):
    # Indicates that a certain class, function or behaviour is experimental
    def __init__(self, obj, msg=None):
        """Creates a ExperimentalWarning for the specified obj.

        If a message is passed in msg, it will be printed instead of the
        default message.
        """
        super(ExperimentalWarning, self).__init__()
        self.obj = obj
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "%s is in an experimental state." % repr(self.obj)
        return repr(self.msg)


def experimental(func):
    # A simple decorator to mark functions and methods as experimental
    def wrapper(*fargs, **kw):
        warnings.warn("%s" % func.__name__, category=ExperimentalWarning,
                      stacklevel=2)
        return func(*fargs, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper
