import ctypes
from .compat import isiterable, UnsupportedError
from .err import raise_sdl_err
from .array import to_ctypes
from .color import convert_to_color
from .. import surface, pixels, rect
from .algorithms import clipline
from .surface import _get_target_surface

__all__ = ["prepare_color", "fill", "line"]


def prepare_color(color, target):
    """Prepares a given color for a specific target.

    Targets can be :obj:`~sdl2.SDL_PixelFormat`, :obj:`~sdl2.SDL_Surface`,
    or :obj:`~sdl2.ext.SoftwareSprite` objects. 
    
    Colors can be provided in any form supported by
    :func:`sdl2.ext.convert_to_color`.
    
    Args:
        color (:obj:`sdl2.ext.Color`): The color to prepare for the pixel format
            of the given target.
        target (:obj:`SDL_PixelFormat`, :obj:`SDL_Surface`, :obj:`SoftwareSprite`): The
            target pixel format, surface, or sprite for which the color should be
            prepared.
    
    Returns:
        int: An integer approximating the given color in the target's pixel
        format.

    """
    color = convert_to_color(color)
    pformat = None
    # Software surfaces
    if isinstance(target, pixels.SDL_PixelFormat):
        pformat = target
    else:
        surf = _get_target_surface(target)
        pformat = surf.format.contents
    if pformat.Amask != 0:
        # Target has an alpha mask
        return pixels.SDL_MapRGBA(pformat, color.r, color.g, color.b, color.a)
    return pixels.SDL_MapRGB(pformat, color.r, color.g, color.b)


def fill(target, color, area=None):
    """Fills one or more rectangular areas on a surface with a given color.

    Fill areas can be specified as 4-item ``(x, y, w, h)`` tuples,
    :obj:`~sdl2.rect.SDL_Rect` objects, or a list containing multiple areas to
    fill in either format. If no area is provided, the entire target will be
    filled with the provided color.

    The fill color can be provided in any format supported by
    :func:`~sdl2.ext.color.convert_to_color`.

    Args:
        target (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            target surface or sprite to modify.
        color (:obj:`sdl2.ext.Color`): The color with which to fill the
            specified region(s) of the target.
        area (tuple, :obj:`~sdl2.SDL_Rect`, list, optional): The rectangular
            region (or regions) of the target surface to fill with the given
            colour. If no regions are specified (the default), the whole surface
            of the target will be filled.

    """
    color = prepare_color(color, target)
    rtarget = _get_target_surface(target)

    err_msg = (
        "Fill areas must be specified as either (x, y, w, h) tuples or "
        "SDL_Rect objects (Got unsupported format '{0}')"
    )

    rects = []
    if area:
        if not isiterable(area) or not isiterable(area[0]):
            area = [area]
        for r in area:
            if isinstance(r, rect.SDL_Rect):
                rects.append(r)
            else:
                try:
                    new_rect = rect.SDL_Rect(
                        int(r[0]), int(r[1]), int(r[2]), int(r[3])
                    )
                    rects.append(new_rect)
                except (TypeError, ValueError, IndexError):
                    raise ValueError(err_msg.format(str(r)))

    if len(rects) > 2:
        rects, count = to_ctypes(rects, rect.SDL_Rect)
        rects = ctypes.cast(rects, ctypes.POINTER(rect.SDL_Rect))
        ret = surface.SDL_FillRects(rtarget, rects, count, color)
    elif len(rects) == 1:
        ret = surface.SDL_FillRect(rtarget, rects[0], color)
    else:
        ret = surface.SDL_FillRect(rtarget, None, color)
    if ret < 0:
        raise_sdl_err("filling the surface")


def line(target, color, dline, width=1):
    """Draws one or lines on a surface in a given color.

    The fill color can be provided in any format supported by
    :func:`~sdl2.ext.color.convert_to_color`.

    Args:
        target (:obj:`~sdl2.SDL_Surface`, :obj:`~sdl2.ext.SoftwareSprite`): The
            target surface or sprite to modify.
        color (:obj:`sdl2.ext.Color`): The color with which to draw lines.
        dline (tuple, list): The ``(x1, y1, x2, y2)`` integer coordinates of a
            line to draw, or a list of multiple sets of ``(x1, y1, x2, y2)``
            coordinates for multiple lines.
        width (int, optional): The width of the line(s) in pixels. Defaults to
            1 if not specified.

    """
    if width < 1:
        raise ValueError("width must be greater than 0")
    color = prepare_color(color, target)
    rtarget = _get_target_surface(target)

    # If first item is iterable, assume multiple lines in (x1, y1, x2, y2) form
    if isiterable(dline[0]):
        flattened = []
        for line in dline:
            flattened += list(line)
        dline = flattened

    # line: (x1, y1, x2, y2) OR (x1, y1, x2, y2, ...)
    if (len(dline) % 4) != 0:
        raise ValueError("line does not contain a valid set of points")
    pcount = len(dline)
    SDLRect = rect.SDL_Rect
    fillrect = surface.SDL_FillRect

    pitch = rtarget.pitch
    bpp = rtarget.format.contents.BytesPerPixel
    frac = pitch / bpp
    clip_rect = rtarget.clip_rect
    left, right = clip_rect.x, clip_rect.x + clip_rect.w - 1
    top, bottom = clip_rect.y, clip_rect.y + clip_rect.h - 1

    if bpp == 3:
        raise UnsupportedError("24bpp surfaces are not currently supported.")
    if bpp == 1:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint8))
    elif bpp == 2:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint16))
    elif bpp == 4:
        pxbuf = ctypes.cast(rtarget.pixels, ctypes.POINTER(ctypes.c_uint32))
    else:
        pxbuf = rtarget.pixels  # byte-wise access.

    for idx in range(0, pcount, 4):
        x1, y1, x2, y2 = dline[idx:idx + 4]
        if x1 == x2:
            # Vertical line
            if y1 < y2:
                varea = SDLRect(x1 - width // 2, y1, width, y2 - y1)
            else:
                varea = SDLRect(x1 - width // 2, y2, width, y1 - y2)
            fillrect(rtarget, varea, color)
            continue
        if y1 == y2:
            # Horizontal line
            if x1 < x2:
                varea = SDLRect(x1, y1 - width // 2, x2 - x1, width)
            else:
                varea = SDLRect(x2, y1 - width // 2, x1 - x2, width)
            fillrect(rtarget, varea, color)
            continue
        if width != 1:
            raise ValueError("Diagonal lines must have a width of 1.")
        if width == 1:
            # Bresenham
            x1, y1, x2, y2 = clipline(left, top, right, bottom, x1, y1, x2, y2)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            if x1 is None:
                # not to be drawn
                continue
            dx = abs(x2 - x1)
            dy = -abs(y2 - y1)
            err = dx + dy
            sx, sy = 1, 1
            if x1 > x2:
                sx = -sx
            if y1 > y2:
                sy = -sy
            while True:
                pxbuf[int(y1 * frac + x1)] = color
                if x1 == x2 and y1 == y2:
                    break
                e2 = err * 2
                if e2 > dy:
                    err += dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy
