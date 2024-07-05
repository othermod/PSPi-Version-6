from ctypes import byref, c_int, c_float

from .. import blendmode, surface, rect, video, render, error, dll, hints
from ..stdinc import Uint8, Uint32

from .color import convert_to_color
from .err import raise_sdl_err
from .compat import deprecated, stringify, byteify, isiterable
from .sprite import SoftwareSprite, TextureSprite
from .surface import _get_target_surface
from .window import Window

__all__ = ["set_texture_scale_quality", "Renderer", "Texture"]


# NOTE: The following 3 utility functions probably belong in a separate module

def is_numeric(x):
    try:
        return float(x) == x
    except (TypeError, ValueError):
        return False

def _is_point(x):
    if isiterable(x):
        return len(x) == 2
    if isinstance(x, rect.SDL_Point) or isinstance(x, rect.SDL_FPoint):
        return True
    return False

def _is_rect(x):
    if isiterable(x):
        return len(x) == 4
    if isinstance(x, rect.SDL_Rect) or isinstance(x, rect.SDL_FRect):
        return True
    return False

def _sanitize_points(points):
    # If first item is numeric, assume flat list of points
    if isinstance(points, rect.SDL_Point) or isinstance(points, rect.SDL_FPoint):
        points = [points]
    elif is_numeric(points[0]):
        if len(points) % 2 != 0:
            raise ValueError("Flat x/y coordinate lists must have even length")
        chunked = []
        for i in range(0, len(points), 2):
            p = (points[i], points[i+1])
            chunked.append(p)
        points = chunked

    type_err = (
        "Points must be specified as either (x, y) tuples or "
        "SDL_Point objects (Got unsupported format '{0}')"
    )
    pts = []
    if not isiterable(points):
        points = [points]
    for p in points:
        if isinstance(p, rect.SDL_Point) or isinstance(p, rect.SDL_FPoint):
            p = (p.x, p.y)
        elif len(p) != 2:
            raise ValueError(type_err.format(str(p)))
        if dll.version < 2010 and any([int(v) != v for v in p]):
            e = "Floating point rendering requires SDL 2.0.10 or newer"
            raise RuntimeError(e + " (got '{0}')".format(str(p)))
        pts.append((p[0], p[1]))
    return pts


def _sanitize_rects(rects):
    type_err = (
        "Rectangles must be specified as either (x, y, w, h) tuples or "
        "SDL_Rect objects (Got unsupported format '{0}')"
    )
    out = []
    if not (isiterable(rects) and _is_rect(rects[0])):
        rects = [rects]
    for r in rects:
        if isinstance(r, rect.SDL_Rect) or isinstance(r, rect.SDL_FRect):
            r = (r.x, r.y, r.w, r.h)
        elif len(r) != 4:
            raise ValueError(type_err.format(str(r)))
        if dll.version < 2010 and any([int(v) != v for v in r]):
            e = "Floating point rendering requires SDL 2.0.10 or newer"
            raise RuntimeError(e + " (got '{0}')".format(str(r)))
        out.append((r[0], r[1], r[2], r[3]))
    return out


def _get_texture_size(texture):
    flags = Uint32()
    access, w, h = (c_int(), c_int(), c_int())
    ret = render.SDL_QueryTexture(
        texture, byref(flags), byref(access), byref(w), byref(h)
    )
    if ret < 0:
        raise_sdl_err("getting texture attributes")
    return (w.value, h.value)



def set_texture_scale_quality(method):
    """Sets the default scaling quailty for :obj:`~sdl2.ext.Texture` objects.

    By default, SDL2 uses low-quality nearest-neighbour scaling for all new
    textures. This method lets you change the default scaling method to one of
    the following options:
    
    ========= =============================================================
    Method    Description
    ========= =============================================================
    Nearest   Nearest-neighbour pixel scaling (no filtering)
    Linear    Linear filtering
    Best      Anisotropic filtering (falls back to linear if not available)
    ========= =============================================================

    This function does not apply retroactively, and will only affect textures
    created after it is called.

    Args:
        method (str): The default scaling method to use for SDL textures. Must
            be one of 'nearest', 'linear', or 'best'.

    """
    method = byteify(method.lower())
    if method not in [b"nearest", b"linear", b"best"]:
        raise ValueError(
            "Texture scaling method must be 'nearest', 'linear', or 'best'."
        )
    hints.SDL_SetHint(hints.SDL_HINT_RENDER_SCALE_QUALITY, method)



class Texture(object):
    """A 2D texture to be used with a :obj:`~sdl2.ext.Renderer`.

    In SDL2, textures are 2D images that have been prepared for fast rendering
    with a given renderer. For example, if an SDL surface is converted into a
    texture with a :obj:`~sdl2.ext.Renderer` using the OpenGL backend, the pixel
    data for the surface will internally be converted into an OpenGL texture.

    Once a surface has been converted into a :obj:`Texture`, the surface can be
    safely deleted if no longer needed.

    Args:
        renderer (:obj:`~sdl2.ext.Renderer`): The renderer associated with the
            texture.
        surface (:obj:`~sdl2.SDL_Surface`): An SDL surface from which the
            texture will be created.
    
    """
    def __init__(self, renderer, surface):
        # Validate and get reference to the parent renderer
        self._renderer_ref = None
        if isinstance(renderer, Renderer):
            self._renderer_ref = renderer._renderer_ref
        elif hasattr(renderer, "contents"):
            if isinstance(renderer.contents, render.SDL_Renderer):
                self._renderer_ref = [renderer]
        if self._renderer_ref is None:
            raise TypeError(
                "'renderer' must be a valid Renderer object or a pointer to "
                "an SDL_Renderer."
            )
        # Convert the passed surface into a texture
        surface = _get_target_surface(surface, "surface")
        self._tx = render.SDL_CreateTextureFromSurface(self._renderer, surface)
        if not self._tx:
            raise_sdl_err("creating the texture")
        # Cache the size of the texture for future use
        self._size = _get_texture_size(self.tx)

    def __del__(self):
        if hasattr(self, "_tx"):
            self.destroy()

    @property
    def _renderer(self):
        # NOTE: This is sort of a hack to get around a ctypes problem. Basically,
        # if the parent renderer of a texture is destroyed before the texture
        # itself, destroying or doing anything with that texture will result in a
        # segfault. By wrapping the renderer in a List, we can overwrite it with
        # None when destroyed (within the Renderer class) and detect that in any
        # child textures to avoid any memory-unsafe behaviour.
        return self._renderer_ref[0]

    @property
    def tx(self):
        """:obj:`~sdl2.SDL_Texture`: The underlying base SDL texture object.
        Can be used to perform operations with the texture using the base
        PySDL2 bindings.

        """
        if self._tx is None:
            raise RuntimeError(
                "Cannot use a texture after it has been destroyed."
            )
        elif self._renderer_ref[0] is None:
            raise RuntimeError(
                "Cannot use a texture after its parent renderer has been "
                "destroyed."
            )
        return self._tx

    @property
    def size(self):
        """tuple: The width and height (in pixels) of the texture."""
        tx = self.tx # Makes sure texture is still usable
        return self._size

    def destroy(self):
        """Deletes the texture and frees its associated memory.
        
        When a texture is no longer needed, it should be destroyed using this
        method to free up memory for new textures. After being destroyed, a
        texture can no longer be used.

        """
        if self._tx and self._renderer_ref[0]:
            render.SDL_DestroyTexture(self._tx)
            self._tx = None

    @property
    def scale_mode(self):
        """str: The current scaling mode to use for rendering the texture. Can
        be 'nearest', 'linear', 'best', or 'unknown'.
        
        See :func:`set_texture_scale_quality` for more information.

        .. note::
           For SDL versions older than 2.0.12, the scaling mode will always be
           'unknown'.

        """
        if dll.version < 2012:
            return "unknown"
        modes = ["nearest", "linear", "best"]
        mode_num = c_int()
        ret = render.SDL_GetTextureScaleMode(self.tx, byref(mode_num))
        if ret < 0:
            raise_sdl_err("retrieving the texture scaling mode")
        try:
            return modes[mode_num.value]
        except IndexError:
            return "unknown"

    def set_scale_mode(self, mode):
        """Sets a custom scaling method to use for rendering the texture.

        This method overrides the default texture scaling method specified by
        :func:`set_texture_scale_quality`, the documentation for which describes
        the different possible scaling modes.

        .. note::
           Support for custom per-texture scaling modes is only available in
           SDL2 2.0.12 and up. As such, this method has no effect when used with
           earlier releases of SDL2.

        Args:
            mode (str): The scaling method to use for the current texture. Must
                be one of 'nearest', 'linear', or 'best'.

        """
        if dll.version < 2012:
            return None
        modes = {
            "nearest": render.SDL_ScaleModeNearest,
            "linear": render.SDL_ScaleModeLinear,
            "best": render.SDL_ScaleModeBest,
        }
        mode = mode.lower()
        if mode not in modes.keys():
            raise ValueError(
                "Texture scaling mode must be either 'nearest', 'linear', "
                "or 'best'."
            )
        ret = render.SDL_SetTextureScaleMode(self.tx, modes[mode])
        if ret < 0:
            raise_sdl_err("setting the texture scaling mode")



class Renderer(object):
    """A rendering context for SDL2 windows and sprites.

    A ``Renderer`` can be created from an SDL window, an SDL Surface, or a
    :obj:`~sdl2.ext.SoftwareSprite`. Depending on the settings and operating
    system, this rendering context can use either hardware or software
    acceleration.

    A useful feature of SDL renderers is that that the logical size of the
    rendering context can be different than the actual size (in pixels) of its
    target window or surface. For example, the renderer for a 1024x768 window
    can be set to have a logical size of 640x480, improving performance at the
    cost of image quality. The rendered content will be automatically scaled to
    fit the target, and will be centered with black bars on either side in the
    case of an aspect ratio mismatch.

    If creating a rendering context from a window, you can customize the
    renderer using flags to request different settings:

    =============================== ===========================================
    Flag                            Description
    =============================== ===========================================
    ``SDL_RENDERER_SOFTWARE``       Requests a software-accelerated renderer.
    ``SDL_RENDERER_ACCELERATED``    Requests a hardware-accelerated renderer.
    ``SDL_RENDERER_PRESENTVSYNC``   Enables vsync support for :meth:`present`.
    ``SDL_RENDERER_TARGETTEXTURE``  Requests support for rendering to texture.
    =============================== ===========================================

    To combine multiple flags, you can use a bitwise OR to combine two or more
    together before passing them to the `flags` argument::

      render_flags = (
          sdl2.SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
      )
      sdl2.ext.Renderer(window, flags=render_flags)

    By default, SDL2 will choose the first renderer backend that supports all
    the requested flags. However, you can also request a specific rendering
    backend by name (e.g. 'opengl', 'opengles2', 'metal', 'direct3d', etc.),
    giving you more control but likely making your code less cross-platform.

    Args:
        target (:obj:`~sdl2.ext.Window`, :obj:`~sdl2.SDL_Surface`): The target
            window or surface from which to create the rendering context.
        backend (str or int, optional): The name of the specific backend to use
            for the new rendering context (e.g. 'opengl'). Defaults to letting
            SDL2 decide. If ``target`` is not an SDL window, this argument has
            no effect.
        logical_size (tuple, optional): The initial logical size (in pixels) of
            the rendering context as a ``(w, h)`` tuple. Defaults to the size
            of the target window or surface.
        flags (int, optional): The requested features and settings for the
            new rendering context. Defaults to requesting a hardware-accelerated
            context. If ``target`` is not an SDL window, this argument has no
            effect.
 
    Raises:
        RuntimeError: If a requested rendering backend is not available.

    """

    def __init__(self, target, backend=-1, logical_size=None,
                 flags=render.SDL_RENDERER_ACCELERATED):
        self._renderer_ref = None
        self.rendertarget = None

        available = self._get_render_drivers()
        if isinstance(backend, str):
            if backend.lower() in available:
                index = available.index(backend.lower())
            else:
                e1 = "'{0}' is not a supported renderer on this system. "
                e2 = "The renderer backend must be one of the following: "
                raise RuntimeError(e1.format(backend) + e2 + str(available))
        else:
            index = backend

        _size = None
        if isinstance(target, Window):
            _renderer = render.SDL_CreateRenderer(target.window, index, flags)
            _size = target.size
        elif isinstance(target, video.SDL_Window):
            _renderer = render.SDL_CreateRenderer(target, index, flags)
            w, h = c_int(0), c_int(0)
            video.SDL_GetWindowSize(target, byref(w), byref(h))
            _size = (w.value, h.value)
        elif isinstance(target, SoftwareSprite):
            _renderer = render.SDL_CreateSoftwareRenderer(target.surface)
            _size = target.size
        elif isinstance(target, surface.SDL_Surface):
            _renderer = render.SDL_CreateSoftwareRenderer(target)
            _size = (target.w, target.h)
        elif "SDL_Surface" in str(type(target)):
            _renderer = render.SDL_CreateSoftwareRenderer(target.contents)
            _size = (target.contents.w, target.contents.h)
        else:
            raise TypeError("unsupported target type")
        if not _renderer:
            raise_sdl_err("creating the SDL renderer")
        error.SDL_ClearError()  # Clear any errors from renderer selection
        self._renderer_ref = [_renderer]

        self.rendertarget = target
        self.color = (0, 0, 0, 0)  # Set black as the default draw color
        self.logical_size = _size
        self._original_logical_size = self.logical_size
        if logical_size is not None:
            self.logical_size = logical_size

    def __del__(self):
        if self._renderer_ref is not None:
            self.destroy()

    def _get_render_drivers(self):
        renderers = []
        drivers = render.SDL_GetNumRenderDrivers()
        for x in range(drivers):
            info = render.SDL_RendererInfo()
            ret = render.SDL_GetRenderDriverInfo(x, info)
            if ret == 0:
                renderers.append(stringify(info.name))
            error.SDL_ClearError()
        return renderers

    @property
    def sdlrenderer(self):
        """:obj:`~sdl2.SDL_Renderer`: The underlying base SDL renderer object.
        Can be used to perform operations with the renderer using the base
        PySDL2 bindings.

        """
        if self._renderer_ref[0] is None:
            raise RuntimeError(
                "Cannot use a renderer after it has been destroyed."
            )
        return self._renderer_ref[0]

    @property
    @deprecated
    def renderer(self):
        return self.sdlrenderer

    @property
    def logical_size(self):
        """tuple: The logical size of the rendering context (in pixels), as a
        ``(width, height)`` tuple.

        """
        w, h = c_int(0), c_int(0)
        render.SDL_RenderGetLogicalSize(self.sdlrenderer, byref(w), byref(h))
        return w.value, h.value

    @logical_size.setter
    def logical_size(self, size):
        width, height = size
        ret = render.SDL_RenderSetLogicalSize(self.sdlrenderer, width, height)
        if ret != 0:
            raise_sdl_err("setting the logical size of the renderer")

    @property
    def color(self):
        """:obj:`~sdl2.ext.Color`: The current drawing color of the renderer."""
        r, g, b, a = Uint8(0), Uint8(0), Uint8(0), Uint8(0)
        ret = render.SDL_GetRenderDrawColor(self.sdlrenderer, byref(r), byref(g),
                                            byref(b), byref(a))
        if ret < 0:
            raise_sdl_err("retrieving the drawing color of the renderer")
        return convert_to_color((r.value, g.value, b.value, a.value))

    @color.setter
    def color(self, value):
        c = convert_to_color(value)
        ret = render.SDL_SetRenderDrawColor(self.sdlrenderer, c.r, c.g, c.b, c.a)
        if ret < 0:
            raise_sdl_err("setting the drawing color of the renderer")

    @property
    def blendmode(self):
        """int: The blend mode used for :meth:`fill` and :meth:`line` drawing
        operations. This value can be any of the following constants:
        
        ========================= ====================================
        Flag                      Description
        ========================= ====================================
        ``SDL_BLENDMODE_NONE``    No blending
        ``SDL_BLENDMODE_BLEND``   Alpha channel blending
        ``SDL_BLENDMODE_ADD``     Additive blending
        ``SDL_BLENDMODE_MOD``     Color modulation
        ``SDL_BLENDMODE_MUL``     Color multiplication (SDL >= 2.0.12)
        ========================= ====================================

        """
        mode = blendmode.SDL_BlendMode()
        ret = render.SDL_GetRenderDrawBlendMode(self.sdlrenderer, byref(mode))
        if ret < 0:
            raise_sdl_err("retrieving the blend mode for the renderer")
        return mode

    @blendmode.setter
    def blendmode(self, value):
        ret = render.SDL_SetRenderDrawBlendMode(self.sdlrenderer, value)
        if ret < 0:
            raise_sdl_err("setting the blend mode for the renderer")

    @property
    def scale(self):
        """tuple: The x/y scaling factors applied to all drawing coordinates
        before rendering, in the format ``(scale_x, scale_y)``. These can be
        used to facilitate resolution-independent drawing.
        
        """
        sx = c_float(0.0)
        sy = c_float(0.0)
        render.SDL_RenderGetScale(self.sdlrenderer, byref(sx), byref(sy))
        return sx.value, sy.value

    @scale.setter
    def scale(self, value):
        if any([s <= 0 for s in value]):
            raise ValueError("Scaling factors must be greater than zero.")
        sx, sy = value
        ret = render.SDL_RenderSetScale(self.sdlrenderer, sx, sy)
        if ret != 0:
            raise_sdl_err("setting the scaling factors for the renderer")

    def destroy(self):
        """Destroys the renderer and any associated textures.

        When a renderer is no longer needed, it should be destroyed using this
        method to free up its associated memory. After being destroyed, a
        renderer can no longer be used.
        
        """
        if self._renderer_ref[0]:
            render.SDL_DestroyRenderer(self._renderer_ref[0])
            self._renderer_ref[0] = None
            self.rendertarget = None

    def reset_logical_size(self):
        """Resets the logical size of the renderer to its original value."""
        self.logical_size = self._original_logical_size

    def clear(self, color=None):
        """Clears the rendering surface with a given color.

        Args:
            color (:obj:`~sdl2.ext.Color`, optional): The color with which to
                clear the entire rendering context. If not specified, the
                renderer's current :attr:`color` will be used.

        """
        if color is None:
            ret = render.SDL_RenderClear(self.sdlrenderer)
        else:
            tmp = self.color
            self.color = color
            ret = render.SDL_RenderClear(self.sdlrenderer)
            self.color = tmp
        if ret < 0:
           raise_sdl_err("clearing the rendering context")

    def copy(self, src, srcrect=None, dstrect=None, angle=0, center=None,
             flip=render.SDL_FLIP_NONE):
        """Copies (blits) a texture to the rendering context.

        If the source texture is an :obj:`~sdl2.SDL_Surface`, you will need
        to convert it into a :obj:`~sdl2.ext.Texture` first before it can be
        copied to the rendering surface.

        The source texture can be flipped horizontally or vertically when
        being copied to the rendering context using one of the following
        flags:

        ========================= ===================================
        Flag                      Description
        ========================= ===================================
        ``SDL_FLIP_NONE``         Does not flip the source (default)
        ``SDL_FLIP_HORIZONTAL``   Flips the source horizontally
        ``SDL_FLIP_VERTICAL``     Flips the source vertically
        ========================= ===================================

        .. note::
           Subpixel rendering (i.e. using floats as pixel coordinates) requires
           SDL 2.0.10 or newer.

        Args:
            src (:obj:`~sdl2.ext.Texture`, :obj:`~sdl2.SDL_Texture`): The source
                texture to copy to the rendering surface.
            srcrect (tuple, optional): An ``(x, y, w, h)`` rectangle defining
                the subset of the source texture to copy to the rendering
                surface. Defaults to copying the entire source texture.
            dstrect (tuple, optional): An ``(x, y, w, h)`` rectangle
                defining the region of the rendering surface to which the 
                source texture will be copied. Alternatively, if only
                ``(x, y)`` coordinates are provided, the width and height of
                the source rectangle will be used. Defaults to stretching
                the source across the entire rendering context.
            angle (float, optional): The clockwise rotation (in degrees) to
                apply to the destination rectangle. Defaults to no rotation.
            center (tuple, optional): The point around with the destination
                rectangle will be rotated. Defaults to the center of the
                destination rectangle.
            flip (int, optional): A flag indicating whether the source should
                be flipped (horizontally or vertically) when rendering to the
                render context. Defaults to no flipping.

        """
        if dll.version < 2010:
            render_copy = render.SDL_RenderCopyEx
            Point = rect.SDL_Point
            Rect = rect.SDL_Rect
        else:
            render_copy = render.SDL_RenderCopyExF
            Point = rect.SDL_FPoint
            Rect = rect.SDL_FRect

        if isinstance(src, TextureSprite):
            texture = src.texture
            angle = angle if angle != 0 else src.angle
            center = center if center else src.center
            flip = flip if flip != 0 else src.flip
        elif isinstance(src, Texture):
            texture = src.tx
        elif isinstance(src, render.SDL_Texture):
            texture = src
        else:
            raise TypeError("src must be a Texture object or an SDL_Texture")

        if srcrect:
            x, y, w, h = _sanitize_rects([srcrect])[0]
            srcrect = rect.SDL_Rect(int(x), int(y), int(w), int(h))

        if dstrect:
            if _is_point(dstrect):
                x, y = dstrect
                if srcrect:
                    w, h = (srcrect.w, srcrect.h)
                else:
                    w, h = _get_texture_size(texture)
            elif _is_rect(dstrect):
                x, y, w, h = dstrect
            else:
                err = "'dstrect' must be a valid point or rectangle."
                raise ValueError(err)
            dstrect = Rect(x, y, w, h)

        if center:
            x, y = _sanitize_points(center)[0]
            center = Point(x, y)

        ret = render_copy(
            self.sdlrenderer, texture, srcrect, dstrect, angle, center, flip
        )
        if ret < 0:
            raise_sdl_err("copying the texture to the rendering context")

    def blit(self, src, srcrect=None, dstrect=None, angle=0, center=None,
             flip=render.SDL_FLIP_NONE):
        """Copies a texture to the rendering context.
        
        An alias for the :meth:`copy` method.

        """
        self.copy(src, srcrect, dstrect, angle, center, flip)

    def present(self):
        """Presents the current rendering surface to the screen.

        Because SDL renderers use batch rendering (i.e. they have a separate
        backbuffer that is drawn to and buffer shown on screen which are
        switched when this function is called), any drawing operations
        performed with the renderer will not take effect until this method
        is called.

        It is recommended that you clear and redraw the contents of the
        rendering context every time before this method is called, as the
        contents of the buffers are not guaranteed to remain the same between
        repeat presentations.
        
        """
        render.SDL_RenderPresent(self.sdlrenderer)

    def draw_line(self, points, color=None):
        """Draws one or more connected lines on the rendering context.

        .. note::
           Subpixel rendering (i.e. using floats as pixel coordinates) requires
           SDL 2.0.10 or newer.

        Args:
            points (list): A list of 2 or more ``(x, y)`` coordinates or
                :obj:`~sdl2.SDL_Point` objects defining the set of connected
                lines to draw.
            color (:obj:`~sdl2.ext.Color`, optional): The color with which to
                draw the lines. If not specified, the renderer's current
                :attr:`color` will be used.

        """
        if dll.version < 2010:
            draw_lines = render.SDL_RenderDrawLines
            Point = rect.SDL_Point
        else:
            draw_lines = render.SDL_RenderDrawLinesF
            Point = rect.SDL_FPoint

        points = _sanitize_points(points)
        if len(points) < 2:
            raise ValueError("At least two (x, y) points are required.")
        sdlpts = []
        for p in points:
            x, y = p
            sdlpts.append(Point(x, y))
        points_ptr = (Point * len(points))(*sdlpts)

        if color is None:
            ret = draw_lines(self.sdlrenderer, points_ptr, len(points))
        else:
            tmp = self.color
            self.color = color
            ret = draw_lines(self.sdlrenderer, points_ptr, len(points))
            self.color = tmp

        if ret < 0:
            raise_sdl_err("drawing lines to the renderer")

    def draw_point(self, points, color=None):
        """Draws one or more points on the rendering context.

        .. note::
           Subpixel rendering (i.e. using floats as pixel coordinates) requires
           SDL 2.0.10 or newer.

        Args:
            points (list): A list of ``(x, y)`` coordinates or
                :obj:`~sdl2.SDL_Point` objects defining the set of points to
                draw.
            color (:obj:`~sdl2.ext.Color`, optional): The color with which to
                draw the points. If not specified, the renderer's current
                :attr:`color` will be used.

        """
        if dll.version < 2010:
            draw_points = render.SDL_RenderDrawPoints
            Point = rect.SDL_Point
        else:
            draw_points = render.SDL_RenderDrawPointsF
            Point = rect.SDL_FPoint

        points = _sanitize_points(points)
        sdlpts = []
        for p in points:
            x, y = p
            sdlpts.append(Point(x, y))
        points_ptr = (Point * len(points))(*sdlpts)

        if color is None:
            ret = draw_points(self.sdlrenderer, points_ptr, len(points))
        else:
            tmp = self.color
            self.color = color
            ret = draw_points(self.sdlrenderer, points_ptr, len(points))
            self.color = tmp

        if ret < 0:
            raise_sdl_err("drawing points to the renderer")

    def draw_rect(self, rects, color=None):
        """Draws one or more rectangles on the rendering context.

        Rectangles can be specified as 4-item ``(x, y, w, h)`` tuples,
        :obj:`~sdl2.rect.SDL_Rect` objects, or a list containing multiple
        rectangles in either format.

        .. note::
           Subpixel rendering (i.e. using floats as pixel coordinates) requires
           SDL 2.0.10 or newer.

        Args:
            rects (tuple, :obj:`~sdl2.SDL_Rect`, list): The rectangle(s) to draw
                to the rendering context.
            color (:obj:`~sdl2.ext.Color`, optional): The color with which to
                draw the rectangle(s). If not specified, the renderer's current
                :attr:`color` will be used.

        """
        if dll.version < 2010:
            draw_rects = render.SDL_RenderDrawRects
            Rect = rect.SDL_Rect
        else:
            draw_rects = render.SDL_RenderDrawRectsF
            Rect = rect.SDL_FRect

        rects = _sanitize_rects(rects)
        sdlrects = []
        for r in rects:
            x, y, w, h = r
            sdlrects.append(Rect(x, y, w, h))
        rects_ptr = (Rect * len(rects))(*sdlrects)

        if color is None:
            ret = draw_rects(self.sdlrenderer, rects_ptr, len(rects))
        else:
            tmp = self.color
            self.color = color
            ret = draw_rects(self.sdlrenderer, rects_ptr, len(rects))
            self.color = tmp
    
        if ret < 0:
            raise_sdl_err("drawing rectangles to the renderer")

    def fill(self, rects, color=None):
        """Fills one or more rectangular regions the rendering context.

        Fill regions can be specified as 4-item ``(x, y, w, h)`` tuples,
        :obj:`~sdl2.rect.SDL_Rect` objects, or a list containing multiple
        rectangles in either format.

        .. note::
           Subpixel rendering (i.e. using floats as pixel coordinates) requires
           SDL 2.0.10 or newer.

        Args:
            rects (tuple, :obj:`~sdl2.SDL_Rect`, list): The rectangle(s) to fill
                within the rendering context.
            color (:obj:`~sdl2.ext.Color`, optional): The color with which to
                fill the rectangle(s). If not specified, the renderer's current
                :attr:`color` will be used.

        """
        if dll.version < 2010:
            fill_rects = render.SDL_RenderFillRects
            Rect = rect.SDL_Rect
        else:
            fill_rects = render.SDL_RenderFillRectsF
            Rect = rect.SDL_FRect

        rects = _sanitize_rects(rects)
        sdlrects = []
        for r in rects:
            x, y, w, h = r
            sdlrects.append(Rect(x, y, w, h))
        rects_ptr = (Rect * len(rects))(*sdlrects)

        if color is None:
            ret = fill_rects(self.sdlrenderer, rects_ptr, len(rects))
        else:
            tmp = self.color
            self.color = color
            ret = fill_rects(self.sdlrenderer, rects_ptr, len(rects))
            self.color = tmp
    
        if ret < 0:
            raise_sdl_err("filling rectangles in the renderer")
