from .. import surface, rect, pixels
from .err import SDLError, raise_sdl_err
from .sprite import SoftwareSprite
from .surface import _get_target_surface
from .image import load_bmp

__all__ = ["BitmapFont"]


class BitmapFont(object):
    """A class for rendering text using a given bitmap font.

    This class takes an image of equally-spaced font characters and a font map
    indicating the location of each character on the image, and uses these to
    render text using the given font. This class is based on base SDL2 functions
    and does not require the SDL_ttf library to be installed.

    The font mapping table is a list of strings, with each string representing
    a row of characters on the font image surface. Each character within each
    line is assumed to be of equal height and width, but this can be adjusted
    using the :meth:`remap` method.
    
    For example, the built-in bitmap font ``font.bmp`` has the following layout:

    .. image:: images/font.png

    The default font mapping table, which matches the layout of ``font.bmp``,
    looks like this::

       fontmap = [
           '0123456789',
           'ABCDEFGHIJ',
           'KLMNOPQRST',
           'UVWXYZ    ',
           'abcdefghij',
           'klmnopqrst',
           'uvwxyz    ',
           ',;.:!?+-()',
        ]
    
    Args:
        font_img (:obj:`SDL_Surface` or str): A surface or path to a file
            containing a valid bitmap (``.bmp``) font image.
        size (tuple, optional): A ``(width, height)`` tuple defining the size of
            each character in the bitmap font. If not specified, this will be
            inferred automatically from the fontmap and font image.
        fontmap (list, optional): A list of strings defining the locations of
            characters in the font image. If not specified, the default font map
            defined above will be used.

    """
    DEFAULTMAP = [
        "0123456789",
        "ABCDEFGHIJ",
        "KLMNOPQRST",
        "UVWXYZ    ",
        "abcdefghij",
        "klmnopqrst",
        "uvwxyz    ",
        ",;.:!?+-()",
    ]

    def __init__(self, font_img, size=None, mapping=None):
        if hasattr(font_img, "upper"):  # if string
            self.surface = load_bmp(font_img)
        elif isinstance(font_img, SoftwareSprite):
            self.surface = font_img.surface
            self._sprite = font_img  # prevent GC on the Sprite
        elif isinstance(font_img, surface.SDL_Surface):
            self.surface = font_img
        elif "SDL_Surface" in str(type(font_img)):
            self.surface = font_img.contents
        else:
            raise TypeError("font_img must be a Sprite or SDL_Surface")

        if mapping is None:
            self.mapping = list(BitmapFont.DEFAULTMAP)
        else:
            self.mapping = mapping

        if not size:
            map_rows = len(self.mapping)
            map_cols = len(self.mapping[0])
            surf_size = (float(self.surface.w), float(self.surface.h))
            size = (int(surf_size[0] / map_cols), int(surf_size[1] / map_rows))
        self.size = size[0], size[1]

        self.offsets = {}
        self._max_height = self.size[1]
        self._calculate_offsets()

    def _calculate_offsets(self):
        # Calculates the internal character offsets for each line
        self.offsets = {}
        x, y = 0, 0
        w, h = self.size
        for line in self.mapping:
            x = 0
            for c in line:
                if c not in self.offsets.keys():
                    self.offsets[c] = rect.SDL_Rect(x, y, w, h)
                x += w
            y += h

    def _validate_chars(self, text):
        e = "The character '{0}' does not exist within the current font mapping"
        for ch in text:
            if ch != "\n" and ch not in self.offsets.keys():
                raise ValueError(e.format(ch))

    def _get_rendered_size(self, text, line_h):
        line_h = self._max_height if not line_h else line_h
        text_w, text_h = (0, 0)
        lines = text.split("\n")
        for line in lines:
            line_w = 0
            for c in line:
                charsize = self.offsets[c]
                line_w += charsize.w
            if line_w > text_w:
                text_w = line_w
            text_h += line_h
        return (text_w, text_h)

    def _render_text(self, target, fontsf, lines, line_h, offset=(0, 0)):
        line_h = self._max_height if not line_h else line_h
        dstr = rect.SDL_Rect(0, 0, 0, 0)
        y = offset[1]
        for line in lines:
            x = offset[0]
            for c in line:
                dstr.x = x
                dstr.y = y + (line_h - self.offsets[c].h)
                surface.SDL_BlitSurface(fontsf, self.offsets[c], target, dstr)
                x += self.offsets[c].w
            y += line_h
        return (x, y)

    def remap(self, c, x, y, w, h):
        """Updates the source rectangle for a given font character.

        This method can be used to fine-tune the character mappings in the font
        image to produce better spacing in the rendered text.

        Args:
            c (str): The character to remap in the font image.
            x (int): The x coordinate (in pixels) of the top-left corner of the
                new rectangle for the character.
            y (int): The y coordinate (in pixels) of the top-left corner of the
                new rectangle for the character.
            w (int): The width (in pixels) of the new rectangle for the
                character.
            h (int): The height (in pixels) of the new rectangle for the
                character.

        """
        if len(c) > 1:
            raise ValueError("Can only remap one character at a time.")
        self._validate_chars(c)
        x, y, w, h = [int(i) for i in (x, y, w, h)]
        if any([w < 1, h < 1]):
            raise ValueError("Width and height must both be positive integers.")
        surf_w, surf_h = (self.surface.w, self.surface.h)
        if x < 0 or y < 0 or x+w >= surf_w or y+h >= surf_h:
            e = "Character rectangle cannot exceed the bounds of the font image"
            raise ValueError(e + " ({0}, {1}).".format(surf_w, surf_h))

        self.offsets[c] = rect.SDL_Rect(x, y, w, h)
        if h > self._max_height:
            self._max_height = h

    def render(self, text, bpp=None):
        # Deprecated: replaced by render_text, which returns a surface
        self._validate_chars(text)
        lines = text.split("\n")

        tw, th = self._get_rendered_size(text, None)
        if bpp is None:
            bpp = self.surface.format.contents.BitsPerPixel
        sf = surface.SDL_CreateRGBSurface(0, tw, th, bpp, 0, 0, 0, 0)
        if not sf:
            raise SDLError()
        imgsurface = SoftwareSprite(sf.contents, False)

        self._render_text(imgsurface.surface, self.surface, lines, None)
        return imgsurface

    def render_text(self, text, line_h=None, as_argb=True):
        """Renders a string of text to a new surface.

        If a newline character (``\\n``) is encountered in the string, it will
        be rendered as a line break in the rendered text.

        By default, this function also converts the rendered text from the native
        format of the font image to 32-bit ARGB, for consistency across functions
        and better compatibility with SDL2 renderers. To disable ARGB conversion,
        set the ``as_argb`` parameter to ``False``.

        Args:
            text (str): The string of text to render.
            line_h (int, optional): The line height (in pixels) to use for each
                line of the rendered text. If not specified, the maximum
                character height for the font will be used. Defaults to ``None``.
            as_argb (bool, optional): Whether the output surface should be
                converted to 32-bit ARGB pixel format or left as-is. Defaults to
                ``True`` (convert to ARGB).

        Returns:
            :obj:`~sdl2.SDL_Surface`: A surface containing the rendered text.

        Raises:
            ValueError: If a character in the text is not provided by the
            current font.

        """
        self._validate_chars(text)
        lines = text.split("\n")

        # Create a new surface with the same format as the font image
        tw, th = self._get_rendered_size(text, line_h)
        fmt = self.surface.format.contents.format
        bpp = 32  # according to SDL2 source, this has no effect
        sf = surface.SDL_CreateRGBSurfaceWithFormat(0, tw, th, bpp, fmt)
        if not sf:
            raise_sdl_err("creating the font surface")

        # Render text to the new surface, converting pixel format if necessary
        self._render_text(sf.contents, self.surface, lines, line_h)
        if as_argb and fmt != pixels.SDL_PIXELFORMAT_ARGB8888:
            out_fmt = pixels.SDL_AllocFormat(pixels.SDL_PIXELFORMAT_ARGB8888)
            sf_argb = surface.SDL_ConvertSurface(sf, out_fmt, 0)
            surface.SDL_FreeSurface(sf)
            sf = sf_argb
            if not sf:
                raise_sdl_err("converting rendered text to ARGB format")

        return sf.contents

    def render_on(self, target, text, offset=(0, 0), line_h=None):
        """Renders a string of text to an existing surface.

        If a newline character (``\\n``) is encountered in the string, it will
        be rendered as a line break in the rendered text.

        Args:
            target (:obj:`~sdl2.SDL_Surface`): The surface on which to render
                the given string.
            text (str): The string of text to render to the target surface.
            offset (tuple, optional): The ``(x, y)`` coordinates of the target
                surface on which the top-left corner of the rendered text will
                be placed. Defaults to ``(0, 0)``.
            line_h (int, optional): The line height (in pixels) to use for each
                line of the rendered text. If not specified, the maximum
                character height for the font will be used. Defaults to ``None``.

        Returns:
            tuple: The ``(x1, y1, x2, y2)`` rectangle of the target surface on
            which the text was rendered.

        Raises:
            ValueError: If a character in the text is not provided by the
            current font.

        """
        x1, y1 = offset
        dest = rect.SDL_Rect(x1, y1, 0, 0)
        target = _get_target_surface(target)

        sf = self.render_text(text, line_h, as_argb=False)
        ret = surface.SDL_BlitSurface(sf, None, target, dest)
        if ret != 0:
            raise_sdl_err("copying the text to the target surface")

        return (x1, y1, x1 + sf.w, y1 + sf.h)

    def contains(self, c):
        """Checks whether a given character is mapped within the font.
        
        Args:
            c (str): The character to check for within the font map.

        Returns:
            bool: ``True`` if the font contains the character, otherwise
            ``False``.
    
        """
        return c in self.offsets

    def can_render(self, text):
        # Deprecated: already throws informative exception on missing character
        lines = text.split("\n")
        for line in lines:
            for c in line:
                if c != ' ' and c not in self.offsets:
                    return False
        return True
