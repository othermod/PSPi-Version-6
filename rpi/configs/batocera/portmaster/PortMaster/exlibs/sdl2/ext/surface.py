from .compat import isiterable
from .err import raise_sdl_err
from .color import convert_to_color
from .. import pixels
from .. import surface as surf
from ..rect import SDL_Rect

__all__ = ["subsurface"]


def _get_rect_tuple(r, argname):
    if isinstance(r, SDL_Rect):
        return (r.x, r.y, r.w, r.h)
    elif isiterable(r) and len(r) == 4:
        return tuple(r)
    else:
        e = "'{0}' must be an SDL_Rect or tuple of 4 integers."
        raise TypeError(e.format(argname))


def _get_target_surface(target, argname="target"):
    """Gets the SDL_surface from the passed target."""
    if hasattr(target, "surface"):  # i.e. if SoftwareSprite
        rtarget = target.surface  
    elif isinstance(target, surf.SDL_Surface):
        rtarget = target
    elif "SDL_Surface" in str(type(target)):
        rtarget = target.contents
    else:
        raise TypeError(
            "{0} must be a valid Sprite or SDL Surface".format(argname)
        )
    return rtarget


def _create_surface(size, fill=None, fmt="ARGB8888", errname="SDL"):
    # Perform initial type and argument checking
    if not isiterable(size) and len(size) == 2:
        e = "Surface size must be a tuple of two positive integers."
        raise TypeError(e)
    if not all([i > 0 and int(i) == i for i in size]):
        e = "Surface height and width must both be positive integers (got {0})."
        raise ValueError(e.format(str(size)))
    if fmt not in pixels.NAME_MAP.keys() and fmt not in pixels.ALL_PIXELFORMATS:
        e = "'{0}' is not a supported SDL pixel format."
        raise ValueError(e.format(fmt))
    if fill is not None:
        fill = convert_to_color(fill)

    # Actually create a surface with the given pixel format
    w, h = size
    bpp = 32  # NOTE: according to the SDL_surface.c code, this has no effect
    fmt_enum = fmt if type(fmt) == int else pixels.NAME_MAP[fmt]
    sf = surf.SDL_CreateRGBSurfaceWithFormat(0, w, h, bpp, fmt_enum)
    if not sf:
        raise_sdl_err("creating the {0} surface".format(errname))

    # If provided, set the fill for the new surface
    if fill is not None:
        pixfmt = sf.contents.format.contents
        if pixfmt.Amask == 0:
            fill_col = pixels.SDL_MapRGB(pixfmt, fill.r, fill.g, fill.b)
        else:
            fill_col = pixels.SDL_MapRGBA(pixfmt, fill.r, fill.g, fill.b, fill.a)
        surf.SDL_FillRect(sf, None, fill_col)

    return sf


def subsurface(surface, area):
    """Creates a new :obj:`~sdl2.SDL_Surface` from a part of another surface.

    Surfaces created with this function will share pixel data with the original
    surface, meaning that any modifications to one surface will result in
    modifications to the other.

    .. warning::
       Because subsurfaces share pixel data with their parent surface, they
       *cannot* be used after the parent surface is freed. Doing so will
       almost certainly result in a segfault.

    Args:
        surface (:obj:`~sdl2.SDL_Surface`): The parent surface from which
            new sub-surface should be created.
        area (:obj:`SDL_Rect`, tuple): The ``(x, y, w, h)`` subset of the parent
            surface to use for the new surface, where ``x, y`` are the pixel
            coordinates of the top-left corner of the rectangle and ``w, h`` are
            its width and height (in pixels). Can also be specified as an
            :obj:`SDL_Rect`.

    Returns:
        :obj:`~sdl2.SDL_Surface`: The newly-created subsurface.

    """
    if not isinstance(surface, surf.SDL_Surface):
        if "SDL_Surface" in str(type(surface)):
            surface = surface.contents
        else:
            e = "'surface' must be an SDL_Surface (got {0})"
            raise TypeError(e.format(type(surface)))

    x, y, w, h = _get_rect_tuple(area, argname="area")
    if x + w > surface.w or y + h > surface.h:
        e = "The specified area {0} exceeds the bounds of the parent surface "
        e += str((surface.w, surface.h))
        raise ValueError(e.format(str(area)))

    fmt = surface.format[0]
    bpp = fmt.BitsPerPixel
    subpixels = (surface.pixels + surface.pitch * y + fmt.BytesPerPixel * x)
    subsurf = surf.SDL_CreateRGBSurfaceFrom(
        subpixels, w, h, bpp, surface.pitch, fmt.Rmask, fmt.Gmask, fmt.Bmask, fmt.Amask
    )
    if not subsurf:
        raise_sdl_err("creating the subsurface")
        
    return subsurf.contents
