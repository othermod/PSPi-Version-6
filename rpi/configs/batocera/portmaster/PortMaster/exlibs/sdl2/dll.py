from __future__ import absolute_import
import os
import sys
import warnings
from platform import machine as cpu_arch
from ctypes import CDLL, POINTER, Structure, c_uint8, cast, addressof
from ctypes.util import find_library
from ._internal import AttributeDict, prettywarn, get_pointer

__all__ = ["DLL", "nullfunc"]


# Use DLLs from pysdl2-dll, if installed and DLL path not explicitly set
try:
    prepath = os.getenv('PYSDL2_DLL_PATH')
    import sdl2dll
    postpath = os.getenv('PYSDL2_DLL_PATH')
    if prepath != postpath:
        msg = "Using SDL2 binaries from pysdl2-dll {0}"
        vstr = sdl2dll.__version__
        prettywarn(msg.format(vstr), UserWarning)
        # Warn if on Apple Silicon and pysdl2-dll isn't fully native
        vernum = tuple([int(i) for i in vstr.split(".")[:3]])
        need_update = vernum <= (2, 0, 22) and "post" not in vstr
        if sys.platform == "darwin" and cpu_arch() == "arm64" and need_update:
            msg = "The installed version of pysdl2-dll does not fully support\n"
            msg += "Apple Silicon. Please update to the latest version for "
            msg += "full compatibility."
            prettywarn(msg.format(sdl2dll.__version__), UserWarning)

except ImportError:
    pass


# Wrapper functions for handling calls to missing or unsupported functions

def nullfunc(*args):
    """A simple no-op function to be used as dll replacement."""
    return

def _unavailable(err):
    """A wrapper that raises a RuntimeError if a function is not supported."""
    def wrapper(*fargs, **kw):
        raise RuntimeError(err)
    return wrapper

def _nonexistent(funcname, func):
    """A simple wrapper to mark functions and methods as nonexistent."""
    def wrapper(*fargs, **kw):
        warnings.warn("%s does not exist" % funcname,
                      category=RuntimeWarning, stacklevel=2)
        return func(*fargs, **kw)
    wrapper.__name__ = func.__name__
    return wrapper


# Functions and structures for working with library version numbers

class SDL_version(Structure):
    # NOTE: defined here so library versions can be detected on load
    _fields_ = [
        ("major", c_uint8),
        ("minor", c_uint8),
        ("patch", c_uint8),
    ]

def _version_tuple_to_int(v):
    # Convert a tuple to an integer (e.g. (2,0,18) to 2018, (2,24,1) to 2241)
    if v[1] > 99:
        # Cap the minor version at 99 to avoid ambiguity: in practice
        # the version number is unlikely to reach 2.99.z.
        return v[0] * 1000 + 999
    elif v[1] > 0:
        # For SDL2 >= 2.23.0 (new version scheme): 2.23.0 -> 2230
        # Note that this is not the same encoding as SDL_VERSIONNUM.
        # Cap the micro version at 9 to avoid ambiguity: we're unlikely
        # to need to distinguish between 2.y.9 and 2.y.10, since those
        # would be patch/bugfix releases from the same branch anyway.
        return v[0] * 1000 + v[1] * 10 + min(v[2], 9)
    else:
        # For SDL2 <= 2.0.22 (old version scheme): 2.0.22 -> 2022
        # This is the same encoding as SDL_VERSIONNUM.
        return v[0] * 1000 + v[1] * 100 + v[2]

def _version_tuple_to_str(v):
    return ".".join(map(str, v))

def _version_str_to_tuple(s):
    return tuple(map(int, s.split('.')))

def _so_version_num(libname):
    """Extracts the version number from an .so filename as a list of ints."""
    return list(map(int, libname.split('.so.')[1].split('.')))



# Functions for allowing Microsoft Store Python to load image/ttf/mixer

def _using_ms_store_python():
    """Checks if the Python interpreter was installed from the Microsoft Store."""
    return 'WindowsApps\\PythonSoftwareFoundation.' in sys.executable


def _preload_deps(libname, dllpath):
    """Preloads all DLLs that SDL2 and its extensions link to (e.g. libFLAC).
    
    This is required for Python installed from the Microsoft Store, which has
    strict DLL loading rules but will allow loading of DLLs that have already
    been loaded by the current process.
    """
    deps = {
        "SDL2": [],
        "SDL2_ttf": ["freetype"],
        "SDL2_image": ["zlib", "jpeg", "png16", "tiff", "webp"],
        "SDL2_mixer": ["modplug", "mpg123", "ogg", "vorbis", "vorbisfile",
                       "opus", "opusfile", "FLAC"],
        "SDL2_gfx": []
    }
    preloaded = {}
    dlldir = os.path.abspath(os.path.join(dllpath, os.pardir))
    all_dlls = [f for f in os.listdir(dlldir) if f.split(".")[-1] == "dll"]
    for name in deps[libname]:
        dllname = name if name == "zlib" else "lib{0}-".format(name)
        for dll in all_dlls:
            if dll.startswith(dllname):
                try:
                    filepath = os.path.join(dlldir, dll)
                    preloaded[name] = CDLL(filepath)
                except OSError:
                    pass
                break

    if len(preloaded) < len(deps[libname]):
        e = ("Unable to preload all dependencies for {0}. This module may not "
            "work correctly.")
        prettywarn(e.format(libname), RuntimeWarning)

    return preloaded


# Functions for finding SDL libraries within a set of given paths

def _finds_libs_at_path(libnames, path, patterns):
    """Find libraries matching a given name (e.g. SDL2) in a specific path.
    """
    # Adding the potential 'd' suffix that is present on the library
    # when built in debug configuration
    searchfor = libnames + [libname + 'd' for libname in libnames]
    results = []

    # First, find any libraries matching pattern exactly within given path
    for libname in searchfor:
        for subpath in str.split(path, os.pathsep):
            for pattern in patterns:
                dllfile = os.path.join(subpath, pattern.format(libname))
                if os.path.exists(dllfile):
                    results.append(dllfile)

    # Next, on Linux and similar, find any libraries with version suffixes matching
    # pattern (e.g. libSDL2.so.2) at path and add them in descending version order
    # (i.e. newest first)
    if sys.platform not in ("win32", "darwin"):
        versioned = []
        files = os.listdir(path)
        for f in files:
            for libname in searchfor:
                dllname = "lib{0}.so".format(libname)
                if dllname in f and not (dllname == f or f.startswith(".")):
                    versioned.append(os.path.join(path, f))
        versioned.sort(key = _so_version_num, reverse = True)
        results = results + versioned

    return results


def _findlib(libnames, path=None):
    """Find libraries with a given name and return their paths in a list.

    If a path is specified, libraries found in that directory will take precedence,
    with libraries found in system search paths following.

    """

    platform = sys.platform
    if platform == "win32":
        patterns = ["{0}.dll"]
    elif platform == "darwin":
        patterns = ["lib{0}.dylib", "{0}.framework/{0}", "{0}.framework/Versions/A/{0}"]
    else:
        patterns = ["lib{0}.so"]

    # Adding the potential 'd' suffix that is present on the library
    # when built in debug configuration
    searchfor = libnames + [libname + 'd' for libname in libnames]

    # First, find any matching libraries at the given path (if specified)
    results = []
    if path and path.lower() != "system":
        results = _finds_libs_at_path(libnames, path, patterns)

    # Next, search for library in system library search paths
    for libname in searchfor:
        dllfile = find_library(libname)
        if dllfile:
            # For Python 3.8+ on Windows, need to specify relative or full path
            if os.name == "nt" and not ("/" in dllfile or "\\" in dllfile):
                dllfile = "./" + dllfile
            results.append(dllfile)

    # On ARM64 Macs, search the non-standard brew library path as a fallback
    arm_brewpath = "/opt/Homebrew/lib"
    is_apple_silicon = platform == "darwin" and cpu_arch() == "arm64"
    if is_apple_silicon and os.path.exists(arm_brewpath):
        results += _finds_libs_at_path(libnames, arm_brewpath, patterns)

    return results


# Classes for loading libraries and binding ctypes functions

class SDLFunc(object):
    # A container class for SDL ctypes function definitions
    def __init__(self, name, args=None, returns=None, added=None):
        self.name = name
        self.args = args
        self.returns = returns
        self.added = added


class DLLWarning(Warning):
    pass


class DLL(object):
    """Function wrapper around the different DLL functions. Do not use or
    instantiate this one directly from your user code.
    """
    def __init__(self, libinfo, libnames, path=None):
        self._dll = None
        self._deps = None
        self._libname = libinfo
        self._version = None
        minversions = {
            "SDL2": (2, 0, 5),
            "SDL2_mixer": (2, 0, 1),
            "SDL2_ttf": (2, 0, 14),
            "SDL2_image": (2, 0, 1),
            "SDL2_gfx": (1, 0, 3)
        }
        foundlibs = _findlib(libnames, path)
        dllmsg = "PYSDL2_DLL_PATH: %s" % (os.getenv("PYSDL2_DLL_PATH") or "unset")
        if len(foundlibs) == 0:
            raise RuntimeError("could not find any library for %s (%s)" %
                               (libinfo, dllmsg))
        for libfile in foundlibs:
            try:
                self._dll = CDLL(libfile)
                self._libfile = libfile
                self._version_tuple = self._get_version_tuple(libinfo, self._dll)
                if self._version_tuple < minversions[libinfo]:
                    versionstr = _version_tuple_to_str(self._version_tuple)
                    minimumstr = _version_tuple_to_str(minversions[libinfo])
                    err = "{0} (v{1}) is too old to be used by py-sdl2"
                    err += " (minimum v{0})".format(minimumstr)
                    raise RuntimeError(err.format(libfile, versionstr))
                break
            except Exception as exc:
                # Could not load the DLL, move to the next, but inform the user
                # about something weird going on - this may become noisy, but
                # is better than confusing the users with the RuntimeError below
                self._dll = None

                warnings.warn(repr(exc), DLLWarning)
        if self._dll is None:
            raise RuntimeError("found %s, but it's not usable for the library %s" %
                               (foundlibs, libinfo))
        if _using_ms_store_python():
            self._deps = _preload_deps(libinfo, self._libfile)
        if path is not None and sys.platform in ("win32",) and \
            path in self._libfile:
            os.environ["PATH"] = "%s;%s" % (path, os.environ["PATH"])

    def bind_function(self, funcname, args=None, returns=None, added=None):
        """Binds the passed argument and return value types to the specified
        function. If the version of the loaded library is older than the
        version where the function was added, an informative exception will
        be raised if the bound function is called.
        
        Args:
            funcname (str): The name of the function to bind.
            args (List or None, optional): The data types of the C function's 
                arguments. Should be 'None' if function takes no arguments.
            returns (optional): The return type of the bound C function. Should
                be 'None' if function returns 'void'.
            added (str, optional): The version of the library in which the
                function was added, in the format '2.x.x'.
        """
        func = getattr(self._dll, funcname, None)
        min_version = _version_str_to_tuple(added) if added else None
        if not func:
            versionstr = _version_tuple_to_str(self._version_tuple)
            if min_version and min_version > self._version_tuple:
                e = "'{0}' requires {1} <= {2}, but the loaded version is {3}."
                errmsg = e.format(funcname, self._libname, added, versionstr)
                return _unavailable(errmsg)
            else:
                e = "Could not find function '%s' in %s (%s)"
                libver = self._libname + ' ' + versionstr
                raise ValueError(e % (funcname, self._libfile, libver))
        func.argtypes = args
        func.restype = returns
        return func

    def _get_version_tuple(self, libname, dll):
        """Gets the version of the linked SDL library"""
        if libname == "SDL2":
            dll.SDL_GetVersion.argtypes = [POINTER(SDL_version)]
            v = SDL_version()
            dll.SDL_GetVersion(v)
        else:
            if libname == "SDL2_mixer":
                func = dll.Mix_Linked_Version
            elif libname == "SDL2_ttf":
                func = dll.TTF_Linked_Version
            elif libname == "SDL2_image":
                func = dll.IMG_Linked_Version
            elif libname == "SDL2_gfx":
                return (1, 0, 4) # not supported in SDL2_gfx, so just assume latest
            func.argtypes = None
            func.restype = POINTER(SDL_version)
            v = func().contents

        return (v.major, v.minor, v.patch)

    @property
    def libfile(self):
        """str: The filename of the loaded library."""
        return self._libfile

    @property
    def version_tuple(self):
        """tuple: The version of the loaded library in the form of a
        tuple of integers (e.g. (2, 24, 1) for SDL 2.24.1).
        """
        return self._version_tuple

    @property
    def version(self):
        """int: The version of the loaded library in the form of a 4-digit
        integer (e.g. '2008' for SDL 2.0.8, '2231' for SDL 2.23.1).

        Note that this is not the same version encoding as SDL_VERSIONNUM,
        and the exact encoding used is not guaranteed.
        In new code, use version_tuple instead.
        """
        return _version_tuple_to_int(self._version_tuple)


# Once the DLL class is defined, try loading the main SDL2 library

try:
    dll = DLL("SDL2", ["SDL2", "SDL2-2.0", "SDL2-2.0.0"], os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)

def get_dll_file():
    """Gets the file name of the loaded SDL2 library."""
    return dll.libfile

_bind = dll.bind_function
version = dll.version
version_tuple = dll.version_tuple
