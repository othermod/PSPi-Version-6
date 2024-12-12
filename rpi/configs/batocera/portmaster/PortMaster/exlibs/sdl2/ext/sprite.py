import abc
from ctypes import byref, c_int

from .. import surface, rect, render
from ..stdinc import Uint32

from .err import SDLError
from .surface import subsurface

__all__ = ["Sprite", "SoftwareSprite", "TextureSprite"]


class Sprite(object):
    """A simple 2D object."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Creates a new Sprite."""
        super(Sprite, self).__init__()
        self.x = 0
        self.y = 0
        self.depth = 0

    @property
    def position(self):
        """The top-left position of the Sprite as tuple."""
        return self.x, self.y

    @position.setter
    def position(self, value):
        """The top-left position of the Sprite as tuple."""
        self.x = value[0]
        self.y = value[1]

    @property
    @abc.abstractmethod
    def size(self):
        """The size of the Sprite as tuple."""
        return

    @property
    def area(self):
        """The rectangular area occupied by the Sprite."""
        w, h = self.size
        return (self.x, self.y, self.x + w, self.y + h)


class SoftwareSprite(Sprite):
    """A simple, visible, pixel-based 2D object using software buffers."""
    def __init__(self, imgsurface, free):
        """Creates a new SoftwareSprite."""
        super(SoftwareSprite, self).__init__()
        self.free = free
        if isinstance(imgsurface, surface.SDL_Surface):
            self.surface = imgsurface
        elif "SDL_Surface" in str(type(imgsurface)):
            self.surface = imgsurface.contents
        else:
            raise TypeError("imgsurface must be an SDL_Surface")

    def __del__(self):
        """Releases the bound SDL_Surface, if it was created by the
        SoftwareSprite.
        """
        imgsurface = getattr(self, "surface", None)
        if self.free and imgsurface is not None:
            surface.SDL_FreeSurface(imgsurface)
        self.surface = None

    @property
    def size(self):
        """The size of the SoftwareSprite as tuple."""
        return self.surface.w, self.surface.h

    def subsprite(self, area):
        """Creates another SoftwareSprite from a part of the SoftwareSprite.

        The two sprites share pixel data, so if the parent sprite's surface is
        not managed by the sprite (free is False), you will need to keep it
        alive while the subsprite exists."""
        ssurface = subsurface(self.surface, area)
        ssprite = SoftwareSprite(ssurface, True)
        # Keeps the parent surface alive until subsprite is freed
        if self.free:
            ssprite._parent = self
        return ssprite

    def __repr__(self):
        return "SoftwareSprite(size=%s, bpp=%d)" % \
            (self.size, self.surface.format.contents.BitsPerPixel)


class TextureSprite(Sprite):
    """A simple, visible, texture-based 2D object, using a renderer."""
    def __init__(self, texture, free=True):
        """Creates a new TextureSprite."""
        super(TextureSprite, self).__init__()
        self.texture = texture
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(texture, byref(flags), byref(access),
                                      byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        self.free = free
        self.angle = 0.0
        self.flip = render.SDL_FLIP_NONE
        self._size = w.value, h.value
        self._center = None

    def __del__(self):
        """Releases the bound SDL_Texture."""
        if self.free:
            if self.texture != None:
                render.SDL_DestroyTexture(self.texture)
        self.texture = None

    @property
    def center(self):
        """The center of the TextureSprite as tuple."""
        return self._center

    @center.setter
    def center(self, value):
        """Sets the center of the TextureSprite."""
        if value != None:
            self._center = rect.SDL_Point(value[0], value[1])
        else:
            self._center = None

    @property
    def size(self):
        """The size of the TextureSprite as tuple."""
        return self._size

    def __repr__(self):
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(self.texture, byref(flags),
                                      byref(access), byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        if self.center:
            return "TextureSprite(format=%d, access=%d, size=%s, angle=%f, center=%s)" % \
                (flags.value, access.value, (w.value, h.value), self.angle,
                 (self.center.x, self.center.y))
        else:
            return "TextureSprite(format=%d, access=%d, size=%s, angle=%f)" % \
                (flags.value, access.value, (w.value, h.value), self.angle)
