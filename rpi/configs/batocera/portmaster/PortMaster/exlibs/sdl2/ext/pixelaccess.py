import ctypes
from .compat import UnsupportedError, experimental
from .array import MemoryView
from ..surface import SDL_MUSTLOCK, SDL_LockSurface, SDL_UnlockSurface, \
    SDL_Surface
from ..stdinc import Uint8
from .draw import prepare_color
from .sprite import SoftwareSprite
from .surface import _get_target_surface

try:
    import numpy
    _HASNUMPY = True
except ImportError:
    _HASNUMPY = False


__all__ = [
    "PixelView", "SurfaceArray", "pixels2d", "pixels3d", "surface_to_ndarray"
]

class PixelView(MemoryView):
    """A 2D memory view for reading and writing SDL surface pixels.

    This class uses a ``view[y][x]`` layout, with the y-axis as the first
    dimension and the x-axis as the second. ``PixelView`` objects currently do
    not support array slicing, but support negative indexing as of
    PySDL2 0.9.10.

    If the source surface is RLE-accelerated, it will be locked automatically
    when the view is created and you will need to re-lock the surface using
    :func:`SDL_UnlockSurface` once you are done with the view.

    .. warning::
       The source surface should not be freed or deleted until the view is no
       longer needed. Accessing the view for a freed surface will likely cause
       Python to hard-crash.

    .. note:: 
       This class is implemented on top of the :class:`~sdl2.ext.MemoryView`
       class. As such, it makes heavy use of recursion to access rows and
       will generally be much slower than the :mod:`numpy`-based
       :func:`~sdl2.ext.pixels2d` and :func:`~sdl2.ext.pixels3d` functions.

    Args:
        source (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            SDL surface to access with the view.

    """
    def __init__(self, source):
        if isinstance(source, SoftwareSprite):
            self._surface = source.surface
            # keep a reference, so the Sprite's not GC'd
            self._sprite = source
        elif isinstance(source, SDL_Surface):
            self._surface = source
        elif "SDL_Surface" in str(type(source)):
            self._surface = source.contents
        else:
            raise TypeError("source must be a Sprite or SDL_Surface")

        itemsize = self._surface.format.contents.BytesPerPixel
        if itemsize == 3:
            e = "Cannot open a 3 bytes-per-pixel surface using a PixelView."
            raise RuntimeError(e)

        if SDL_MUSTLOCK(self._surface):
            SDL_LockSurface(self._surface)

        pxbuf = ctypes.cast(self._surface.pixels, ctypes.POINTER(Uint8))
        strides = (self._surface.h, self._surface.w)
        srcsize = self._surface.h * self._surface.pitch
        super(PixelView, self).__init__(pxbuf, itemsize, strides,
                                        getfunc=self._getitem,
                                        setfunc=self._setitem,
                                        srcsize=srcsize)

    def _getitem(self, start, end):
        if self.itemsize == 1:
            # byte-wise access
            return self.source[start:end]
        # move the pointer to the correct location
        src = ctypes.byref(self.source.contents, start)
        casttype = ctypes.c_ubyte
        if self.itemsize == 2:
            casttype = ctypes.c_ushort
        elif self.itemsize == 4:
            casttype = ctypes.c_uint
        return ctypes.cast(src, ctypes.POINTER(casttype)).contents.value

    def _setitem(self, start, end, value):
        target = None
        if self.itemsize == 1:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_ubyte))
        elif self.itemsize == 2:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_ushort))
        elif self.itemsize == 4:
            target = ctypes.cast(self.source, ctypes.POINTER(ctypes.c_uint))
        value = prepare_color(value, self._surface)
        target[start // self.itemsize] = value


def _ndarray_prep(source, funcname, ndim):
    # Internal function for preparing SDL_Surfaces for casting to ndarrays
    if not _HASNUMPY:
        err = "'{0}' requires Numpy, which could not be found."
        raise UnsupportedError(err.format(funcname))

    # Get SDL surface and extract required attributes
    psurface = _get_target_surface(source, argname="source")
    sz = psurface.h * psurface.pitch
    bpp = psurface.format.contents.BytesPerPixel
    if bpp < 1 or bpp > 4:
        err = "The bpp of the source surface must be between 1 and 4, inclusive"
        raise ValueError(err + " (got {0}).".format(bpp))
    elif bpp == 3 and ndim == 2:
        err = "Surfaces with 3 bytes-per-pixel cannot be cast as 2D arrays."
        raise RuntimeError(err)

    # Handle 2D and 3D arrays differently where needed
    if ndim == 2:
        dtypes = {
            1: numpy.uint8,
            2: numpy.uint16,
            4: numpy.uint32
        }
        strides = (psurface.pitch, bpp)
        shape = psurface.h, psurface.w
        dtype = dtypes[bpp]
    else:
        strides = (psurface.pitch, bpp, 1)
        shape = psurface.h, psurface.w, bpp
        dtype = numpy.uint8

    return (psurface, sz, shape, dtype, strides)


def pixels2d(source, transpose=True):
    """Creates a 2D Numpy array view for a given SDL surface.

    This function casts the surface pixels to a 2D Numpy array view, providing
    read and write access to the underlying surface. If the source surface is
    RLE-accelerated, it will be locked automatically when the view is created
    and you will need to re-lock the surface using :func:`SDL_UnlockSurface`
    once you are done with the array.

    By default, the array is returned in ``arr[x][y]`` format with the x-axis
    as the first dimension, contrary to PIL and PyOpenGL convention. To obtain 
    an ``arr[y][x]`` array, set the ``transpose`` argument to ``False``.

    .. warning::
       The source surface should not be freed or deleted until the array is no
       longer needed. Accessing the array for a freed surface will likely cause
       Python to hard-crash.

    .. note::
       This function requires Numpy to be installed in the current Python
       environment.

    Args:
        source (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            SDL surface to cast to a numpy array.
        transpose (bool, optional): Whether the output array should be
            transposed to have ``arr[x][y]`` axes instead of ``arr[y][x]`` axes.
            Defaults to ``True``.

    Returns:
        :obj:`numpy.ndarray`: A 2-dimensional Numpy array containing the integer
        color values for each pixel in the surface.

    Raises:
        RuntimeError: If Numpy could not be imported.
   
    """
    sf, sz, shape, dtype, strides = _ndarray_prep(source, "pixels2d", ndim=2)
    if SDL_MUSTLOCK(sf):
        SDL_LockSurface(sf)

    pxbuf = ctypes.cast(sf.pixels, ctypes.POINTER(ctypes.c_ubyte * sz))
    arr = SurfaceArray(
        shape, dtype, pxbuf.contents, 0, strides, "C", source, sf
    )
    return arr.transpose() if transpose else arr


def pixels3d(source, transpose=True):
    """Creates a 3D Numpy array view for a given SDL surface.

    This function casts the surface pixels to a 3D Numpy array view, providing
    read and write access to the underlying surface. If the source surface is
    RLE-accelerated, it will be locked automatically when the view is created
    and you will need to re-lock the surface using :func:`SDL_UnlockSurface`
    once you are done with the array.

    By default, the array is returned in ``arr[x][y]`` format with the x-axis
    as the first dimension, contrary to PIL and PyOpenGL convention. To obtain 
    an ``arr[y][x]`` array, set the ``transpose`` argument to ``False``.

    When creating a 3D array view, the order of the RGBA values for each pixel
    may be reversed for some common surface pixel formats (e.g. 'BGRA' for a
    ``SDL_PIXELFORMAT_ARGB8888`` surface). To correct this, you can call
    ``numpy.flip(arr, axis=2)`` to return a view of the array with the expected
    channel order.

    .. warning::
       The source surface should not be freed or deleted until the array is no
       longer needed. Accessing the array for a freed surface will likely cause
       Python to hard-crash.

    .. note::
       This function requires Numpy to be installed in the current Python
       environment.

    Args:
        source (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            SDL surface to cast to a numpy array.
        transpose (bool, optional): Whether the output array should be
            transposed to have ``arr[x][y]`` axes instead of ``arr[y][x]`` axes.
            Defaults to ``True``.

    Returns:
        :obj:`numpy.ndarray`: A 3-dimensional Numpy array containing the values
        of each byte for each pixel in the surface.

    Raises:
        RuntimeError: If Numpy could not be imported.
   
    """
    sf, sz, shape, dtype, strides = _ndarray_prep(source, "pixels3d", ndim=3)
    if SDL_MUSTLOCK(sf):
        SDL_LockSurface(sf)

    pxbuf = ctypes.cast(sf.pixels, ctypes.POINTER(ctypes.c_ubyte * sz))
    arr = SurfaceArray(
        shape, dtype, pxbuf.contents, 0, strides, "C", source, sf
    )
    return arr.transpose(1, 0, 2) if transpose else arr


def surface_to_ndarray(source, ndim=3):
    """Returns a copy of an SDL surface as a Numpy array.
    
    The main difference between this function and :func:`~sdl2.ext.pixels2d` or
    :func:`~sdl2.ext.pixels3d` is that it returns a copy of the surface instead
    of a view, meaning that modifying the returned array will not affect the
    original surface (or vice-versa). This function is also slightly safer,
    as it does not assume that the source surface has been kept in memory.

    When creating a 3D array copy, the order of the RGBA values for each pixel
    may be reversed for some common surface pixel formats (e.g. 'BGRA' for a
    ``SDL_PIXELFORMAT_ARGB8888`` surface). To correct this, you can call
    ``numpy.flip(arr, axis=2)`` to return a view of the array with the expected
    channel order.

    .. note::
       Unlike :func:`~sdl2.ext.pixels2d` or :func:`~sdl2.ext.pixels3d`, this
       function always returns arrays with the y-axis as the first dimension
       (e.g. ``arr[y][x]``).

    .. note::
       This function requires Numpy to be installed in the current Python
       environment.

    Args:
        source (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            SDL surface to convert to a numpy array.
        ndim (int, optional): The number of dimensions for the returned array,
            must be either 2 (for a 2D array) or 3 (for a 3D array). Defaults
            to 3.

    Returns:
        :obj:`numpy.ndarray`: A Numpy array containing a copy of the pixel data
        for the given surface.

    Raises:
        RuntimeError: If Numpy could not be imported.

    """
    if ndim not in [2, 3]:
        err = "Can only convert surfaces to 2D or 3D arrays (got {0})."
        raise ValueError(err.format(ndim))
    funcname = "surface_to_array"
    sf, sz, shape, dtype, strides = _ndarray_prep(source, funcname, ndim)
    was_unlocked = sf.locked == 0
    if SDL_MUSTLOCK(sf):
        SDL_LockSurface(sf)

    pxbuf = ctypes.cast(sf.pixels, ctypes.POINTER(ctypes.c_ubyte * sz))
    tmp = numpy.ndarray(shape, dtype, pxbuf.contents, strides=strides)
    if was_unlocked and SDL_MUSTLOCK(sf):
        SDL_UnlockSurface(sf)

    return numpy.copy(tmp)


class SurfaceArray(numpy.ndarray if _HASNUMPY else object):
    """A Numpy array that keeps a reference to its parent SDL surface.

    This class is used to keep track of the original source object for
    :func:`~sdl2.ext.pixels2d` or :func:`~sdl2.ext.pixels3d` to prevent it from
    being automatically freed during garbage collection. It should never be used
    for any other purpose.
    
    """
    def __new__(cls, shape, dtype=float, buffer_=None, offset=0,
                strides=None, order=None, source=None, surface=None):
        if _HASNUMPY:
            sfarray = numpy.ndarray.__new__(
                cls, shape, dtype, buffer_, offset, strides, order
            )
            sfarray._source = source
            sfarray._surface = surface
            return sfarray
        else:
            return None

    def __array_finalize__(self, sfarray):
        if sfarray is None:
            return
        self._source = getattr(sfarray, '_source', None)
        self._surface = getattr(sfarray, '_surface', None)
