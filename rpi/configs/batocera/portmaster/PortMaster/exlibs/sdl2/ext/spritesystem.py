from .. import surface, rect, video, pixels, render, rwops

from .color import convert_to_color
from .err import SDLError
from .compat import isiterable
from .ebs import System
from .image import load_image, pillow_to_surface, _HASPIL
from .renderer import Renderer
from .sprite import Sprite, SoftwareSprite, TextureSprite
from .window import Window

__all__ = [
    "SpriteFactory", "SoftwareSpriteRenderSystem", "SpriteRenderSystem",
    "TextureSpriteRenderSystem", "TEXTURE", "SOFTWARE"
]


TEXTURE = 0
SOFTWARE = 1


class SpriteFactory(object):
    """A factory class for creating Sprite components."""
    def __init__(self, sprite_type=TEXTURE, **kwargs):
        """Creates a new SpriteFactory.

        The SpriteFactory can create TextureSprite or SoftwareSprite
        instances, depending on the sprite_type being passed to it,
        which can be SOFTWARE or TEXTURE. The additional kwargs are used
        as default arguments for creating sprites within the factory
        methods.
        """
        if sprite_type == TEXTURE:
            if "renderer" not in kwargs:
                raise ValueError("you have to provide a renderer=<arg> argument")
        elif sprite_type != SOFTWARE:
            raise ValueError("sprite_type must be TEXTURE or SOFTWARE")
        self._spritetype = sprite_type
        self.default_args = kwargs

    @property
    def sprite_type(self):
        """The sprite type created by the factory."""
        return self._spritetype

    def __repr__(self):
        stype = "TEXTURE"
        if self.sprite_type == SOFTWARE:
            stype = "SOFTWARE"
        return "SpriteFactory(sprite_type=%s, default_args=%s)" % \
            (stype, self.default_args)

    def create_sprite_render_system(self, *args, **kwargs):
        """Creates a new SpriteRenderSystem.

        For TEXTURE mode, the passed args and kwargs are ignored and the
        Renderer or SDL_Renderer passed to the SpriteFactory is used.
        """
        if self.sprite_type == TEXTURE:
            return TextureSpriteRenderSystem(self.default_args["renderer"])
        else:
            return SoftwareSpriteRenderSystem(*args, **kwargs)

    def from_image(self, img):
        """Creates a Sprite from the passed PIL.Image or image file name."""
        if _HASPIL:
            from PIL.Image import Image
            if isinstance(img, Image):
                return self.from_surface(pillow_to_surface(img))
        return self.from_surface(load_image(img), True)

    def from_surface(self, tsurface, free=False):
        """Creates a Sprite from the passed SDL_Surface.

        If free is set to True, the passed surface will be freed
        automatically.
        """
        if self.sprite_type == TEXTURE:
            renderer = self.default_args["renderer"]
            texture = render.SDL_CreateTextureFromSurface(renderer.sdlrenderer,
                                                          tsurface)
            if not texture:
                raise SDLError()
            sprite = TextureSprite(texture.contents)
            if free:
                surface.SDL_FreeSurface(tsurface)
            return sprite
        elif self.sprite_type == SOFTWARE:
            return SoftwareSprite(tsurface, free)
        raise ValueError("sprite_type must be TEXTURE or SOFTWARE")

    def from_object(self, obj):
        """Creates a Sprite from an arbitrary object."""
        if self.sprite_type == TEXTURE:
            rw = rwops.rw_from_object(obj)
            # TODO: support arbitrary objects.
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            return self.from_surface(imgsurface.contents, True)
        elif self.sprite_type == SOFTWARE:
            rw = rwops.rw_from_object(obj)
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            return SoftwareSprite(imgsurface.contents, True)
        raise ValueError("sprite_type must be TEXTURE or SOFTWARE")

    def from_color(self, color, size, bpp=32, masks=None):
        """Creates a sprite with a certain color.
        """
        color = convert_to_color(color)
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        sfc = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp, rmask,
                                           gmask, bmask, amask)
        if not sfc:
            raise SDLError()
        fmt = sfc.contents.format
        if fmt.contents.Amask != 0:
            # Target has an alpha mask
            col = pixels.SDL_MapRGBA(fmt, color.r, color.g, color.b, color.a)
        else:
            col = pixels.SDL_MapRGB(fmt, color.r, color.g, color.b)
        ret = surface.SDL_FillRect(sfc, None, col)
        if ret == -1:
            raise SDLError()
        return self.from_surface(sfc.contents, True)

    def from_text(self, text, **kwargs):
        """Creates a Sprite from a string of text."""
        args = self.default_args.copy()
        args.update(kwargs)
        fontmanager = args['fontmanager']
        sfc = fontmanager.render(text, **args)
        return self.from_surface(sfc, free=True)

    def create_sprite(self, **kwargs):
        """Creates an empty Sprite.

        This will invoke create_software_sprite() or
        create_texture_sprite() with the passed arguments and the set
        default arguments.
        """
        args = self.default_args.copy()
        args.update(kwargs)
        if self.sprite_type == TEXTURE:
            return self.create_texture_sprite(**args)
        else:
            return self.create_software_sprite(**args)

    def create_software_sprite(self, size, bpp=32, masks=None):
        """Creates a software sprite.

        A size tuple containing the width and height of the sprite and a
        bpp value, indicating the bits per pixel to be used, need to be
        provided.
        """
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        imgsurface = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp,
                                                  rmask, gmask, bmask, amask)
        if not imgsurface:
            raise SDLError()
        return SoftwareSprite(imgsurface.contents, True)

    def create_texture_sprite(self, renderer, size,
                              pformat=pixels.SDL_PIXELFORMAT_RGBA8888,
                              access=render.SDL_TEXTUREACCESS_STATIC):
        """Creates a texture sprite.

        A size tuple containing the width and height of the sprite needs
        to be provided.

        TextureSprite objects are assumed to be static by default,
        making it impossible to access their pixel buffer in favour for
        faster copy operations. If you need to update the pixel data
        frequently or want to use the texture as target for rendering
        operations, access can be set to the relevant
        SDL_TEXTUREACCESS_* flag.
        """
        if isinstance(renderer, render.SDL_Renderer):
            sdlrenderer = renderer
        elif isinstance(renderer, Renderer):
            sdlrenderer = renderer.sdlrenderer
        else:
            raise TypeError("renderer must be a Renderer or SDL_Renderer")
        texture = render.SDL_CreateTexture(sdlrenderer, pformat, access,
                                           size[0], size[1])
        if not texture:
            raise SDLError()
        return TextureSprite(texture.contents)


class SpriteRenderSystem(System):
    """A rendering system for Sprite components.

    This is a base class for rendering systems capable of drawing and
    displaying Sprite-based objects. Inheriting classes need to
    implement the rendering capability by overriding the render()
    method.
    """
    def __init__(self):
        super(SpriteRenderSystem, self).__init__()
        self.componenttypes = (Sprite,)
        self._sortfunc = lambda e: e.depth

    def render(self, sprites, x=None, y=None):
        """Renders the passed sprites.

        This is a no-op function and needs to be implemented by inheriting
        classes.
        """
        pass

    def process(self, world, components):
        """Draws the passed SoftSprite objects on the Window's surface."""
        self.render(sorted(components, key=self._sortfunc))

    @property
    def sortfunc(self):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        return self._sortfunc

    @sortfunc.setter
    def sortfunc(self, value):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        if not callable(value):
            raise TypeError("sortfunc must be callable")
        self._sortfunc = value


class SoftwareSpriteRenderSystem(SpriteRenderSystem):
    """A rendering system for SoftwareSprite components.

    The SoftwareSpriteRenderSystem class uses a Window as drawing device to
    display Sprite surfaces. It uses the Window's internal SDL surface as
    drawing context, so that GL operations, such as texture handling or
    using SDL renderers is not possible.
    """
    def __init__(self, window):
        """Creates a new SoftwareSpriteRenderSystem for a specific Window."""
        super(SoftwareSpriteRenderSystem, self).__init__()
        if isinstance(window, Window):
            self.window = window.window
        elif isinstance(window, video.SDL_Window):
            self.window = window
        else:
            raise TypeError("unsupported window type")
        self.target = window
        sfc = video.SDL_GetWindowSurface(self.window)
        if not sfc:
            raise SDLError()
        self.surface = sfc.contents
        self.componenttypes = (SoftwareSprite,)

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite) on the Window's surface.

        x and y are optional arguments that can be used as relative drawing
        location for sprites. If set to None, the location information of the
        sprites are used. If set and sprites is an iterable, such as a list of
        SoftwareSprite objects, x and y are relative location values that will
        be added to each individual sprite's position. If sprites is a single
        SoftwareSprite, x and y denote the absolute position of the
        SoftwareSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        if isiterable(sprites):
            blit_surface = surface.SDL_BlitSurface
            imgsurface = self.surface
            x = x or 0
            y = y or 0
            for sprite in sprites:
                r.x = x + sprite.x
                r.y = y + sprite.y
                blit_surface(sprite.surface, None, imgsurface, r)
        else:
            r.x = sprites.x
            r.y = sprites.y
            if x is not None and y is not None:
                r.x = x
                r.y = y
            surface.SDL_BlitSurface(sprites.surface, None, self.surface, r)
        video.SDL_UpdateWindowSurface(self.window)


class TextureSpriteRenderSystem(SpriteRenderSystem):
    """A rendering system for TextureSprite components.

    The TextureSpriteRenderSystem class uses a SDL_Renderer as drawing
    device to display TextureSprite objects.
    """
    def __init__(self, target):
        """Creates a new TextureSpriteRenderSystem.

        target can be a Window, SDL_Window, Renderer or SDL_Renderer.
        If it is a Window or SDL_Window instance, a Renderer will be
        created to acquire the SDL_Renderer.
        """
        super(TextureSpriteRenderSystem, self).__init__()
        if isinstance(target, (Window, video.SDL_Window)):
            # Create a Renderer for the window and use that one.
            target = Renderer(target)

        if isinstance(target, Renderer):
            self._renderer = target  # Used to prevent GC
            sdlrenderer = target.sdlrenderer
        elif isinstance(target, render.SDL_Renderer):
            sdlrenderer = target
        else:
            raise TypeError("unsupported object type")
        self.sdlrenderer = sdlrenderer
        self.componenttypes = (TextureSprite,)

    def __del__(self):
        self.sdlrenderer = None
        if hasattr(self, "_renderer"):
            self._renderer = None

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite).

        x and y are optional arguments that can be used as relative
        drawing location for sprites. If set to None, the location
        information of the sprites are used. If set and sprites is an
        iterable, such as a list of TextureSprite objects, x and y are
        relative location values that will be added to each individual
        sprite's position. If sprites is a single TextureSprite, x and y
        denote the absolute position of the TextureSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        rcopy = render.SDL_RenderCopyEx
        if isiterable(sprites):
            renderer = self.sdlrenderer
            x = x or 0
            y = y or 0
            for sprite in sprites:
                r.x = x + sprite.x
                r.y = y + sprite.y
                r.w, r.h = sprite.size
                if rcopy(renderer, sprite.texture, None, r, sprite.angle,
                         sprite.center, sprite.flip) == -1:
                    raise SDLError()
        else:
            r.x = sprites.x
            r.y = sprites.y
            r.w, r.h = sprites.size
            if x is not None and y is not None:
                r.x = x
                r.y = y
            if rcopy(self.sdlrenderer, sprites.texture, None, r, sprites.angle,
                     sprites.center, sprites.flip) == -1:
                raise SDLError()
        render.SDL_RenderPresent(self.sdlrenderer)
