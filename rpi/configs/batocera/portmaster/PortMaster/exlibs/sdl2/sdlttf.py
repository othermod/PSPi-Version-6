import os
from ctypes import c_int, c_uint, c_long, c_char_p, c_void_p
from ctypes import POINTER as _P
from .dll import DLL, SDLFunc, AttributeDict
from .version import SDL_version, SDL_VERSIONNUM
from .rwops import SDL_RWops
from .stdinc import Uint16, Uint32, SDL_bool
from .pixels import SDL_Color
from .surface import SDL_Surface
from .error import SDL_GetError, SDL_SetError

__all__ = [
    # Opaque Types
    "TTF_Font",

    # Enums
    "hb_direction_t",
    "HB_DIRECTION_INVALID", "HB_DIRECTION_LTR", "HB_DIRECTION_RTL",
    "HB_DIRECTION_TTB", "HB_DIRECTION_BTT",

    # Defines
    "SDL_TTF_MAJOR_VERSION", "SDL_TTF_MINOR_VERSION", "SDL_TTF_PATCHLEVEL",
    "TTF_MAJOR_VERSION", "TTF_MINOR_VERSION", "TTF_PATCHLEVEL",
    "UNICODE_BOM_NATIVE", "UNICODE_BOM_SWAPPED",
    "TTF_STYLE_NORMAL", "TTF_STYLE_BOLD", "TTF_STYLE_ITALIC",
    "TTF_STYLE_UNDERLINE", "TTF_STYLE_STRIKETHROUGH",
    "TTF_HINTING_NORMAL", "TTF_HINTING_LIGHT", "TTF_HINTING_MONO",
    "TTF_HINTING_NONE", "TTF_HINTING_LIGHT_SUBPIXEL",

    # Macro Functions
    "SDL_TTF_VERSION",  "TTF_VERSION", "SDL_TTF_COMPILEDVERSION",
    "SDL_TTF_VERSION_ATLEAST", "HB_TAG",

    # Function Aliases
    "TTF_RenderText", "TTF_RenderUTF8", "TTF_RenderUNICODE",
    "TTF_SetError", "TTF_GetError",

    # Python Functions
    "get_dll_file",
]


try:
    dll = DLL("SDL2_ttf", ["SDL2_ttf", "SDL2_ttf-2.0"],
              os.getenv("PYSDL2_DLL_PATH"))
except RuntimeError as exc:
    raise ImportError(exc)

def get_dll_file():
    """Gets the file name of the loaded SDL2_ttf library."""
    return dll.libfile

_bind = dll.bind_function


# Constants, enums, type definitions, and macros

SDL_TTF_MAJOR_VERSION = 2
SDL_TTF_MINOR_VERSION = 20
SDL_TTF_PATCHLEVEL = 0

def SDL_TTF_VERSION(x):
    x.major = SDL_TTF_MAJOR_VERSION
    x.minor = SDL_TTF_MINOR_VERSION
    x.patch = SDL_TTF_PATCHLEVEL

TTF_MAJOR_VERSION = SDL_TTF_MAJOR_VERSION
TTF_MINOR_VERSION = SDL_TTF_MINOR_VERSION
TTF_PATCHLEVEL = SDL_TTF_PATCHLEVEL
TTF_VERSION = SDL_TTF_VERSION

SDL_TTF_COMPILEDVERSION = SDL_VERSIONNUM(
    SDL_TTF_MAJOR_VERSION, SDL_TTF_MINOR_VERSION, SDL_TTF_PATCHLEVEL
)
SDL_TTF_VERSION_ATLEAST = lambda x, y, z: (SDL_TTF_COMPILEDVERSION >= SDL_VERSIONNUM(x, y, z))

UNICODE_BOM_NATIVE = 0xFEFF
UNICODE_BOM_SWAPPED = 0xFFFE

TTF_STYLE_NORMAL = 0x00
TTF_STYLE_BOLD = 0x01
TTF_STYLE_ITALIC = 0x02
TTF_STYLE_UNDERLINE = 0x04
TTF_STYLE_STRIKETHROUGH = 0x08

TTF_HINTING_NORMAL = 0
TTF_HINTING_LIGHT = 1
TTF_HINTING_MONO = 2
TTF_HINTING_NONE = 3
TTF_HINTING_LIGHT_SUBPIXEL = 4

TTF_WRAPPED_ALIGN_LEFT = 0
TTF_WRAPPED_ALIGN_CENTER = 1
TTF_WRAPPED_ALIGN_RIGHT = 2

TTF_Direction = c_int
TTF_DIRECTION_LTR = 0
TTF_DIRECTION_RTL = 1
TTF_DIRECTION_TTB = 2
TTF_DIRECTION_BTT = 3

class TTF_Font(c_void_p):
    """The opaque data type for fonts opened using the TTF library.
    
    This contains all data associated with a loaded font. Once you are done
    with a :obj:`TTF_Font`, it should be freed using :func:`TTF_CloseFont`.

    """
    pass


# Some additional definitions from HarfBuzz for SetDirection/SetScript

hb_direction_t = c_int
HB_DIRECTION_INVALID = 0
HB_DIRECTION_LTR = 4
HB_DIRECTION_RTL = 5
HB_DIRECTION_TTB = 6
HB_DIRECTION_BTT = 7

def HB_TAG(c1, c2, c3, c4):
    """Converts a 4-character ISO 15924 code into a HarfBuzz script constant.

    A full list of possible 4-character script codes can be found
    here: https://unicode.org/iso15924/iso15924-codes.html

    Args:
        c1 (str): The first character of the code.
        c2 (str): The second character of the code.
        c3 (str): The third character of the code.
        c4 (str): The fourth character of the code.

    Returns:
        int: The HarfBuzz contstant corresponding to the given script.

    """
    c1, c2, c3, c4 = [ord(c) & 0xFF for c in (c1, c2, c3, c4)]
    return (c1 << 24 | c2 << 16 | c3 << 8 | c4)


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("TTF_Linked_Version", None, _P(SDL_version)),
    SDLFunc("TTF_GetFreeTypeVersion", [_P(c_int), _P(c_int), _P(c_int)], added='2.0.18'),
    SDLFunc("TTF_GetHarfBuzzVersion", [_P(c_int), _P(c_int), _P(c_int)], added='2.0.18'),
    SDLFunc("TTF_ByteSwappedUNICODE", [c_int], None),
    SDLFunc("TTF_Init", None, c_int),
    SDLFunc("TTF_OpenFont", [c_char_p, c_int], _P(TTF_Font)),
    SDLFunc("TTF_OpenFontIndex", [c_char_p, c_int, c_long], _P(TTF_Font)),
    SDLFunc("TTF_OpenFontRW", [_P(SDL_RWops), c_int, c_int], _P(TTF_Font)),
    SDLFunc("TTF_OpenFontIndexRW", [_P(SDL_RWops), c_int, c_int, c_long], _P(TTF_Font)),
    SDLFunc("TTF_OpenFontDPI", [c_char_p, c_int, c_uint, c_uint], _P(TTF_Font), added='2.0.18'),
    SDLFunc("TTF_OpenFontIndexDPI",
        [c_char_p, c_int, c_long, c_uint, c_uint],
        returns = _P(TTF_Font), added = '2.0.18'
    ),
    SDLFunc("TTF_OpenFontDPIRW",
        [_P(SDL_RWops), c_int, c_int, c_uint, c_uint],
        returns = _P(TTF_Font), added = '2.0.18'
    ),
    SDLFunc("TTF_OpenFontIndexDPIRW",
        [_P(SDL_RWops), c_int, c_int, c_long, c_uint, c_uint],
        returns = _P(TTF_Font), added = '2.0.18'
    ),
    SDLFunc("TTF_SetFontSize", [_P(TTF_Font), c_int], c_int, added='2.0.18'),
    SDLFunc("TTF_SetFontSizeDPI", [_P(TTF_Font), c_int, c_uint, c_uint], c_int, added='2.0.18'),
    SDLFunc("TTF_GetFontStyle", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_SetFontStyle", [_P(TTF_Font), c_int], None),
    SDLFunc("TTF_GetFontOutline", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_SetFontOutline", [_P(TTF_Font), c_int], None),
    SDLFunc("TTF_GetFontHinting", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_SetFontHinting", [_P(TTF_Font), c_int], None),
    SDLFunc("TTF_GetFontWrappedAlign", [_P(TTF_Font)], c_int, added='2.20.0'),
    SDLFunc("TTF_SetFontWrappedAlign", [_P(TTF_Font), c_int], None, added='2.20.0'),
    SDLFunc("TTF_FontHeight", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_FontAscent", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_FontDescent", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_FontLineSkip", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_GetFontKerning", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_SetFontKerning", [_P(TTF_Font), c_int]),
    SDLFunc("TTF_FontFaces", [_P(TTF_Font)], c_long),
    SDLFunc("TTF_FontFaceIsFixedWidth", [_P(TTF_Font)], c_int),
    SDLFunc("TTF_FontFaceFamilyName", [_P(TTF_Font)], c_char_p),
    SDLFunc("TTF_FontFaceStyleName", [_P(TTF_Font)], c_char_p),
    SDLFunc("TTF_GlyphIsProvided", [_P(TTF_Font), Uint16], c_int),
    SDLFunc("TTF_GlyphIsProvided32", [_P(TTF_Font), Uint32], c_int, added='2.0.18'),
    SDLFunc("TTF_GlyphMetrics",
        [_P(TTF_Font), Uint16, _P(c_int), _P(c_int), _P(c_int), _P(c_int), _P(c_int)],
        returns = c_int
    ),
    SDLFunc("TTF_GlyphMetrics32",
        [_P(TTF_Font), Uint32, _P(c_int), _P(c_int), _P(c_int), _P(c_int), _P(c_int)],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("TTF_SizeText", [_P(TTF_Font), c_char_p, _P(c_int), _P(c_int)], c_int),
    SDLFunc("TTF_SizeUTF8", [_P(TTF_Font), c_char_p, _P(c_int), _P(c_int)], c_int),
    SDLFunc("TTF_SizeUNICODE", [_P(TTF_Font), _P(Uint16), _P(c_int), _P(c_int)], c_int),
    SDLFunc("TTF_MeasureText",
        [_P(TTF_Font), c_char_p, c_int, _P(c_int), _P(c_int)],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("TTF_MeasureUTF8",
        [_P(TTF_Font), c_char_p, c_int, _P(c_int), _P(c_int)],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("TTF_MeasureUNICODE",
        [_P(TTF_Font), _P(Uint16), c_int, _P(c_int), _P(c_int)],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("TTF_RenderText_Solid", [_P(TTF_Font), c_char_p, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderUTF8_Solid", [_P(TTF_Font), c_char_p, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderUNICODE_Solid", [_P(TTF_Font), _P(Uint16), SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderText_Solid_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderUTF8_Solid_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderUNICODE_Solid_Wrapped",
        [_P(TTF_Font), _P(Uint16), SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderGlyph_Solid", [_P(TTF_Font), Uint16, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderGlyph32_Solid",
        [_P(TTF_Font), Uint32, SDL_Color],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderText_Shaded",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderUTF8_Shaded",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderUNICODE_Shaded",
        [_P(TTF_Font), _P(Uint16), SDL_Color, SDL_Color],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderText_Shaded_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderUTF8_Shaded_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderUNICODE_Shaded_Wrapped",
        [_P(TTF_Font), _P(Uint16), SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderGlyph_Shaded",
        [_P(TTF_Font), Uint16, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderGlyph32_Shaded",
        [_P(TTF_Font), Uint32, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderText_Blended", [_P(TTF_Font), c_char_p, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderUTF8_Blended", [_P(TTF_Font), c_char_p, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderUNICODE_Blended", [_P(TTF_Font), _P(Uint16), SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderText_Blended_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderUTF8_Blended_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderUNICODE_Blended_Wrapped",
        [_P(TTF_Font), _P(Uint16), SDL_Color, Uint32],
        returns = _P(SDL_Surface)
    ),
    SDLFunc("TTF_RenderGlyph_Blended", [_P(TTF_Font), Uint16, SDL_Color], _P(SDL_Surface)),
    SDLFunc("TTF_RenderGlyph32_Blended",
        [_P(TTF_Font), Uint32, SDL_Color],
        returns = _P(SDL_Surface), added = '2.0.18'
    ),
    SDLFunc("TTF_RenderText_LCD",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderUTF8_LCD",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderUNICODE_LCD",
        [_P(TTF_Font), _P(Uint16), SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderText_LCD_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderUTF8_LCD_Wrapped",
        [_P(TTF_Font), c_char_p, SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderUNICODE_LCD_Wrapped",
        [_P(TTF_Font), _P(Uint16), SDL_Color, SDL_Color, Uint32],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderGlyph_LCD",
        [_P(TTF_Font), Uint16, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_RenderGlyph32_LCD",
        [_P(TTF_Font), Uint32, SDL_Color, SDL_Color],
        returns = _P(SDL_Surface), added = '2.20.0'
    ),
    SDLFunc("TTF_SetDirection", [c_int], c_int, added='2.0.18'),
    SDLFunc("TTF_SetScript", [c_int], c_int, added='2.0.18'),
    SDLFunc("TTF_SetFontDirection", [_P(TTF_Font), TTF_Direction], c_int, added='2.20.0'),
    SDLFunc("TTF_SetFontScriptName", [_P(TTF_Font), c_char_p], c_int, added='2.20.0'),
    SDLFunc("TTF_CloseFont", [_P(TTF_Font)]),
    SDLFunc("TTF_Quit"),
    SDLFunc("TTF_WasInit", None, c_int),
    SDLFunc("TTF_GetFontKerningSize", [_P(TTF_Font), c_int, c_int], c_int),
    SDLFunc("TTF_GetFontKerningSizeGlyphs",
        [_P(TTF_Font), Uint16, Uint16],
        returns = c_int, added = '2.0.14'
    ),
    SDLFunc("TTF_GetFontKerningSizeGlyphs32",
        [_P(TTF_Font), Uint32, Uint32],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("TTF_SetFontSDF", [_P(TTF_Font), SDL_bool], c_int, added='2.0.18'),
    SDLFunc("TTF_GetFontSDF", [_P(TTF_Font)], SDL_bool, added='2.0.18'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Python wrapper functions

def TTF_Linked_Version():
    """Gets the version of the dynamically-linked **SDL2_ttf** library.

    Returns:
        POINTER(:obj:`SDL_version`): A pointer to a structure containing the
        version of the SDL2_ttf library currently in use.

    """
    return _ctypes.TTF_Linked_Version()

def TTF_GetFreeTypeVersion(major, minor, patch):
    """Gets the version of the FreeType library currently linked by SDL2_ttf.

    This function returns the version numbers by reference, meaning that
    it needs to be called using pre-allocated ctypes variables (see
    :func:`TTF_GlyphMetrics` for an example).

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        major (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the major version number of the linked FreeType library.
        minor (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the minor version number of the linked FreeType library.
        patch (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the patch level of the linked FreeType library.

    """
    return _ctypes["TTF_GetFreeTypeVersion"](major, minor, patch)

def TTF_GetHarfBuzzVersion(major, minor, patch):
    """Gets the version of the HarfBuzz library currently linked by SDL2_ttf.

    This function returns the version numbers by reference, meaning that
    it needs to be called using pre-allocated ctypes variables (see
    :func:`TTF_GlyphMetrics` for an example).

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        major (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the major version number of the linked HarfBuzz library.
        minor (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the minor version number of the linked HarfBuzz library.
        patch (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the patch level of the linked HarfBuzz library.

    """
    return _ctypes["TTF_GetHarfBuzzVersion"](major, minor, patch)

def TTF_ByteSwappedUNICODE(swapped):
    """Tells the library whether UCS-2 unicode text is generally byteswapped.
   
    A unicode BOM character in a string will override this setting for the
    remainder of that string. The default mode is non-swapped, native
    endianness of the CPU. 

    Note that this only affects the behaviour of ``UNICODE`` (UCS-2) functions
    and has no effect on UTF8 functions.
   
    Args:
        swapped (int): If 0, native CPU endianness will be used. If not 0,
            UCS-2 data will be byte-swapped relative to native CPU endianness.

    """
    return _ctypes["TTF_ByteSwappedUNICODE"](swapped)

def TTF_Init():
    """Initializes the TTF engine.
   
    This function must be called before using other functions in this library
    (except for :func:`TTF_WasInit`). SDL does not have to be initialized
    before this function is called. 
   
    Returns:
        int: 0 if successful, or -1 on error.

    """
    return _ctypes["TTF_Init"]()


def TTF_OpenFont(file, ptsize):
    """Opens a font file at a given size.
    
    Point sizes are based on a DPI of 72. Use the :func:`TTF_GetError` function
    to check for any errors opening the font.
   
    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the font
            file to load.
        ptsize (int): The size (in points) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFont"](file, ptsize)

def TTF_OpenFontIndex(file, ptsize, index):
    """Opens a specific font face by index from a file at a given size.
    
    This function allows for loading a specific font face from a multi-face
    font. See :func:`TTF_OpenFont` for more information.
   
    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the font
            file to load.
        ptsize (int): The size (in points) at which to open the font.
        index (int): The index (from 0 to 15) of the font face to open. For
            font files with only one face, this should always be 0.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontIndex"](file, ptsize, index)

def TTF_OpenFontRW(src, freesrc, ptsize):
    """Opens a font from a file object at a given size.

    Point sizes are based on a DPI of 72. Use the :func:`TTF_GetError` function
    to check for any errors opening the font.

    .. note::
       The file object used to create the font (``src``) must be kept in
       memory until you are done with the font. Once the ``src`` has been freed,
       performing any additional operations with the returned :obj:`TTF_Font`
       will result in a hard Python crash (segmentation fault).
   
    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid font.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically when the resulting :obj:`TTF_Font` is closed (or
            if an error is encountered opening the font).
        ptsize (int): The size (in points) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontRW"](src, freesrc, ptsize)

def TTF_OpenFontIndexRW(src, freesrc, ptsize, index):
    """Opens a specific font face by index from a file object at a given size.
    
    This function allows for loading a specific font face from a multi-face
    font. See :func:`TTF_OpenFontRW` for more information.
   
    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid font.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically when the resulting :obj:`TTF_Font` is closed (or
            if an error is encountered opening the font).
        ptsize (int): The size (in points) at which to open the font.
        index (int): The index (from 0 to 15) of the font face to open. For
            font files with only one face, this should always be 0.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontIndexRW"](src, freesrc, ptsize, index)

def TTF_OpenFontDPI(file, ptsize, hdpi, vdpi):
    """Opens a font file at a given size and DPI.
    
    The font will be opened with the given horizontal and vertical target
    resolutions (in DPI). DPI scaling only applies to scalable fonts (e.g.
    TrueType). Use the :func:`TTF_GetError` function to check for any errors
    opening the font.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the font
            file to load.
        ptsize (int): The size (in points) at which to open the font.
        hdpi (int): The horizontal resolution (in DPI) at which to open the font.
        vdpi (int): The vertical resolution (in DPI) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontDPI"](file, ptsize, hdpi, vdpi)

def TTF_OpenFontIndexDPI(file, ptsize, index, hdpi, vdpi):
    """Opens a specific font face by index from a file at a given size and DPI.
    
    See :func:`TTF_OpenFontDPI` and `:func:`TTF_OpenFontIndex` for more
    information.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        file (bytes): A UTF8-encoded bytestring containing the path of the font
            file to load.
        ptsize (int): The size (in points) at which to open the font.
        index (int): The index (from 0 to 15) of the font face to open. For
            font files with only one face, this should always be 0.
        hdpi (int): The horizontal resolution (in DPI) at which to open the font.
        vdpi (int): The vertical resolution (in DPI) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontIndexDPI"](file, ptsize, index, hdpi, vdpi)

def TTF_OpenFontDPIRW(src, freesrc, ptsize, hdpi, vdpi):
    """Opens a font from a file object at a given size and DPI.

    See :func:`TTF_OpenFontDPI` and `:func:`TTF_OpenFontRW` for more
    information.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid font.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically when the resulting :obj:`TTF_Font` is closed (or
            if an error is encountered opening the font).
        ptsize (int): The size (in points) at which to open the font.
        hdpi (int): The horizontal resolution (in DPI) at which to open the font.
        vdpi (int): The vertical resolution (in DPI) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontDPIRW"](src, freesrc, ptsize, hdpi, vdpi)

def TTF_OpenFontIndexDPIRW(src, freesrc, ptsize, index, hdpi, vdpi):
    """Opens a font face by index from a file object at a given size and DPI.
    
    See :func:`TTF_OpenFontDPI` and `:func:`TTF_OpenFontIndexRW` for more
    information.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        src (:obj:`SDL_RWops`): A file object containing a valid font.
        freesrc (int): If non-zero, the provided file object will be closed and
            freed automatically when the resulting :obj:`TTF_Font` is closed (or
            if an error is encountered opening the font).
        ptsize (int): The size (in points) at which to open the font.
        index (int): The index (from 0 to 15) of the font face to open. For
            font files with only one face, this should always be 0.
        hdpi (int): The horizontal resolution (in DPI) at which to open the font.
        vdpi (int): The vertical resolution (in DPI) at which to open the font.
   
    Returns:
        POINTER(:obj:`TTF_Font`): A pointer to the opened font object, or a null
        pointer if there was an error.

    """
    return _ctypes["TTF_OpenFontIndexDPIRW"](src, freesrc, ptsize, index, hdpi, vdpi)

def TTF_SetFontSize(font, ptsize):
    """Changes the size of a TTF font object dynamically.

    Use :func:`TTF_GetError` to check for errors.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to update.
        ptsize (int): The new size (in points) to use for the font.

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["TTF_SetFontSize"](font, ptsize)

def TTF_SetFontSizeDPI(font, ptsize, hdpi, vdpi):
    """Changes the size and DPI of a TTF font object dynamically.

    Use :func:`TTF_GetError` to check for errors.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to update.
        ptsize (int): The new size (in points) to use for the font.
        hdpi (int): The new horizontal resolution (in DPI) at which to render
            the font.
        vdpi (int): The vertical resolution (in DPI) at which to render the
            font.

    Returns:
        int: 0 on success, or -1 on error.

    """
    return _ctypes["TTF_SetFontSizeDPI"](font, ptsize, hdpi, vdpi)


def TTF_GetFontStyle(font):
    """Retrieves the current rendering style of a given font.

    To check for the presence of a given style within a font, the return value
    of this function can be used with a bitwise ``&`` operator::

      style = TTF_GetFontStyle(font)
      is_bold = style & TTF_STYLE_BOLD == TTF_STYLE_BOLD
      is_underlined = style & TTF_STYLE_UNDERLINE == TTF_STYLE_UNDERLINE

    Args:
        font (:obj:`TTF_Font`): The font object for which the style should be
            retrieved.
    
    Returns:
        int: A bitmask of one or more style constants (see
        :func:`TTF_SetFontStyle`).

    """
    return _ctypes["TTF_GetFontStyle"](font)

def TTF_SetFontStyle(font, style):
    """Sets the rendering style for a given font.
    
    Font styles can be specified using the following constants:

    ============= ===========================
    Style         Constant
    ============= ===========================
    Normal        ``TTF_STYLE_NORMAL``
    Bold          ``TTF_STYLE_BOLD``
    Italics       ``TTF_STYLE_ITALICS``
    Underlined    ``TTF_STYLE_UNDERLINE``
    Strikethrough ``TTF_STYLE_STRIKETHROUGH``
    ============= ===========================

    Multiple font styles (e.g. bold and italics) can be combined using the
    bitwise ``|`` operator::
 
      underlined_bold = (TTF_STYLE_BOLD | TTF_STYLE_UNDERLINE)
      TTF_SetFontStyle(font, underlined_bold)
 
    .. note::
       Setting the underline style for a font may cause the surfaces created by
       :obj:`TTF_RenderGlyph` functions to be taller, in order to make room for
       the underline to be drawn underneath.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the style will be set.
        style (int): A bitmask specifying the style(s) to use for the font.

    """
    return _ctypes["TTF_SetFontStyle"](font, style)

def TTF_GetFontOutline(font):
    """Retrieves the current outline thickness of a given font.

    Args:
        font (:obj:`TTF_Font`): The font object for which the outline thickness
            should be retrieved.
    
    Returns:
        int: The outline thickness (in pixels) of the font.

    """
    return _ctypes["TTF_GetFontOutline"](font)

def TTF_SetFontOutline(font, outline):
    """Sets the outline thickness of a given font.
    
    If the outline is set to zero, outlining will be disabled for the font.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the outline thickness
            will be set.
        outline (int): The new outline thickness (in pixels) for the font.

    """
    return _ctypes["TTF_SetFontOutline"](font, outline)

def TTF_GetFontHinting(font):
    """Retrieves the current hinting style of a given font.

    This function returns one of the constants specified in the documentation
    for :func:`TTF_SetFontHinting`.

    Args:
        font (:obj:`TTF_Font`): The font object for which the hinting style
            should be retrieved.
    
    Returns:
        int: A constant indicating the hinting style of the font.

    """
    return _ctypes["TTF_GetFontHinting"](font)

def TTF_SetFontHinting(font, hinting):
    """Sets the rendering hinting mode for a given font.
    
    The hinting mode can be specified using one of the following constants:

    ================ ==============================
    Hinting type     Constant
    ================ ==============================
    Normal           ``TTF_HINTING_NORMAL``
    Light            ``TTF_HINTING_LIGHT``
    Mono             ``TTF_HINTING_MONO``
    None             ``TTF_HINTING_NONE``
    Light (Subpixel) ``TTF_HINTING_LIGHT_SUBPIXEL``
    ================ ==============================

    Note that the ``TTF_HINTING_LIGHT_SUBPIXEL`` hinting mode requires SDL_ttf
    2.0.18 or newer. If no hinting mode is is explicitly set, "normal" hinting
    is used for rendering.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the hinting style
            will be set.
        hinting (int): A constant specifiying the hinting style to use when
            rendering text.

    """
    return _ctypes["TTF_SetFontHinting"](font, hinting)

def TTF_GetFontWrappedAlign(font):
    """Retrieves the current wrapping alignment for a given font.

    This function returns one of the constants specified in the documentation
    for :func:`TTF_SetFontWrappedAlign`.

    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object for which the alignment type
            should be retrieved.
    
    Returns:
        int: A constant indicating the current wrap alignment for the font.

    """
    return _ctypes["TTF_GetFontWrappedAlign"](font)

def TTF_SetFontWrappedAlign(font, align):
    """Sets the alignment to use when rendering wrapped text with a given font.
    
    The alignment type can be specified using one of the following constants:

    ================ ==============================
    Alignment        Constant
    ================ ==============================
    Left-justified   ``TTF_WRAPPED_ALIGN_LEFT``
    Centered         ``TTF_WRAPPED_ALIGN_CENTER``
    Right-justified  ``TTF_WRAPPED_ALIGN_RIGHT``
    ================ ==============================

    Wrapped text will be left-justified if no alignment is explicitly set.

    `Note: Added in SDL_ttf 2.20.0`
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the alignment type
            will be set.
        align (int): A constant specifiying the aligmnent to use when rendering
            wrapped text.

    """
    return _ctypes["TTF_SetFontWrappedAlign"](font, align)


def TTF_FontHeight(font):
    """Gets the maximum pixel height of all glyphs in a given font.

    You can use this height for rendering text as close together vertically
    as possible, though adding at least one pixel height to it will space it
    so they can't touch.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the maximum glyph
            height should be retrieved.

    Returns:
        int: The maximum height (in pixels) of all glyphs in the font.

    """
    return _ctypes["TTF_FontHeight"](font)

def TTF_FontAscent(font):
    """Gets the maximum pixel ascent of all glyphs in a given font.

    The ascent of a glyph is defined as the distance from the top of the
    glyph to its baseline. For example, a lower-case "t" will generally have a
    larger ascent than a lower-case "o".
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the maximum glyph
            ascent should be retrieved.

    Returns:
        int: The maximum ascent (in pixels) of all glyphs in the font.

    """
    return _ctypes["TTF_FontAscent"](font)

def TTF_FontDescent(font):
    """Gets the maximum pixel descent of all glyphs in a given font.

    The descent of a glyph is defined as the distance from the bottom of the
    glyph to its baseline. For example, a lower-case "g" will typically have a
    non-zero descent whereas a lower-case "o" will generally have a descent of
    zero.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the maximum glyph
            descent should be retrieved.

    Returns:
        int: The maximum descent (in pixels) of all glyphs in the font.

    """
    return _ctypes["TTF_FontDescent"](font)

def TTF_FontLineSkip(font):
    """Gets the recommended spacing between lines for a given font.

    This is usually larger than the result of :func:`TTF_FontHeight`.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the recommended line
            skip height should be retrieved.

    Returns:
        int: The recommended line skip height (in pixels) for the font.

    """
    return _ctypes["TTF_FontLineSkip"](font)

def TTF_GetFontKerning(font):
    """Checks whether or not kerning is enabled for a given font.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the kerning status
            should be retrieved.

    Returns:
        int: Non-zero if kerning is enabled for the font, otherwise 0.

    """
    return _ctypes["TTF_GetFontKerning"](font)

def TTF_SetFontKerning(font, allowed):
    """Enables or disables kerning for a given font.

    Kerning is enabled for all fonts by default.
   
    Args:
        font (:obj:`TTF_Font`): The font object for which the kerning status
            should be changed.
        allowed (int): 0 to disable kerning, or non-zero to enable it.

    """
    return _ctypes["TTF_SetFontKerning"](font, allowed)

def TTF_FontFaces(font):
    """Gets the number of faces ("sub-fonts") available in a given font.
   
    This is a count of the number of specific fonts (based on size and style
    and other typographical features) contained in the font itself.

    Args:
        font (:obj:`TTF_Font`): The font object for which the number of faces
            should be retrieved.

    Returns:
        int: The number of faces in the font.

    """
    return _ctypes["TTF_FontFaces"](font)

def TTF_FontFaceIsFixedWidth(font):
    """Checks if the current face of a given font is fixed width.

    Fixed width fonts are monospace, meaning every character that exists in the
    font is the same width, thus you can assume that a rendered string's width
    is going to be the result of a simple calculation:
    ``glyph_width * string_length``.

    Args:
        font (:obj:`TTF_Font`): The font object for which the fixed-width status
            should be retrieved.

    Returns:
        int: A positive integer if the font is fixed-width, otherwise 0.
   
   """
    return _ctypes["TTF_FontFaceIsFixedWidth"](font)

def TTF_FontFaceFamilyName(font):
    """Gets the current family name (e.g. Helvetica) from a given font.

    Args:
        font (:obj:`TTF_Font`): The font object for which the family name
            should be retrieved.

    Returns:
        bytes: The family name of the given font, or ``None`` if not
        available.

    """
    return _ctypes["TTF_FontFaceFamilyName"](font)

def TTF_FontFaceStyleName(font):
    """Gets the current style name (e.g. Bold) from a given font.

    Args:
        font (:obj:`TTF_Font`): The font object for which the style name
            should be retrieved.

    Returns:
        bytes: The style name of the given font, or ``None`` if not
        available.

    """
    return _ctypes["TTF_FontFaceStyleName"](font)

def TTF_GlyphIsProvided(font, ch):
    """Checks whether a character is provided by a given font.

    The built-in Python :func:`ord` function can be used to convert a string
    character to an integer for use with this function (e.g. ``ord("A")``).

    Args:
        font (:obj:`TTF_Font`): The font object within which to check for a
            glyph for the given character.
        ch (int): A unicode integer representing the character to check for
            within the font.

    Returns:
        int: A non-zero integer if the font provides a glyph for the character,
        otherwise 0.

    """
    return _ctypes["TTF_GlyphIsProvided"](font, ch)

def TTF_GlyphIsProvided32(font, ch):
    """Checks whether a character is provided by a given font.

    Functionally identical to :func:`TTF_GlyphIsProvided`, except it supports
    32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_GlyphIsProvided32"](font, ch)

def TTF_GlyphMetrics(font, ch, minx, maxx, miny, maxy, advance):
    """Gets the glyph metrics for a character with a given font.
    
    This function returns the calculated metrics by reference, meaning that
    it needs to be called using pre-allocated ctypes variables::

       from ctypes import c_int, byref

       minX, maxX, minY, maxY = c_int(0), c_int(0), c_int(0), c_int(0)
       adv = c_int(0)
       TTF_GlyphMetrics(
           font, ord(char),
           byref(minX), byref(maxX), byref(minY), byref(maxY), byref(adv)
       )
       results = [x.value for x in (minX, maxX, minY, maxY, adv)]

    The following link may be useful for understanding what these metrics mean:
    http://freetype.sourceforge.net/freetype2/docs/tutorial/step2.html

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        ch (int): A unicode integer representing the character for which to
            retrieve glyph metrics.
        minx (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the glyph's minimum X offset.
        maxx (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the glyph's maximum X offset.
        miny (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the glyph's minimum Y offset.
        maxy (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the glyph's maximum Y offset.

    Returns:
        int: 0 on success, or -1 on error (e.g. if the glyph does not exist in
        the font). 

    """
    return _ctypes["TTF_GlyphMetrics"](font, ch, minx, maxx, miny, maxy, advance)

def TTF_GlyphMetrics32(font, ch, minx, maxx, miny, maxy, advance):
    """Gets the glyph metrics for a character with a given font.

    Functionally identical to :func:`TTF_GlyphMetrics`, except it supports
    32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_GlyphMetrics32"](font, ch, minx, maxx, miny, maxy, advance)


def TTF_SizeText(font, text, w, h):
    """Calculates the size of an ASCII string rendered with a given font.

    This function does not perform any actual rendering, but correct kerning is
    performed to get the actual width. For a string without any newlines, the
    height will be the same as that returned by :func:`TTF_FontHeight`.

    This function returns the calculated metrics by reference, meaning that
    it needs to be called using pre-allocated ctypes variables::

       from ctypes import c_int, byref

       text_w, text_h = c_int(0), c_int(0)
       TTF_SizeText(font, b"hello!", byref(text_w), byref(text_h))
       text_size = [x.value for x in (text_w, text_h)]

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text for which the rendered
            surface size should be calculated.
        w (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface width (in pixels).
        h (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface height (in pixels).

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_SizeText"](font, text, w, h)

def TTF_SizeUTF8(font, text, w, h):
    """Calculates the size of a UTF8-encoded string rendered with a given font.

    See :func:`TTF_SizeText` for more info.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text for which the rendered
            surface size should be calculated.
        w (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface width (in pixels).
        h (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface height (in pixels).

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_SizeUTF8"](font, text, w, h)

def TTF_SizeUNICODE(font, text, w, h):
    """Calculates the size of a UCS-2 encoded string rendered with a given font.

    See :func:`TTF_SizeText` and :func:`TTF_RenderUNICODE_Solid` for more info.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text for which the rendered surface size should be
            calculated.
        w (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface width (in pixels).
        h (byref(:obj:`~ctypes.c_int`)): A pointer to an integer in which to
            store the calculated surface height (in pixels).

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_SizeUNICODE"](font, text, w, h)

def TTF_MeasureText(font, text, measure_width, extent, count):
    """Gets the number of characters that can fit within a given width.

    This function determines how many rendered characters from a given string of
    ASCII text can fit within a given width. It additionally returns the
    rendered width of the fitting characters.

    Use the :func:`TTF_GetError` function to check for any errors.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text.
        measure_width (int): The maximum width (in pixels) of the rendered
            output surface.
        extent (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the calculated rendered width of the first ``count`` characters of
            the string.
        count (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the returned number of characters from the string that can fit
            within the given width.

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_MeasureText"](font, text, measure_width, extent, count)

def TTF_MeasureUTF8(font, text, measure_width, extent, count):
    """Gets the number of characters that can fit within a given width.

    Identical to :func:`TTF_MeasureText`, except that this function is used with
    UTF8-encoded bytestrings instead of ASCII-encoded ones.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text.
        measure_width (int): The maximum width (in pixels) of the rendered
            output surface.
        extent (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the calculated rendered width of the first ``count`` characters of
            the string.
        count (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the returned number of characters from the string that can fit
            within the given width.

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_MeasureUTF8"](font, text, measure_width, extent, count)

def TTF_MeasureUNICODE(font, text, measure_width, extent, count):
    """Gets the number of characters that can fit within a given width.

    Identical to :func:`TTF_MeasureText`, except that this function is used with
    UCS-2 byte arrays instead of ASCII-encoded bytestrings. See the
    :func:`TTF_RenderUNICODE_Solid` documentation for more information on
    converting text to UCS-2 in Python.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text.
        measure_width (int): The maximum width (in pixels) of the rendered
            output surface.
        extent (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the calculated rendered width of the first ``count`` characters of
            the string.
        count (byref(:obj:`~ctypes.c_int`)): A pointer to an integer containing
            the returned number of characters from the string that can fit
            within the given width.

    Returns:
        int: 0 on success, or -1 on error (e.g. if a glyph is not found in
        the font).

    """
    return _ctypes["TTF_MeasureUNICODE"](font, text, measure_width, extent, count)


def TTF_RenderText_Solid(font, text, fg):
    """Renders an ASCII-encoded string to a non-antialiased 8-bit surface.

    The ``Solid`` family of TTF functions render text to an 8-bit palettized
    :obj:`SDL_Surface` with a transparent background and no antialiasing.
    This is the fastest (and lowest quality) of all TTF rendering types.

    The resulting surface has a transparent background unlike
    :func:`TTF_RenderText_Shaded`, but the rendered text is not antialised and
    will thus appear pixelated and difficult to read at small sizes. The
    resulting surface should blit faster than the one returned by
    :func:`TTF_RenderText_Blended`. This rendering type should be used in cases
    when you need to render lots of text very quickly (e.g. if you're updating
    it every frame) or when you don't care about antialiasing.
   
    The 0 pixel is the colorkey for the resulting surface, giving a transparent
    background, and the 1 pixel is set to the text color. This allows you to
    change the color without having to render the text again. Palette index 0
    is not drawn when the returned surface is blitted to another surface (since
    it is the colorkey and thus transparent), though its actual color is 255
    minus each of the RGB components of the foreground color.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Solid"](font, text, fg)

def TTF_RenderUTF8_Solid(font, text, fg):
    """Renders a UTF8-encoded string to a non-antialiased 8-bit surface.

    See :func:`TTF_RenderText_Solid` for more details on the rendering style.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Solid"](font, text, fg)

def TTF_RenderUNICODE_Solid(font, text, fg):
    """Renders a UCS-2 encoded string to a non-antialiased 8-bit surface.

    The required text input format for this function is a ctypes array of
    UNICODE (UCS-2) glyphs in uint16 format, optionally terminated by a
    byte-order mark (``UNICODE_BOM_NATIVE`` or ``UNICODE_BOM_SWAPPED``)
    indicating how the text should be interpreted. Python strings can be
    converted to this format using the following process::

       # Generate a UCS-2 array from a Python string
       teststr = u"Hello world!"
       strlen = len(teststr + 1)  # +1 for byte-order mark
       intstr = unpack('H' * strlen, teststr.encode('utf-16'))
       intstr = intstr + (0, )  # Null-terminate the string
       strarr = (ctypes.c_uint16 * len(intstr))(*intstr)

       # Render the UCS-2 string
       col = SDL_Color(0, 0, 0)
       rendered = TTF_RenderUNICODE_Solid(font, strarr, col)

    Unless there is a very specific need, the ``TTF_RenderUTF8`` functions should
    always be used instead of their ``TTF_RenderUNICODE`` counterparts. In
    addition to having a much friendlier Python API, SDL_ttf uses the
    ``TTF_RenderUTF8`` functions internally for all the ``TTF_RenderUNICODE``
    functions anyway so there is no benefit in terms of supporting a wider range
    of characters.

    See :func:`TTF_RenderText_Solid` for more details on the rendering style.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Solid"](font, text, fg)

def TTF_RenderText_Solid_Wrapped(font, text, fg, wrapLength):
    """Renders an ASCII-encoded string to a non-antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderText_Solid`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Solid_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderUTF8_Solid_Wrapped(font, text, fg, wrapLength):
    """Renders a UTF8-encoded string to a non-antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderUTF8_Solid`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Solid_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderUNICODE_Solid_Wrapped(font, text, fg, wrapLength):
    """Renders a UCS-2 encoded string to a non-antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderUNICODE_Solid`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Solid_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderGlyph_Solid(font, ch, fg):
    """Renders a unicode character to a non-antialiased 8-bit surface.

    The built-in Python :func:`ord` function can be used to convert a string
    character to an integer for use with this function (e.g. ``ord("A")``).

    The glyph is rendered without any padding or centering in the X direction,
    and is aligned normally in the Y direction. See :func:`TTF_RenderText_Solid`
    for more details on the rendering style.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        ch (int): A unicode integer representing the glyph to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the glyph. This
            becomes colormap index 1.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered glyph, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderGlyph_Solid"](font, ch, fg)

def TTF_RenderGlyph32_Solid(font, ch, fg):
    """Renders a unicode character to a non-antialiased 8-bit surface.

    Functionally identical to :func:`TTF_RenderGlyph_Solid`, except it supports
    32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_RenderGlyph32_Solid"](font, ch, fg)


def TTF_RenderText_Shaded(font, text, fg, bg):
    """Renders an ASCII-encoded string to a solid antialiased 8-bit surface.

    The ``Shaded`` family of TTF functions render text to an 8-bit palettized
    :obj:`SDL_Surface` with a solid background color and antialiasing. This is
    the second-fastest of the text rendering types, being slightly faster than
    :func:`TTF_RenderText_Blended` but slower than :func:`TTF_RenderText_Solid`.

    Text rendered using the ``Shaded`` method will be antialiased, but the
    resulting surface will have a solid background colour instead of a
    transparent one. Surfaces rendered with this function should blit as quickly
    as those created with :func:`TTF_RenderText_Blended`. This rendering type
    should be used in cases when you want nice-looking text but don't need
    background transparency.

    The 0 pixel is the background color for the resulting surface, while other
    pixels have varying levels of the foreground color. This results in a box of
    the background color around the text in the foreground color.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Shaded"](font, text, fg, bg)

def TTF_RenderUTF8_Shaded(font, text, fg, bg):
    """Renders a UTF8-encoded string to a solid antialiased 8-bit surface.

    See :func:`TTF_RenderText_Shaded` for more details on the rendering style.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Shaded"](font, text, fg, bg)

def TTF_RenderUNICODE_Shaded(font, text, fg, bg):
    """Renders a UCS-2 encoded string to a solid antialiased 8-bit surface.

    See :func:`TTF_RenderText_Shaded` for more details on the rendering style,
    and :func:`TTF_RenderUNICODE_Solid` for documentation of the text format.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Shaded"](font, text, fg, bg)

def TTF_RenderText_Shaded_Wrapped(font, text, fg, bg, wrapLength):
    """Renders an ASCII-encoded string to a solid antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderText_Shaded`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Shaded_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderUTF8_Shaded_Wrapped(font, text, fg, bg, wrapLength):
    """Renders a UTF8-encoded string to a solid antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderUTF8_Shaded`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Shaded_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderUNICODE_Shaded_Wrapped(font, text, fg, bg, wrapLength):
    """Renders a UCS-2 encoded string to a solid antialiased 8-bit surface.

    This function is identical to :func:`TTF_RenderUNICODE_Shaded`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.0.18`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the text. This
            becomes colormap index 0.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Shaded_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderGlyph_Shaded(font, ch, fg, bg):
    """Renders a unicode character to an 8-bit surface using a given font.

    See :func:`TTF_RenderText_Shaded` for more details on the rendering style,
    and :func:`TTF_RenderGlyph_Solid` for additional usage information.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        ch (int): A unicode integer representing the glyph to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the glyph. This
            becomes colormap index 1.
        bg (:obj:`SDL_Color`): The background fill color for the glyph. This
            becomes colormap index 0.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered glyph, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderGlyph_Shaded"](font, ch, fg, bg)

def TTF_RenderGlyph32_Shaded(font, ch, fg, bg):
    """Renders a unicode character to an 8-bit surface using a given font.

    Functionally identical to :func:`TTF_RenderGlyph_Shaded`, except it supports
    32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_RenderGlyph32_Shaded"](font, ch, fg, bg)


def TTF_RenderText_Blended(font, text, fg):
    """Renders an ASCII-encoded string to an antialiased 32-bit surface.

    The ``Blended`` family of TTF functions render text to a 32-bit ARGB
    :obj:`SDL_Surface` with antialiasing and background transparency.

    The rendered text will be antialiased on a transparent surface using alpha
    blending. This rendering type should be used in cases when you want to
    overlay the rendered text over something else, and in in most other cases
    where high performance isn't the primary concern. For rendering high-quality
    text on a solid background or at smaller font sizes, see the ``LCD`` family
    of rendering functions.

    .. note::
       To render an RGBA surface instead of an ARGB one, just swap the R and B
       values when creating the SDL_Color.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Blended"](font, text, fg)

def TTF_RenderUTF8_Blended(font, text, fg):
    """Renders a UTF8-encoded string to an antialiased 32-bit surface.

    See :func:`TTF_RenderText_Blended` for more details on the rendering style.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Blended"](font, text, fg)

def TTF_RenderUNICODE_Blended(font, text, fg):
    """Renders a UCS-2 encoded string to an antialiased 32-bit surface.

    See :func:`TTF_RenderText_Blended` for more details on the rendering style,
    and :func:`TTF_RenderUNICODE_Solid` for documentation of the text format.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Blended"](font, text, fg)

def TTF_RenderText_Blended_Wrapped(font, text, fg, wrapLength):
    """Renders an ASCII-encoded string to an antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderText_Blended`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_Blended_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderUTF8_Blended_Wrapped(font, text, fg, wrapLength):
    """Renders a UTF8-encoded string to an antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderUTF8_Blended`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_Blended_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderUNICODE_Blended_Wrapped(font, text, fg, wrapLength):
    """Renders a UCS-2 encoded string to an antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderUNICODE_Blended`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_Blended_Wrapped"](font, text, fg, wrapLength)

def TTF_RenderGlyph_Blended(font, ch, fg):
    """Renders a unicode character to an antialiased 32-bit surface.

    See :func:`TTF_RenderText_Blended` for more details on the rendering style,
    and :func:`TTF_RenderGlyph_Solid` for additional usage information.

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        ch (int): A unicode integer representing the glyph to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the glyph.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered glyph, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderGlyph_Blended"](font, ch, fg)

def TTF_RenderGlyph32_Blended(font, ch, fg):
    """Renders a unicode character to an antialiased 32-bit surface.

    Functionally identical to :func:`TTF_RenderGlyph_Blended`, except it
    supports 32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_RenderGlyph32_Blended"](font, ch, fg)


def TTF_RenderText_LCD(font, text, fg, bg):
    """Renders an ASCII-encoded string to a solid 32-bit surface.

    The ``LCD`` family of TTF functions render text to av32-bit ARGB
    :obj:`SDL_Surface` with high-quality subpixel rendering. This should
    produce better results at small sizes than :func:`TTF_RenderText_Shaded`,
    but may be slower and requires a solid background colour for best results.
    
    .. note::
       To render an RGBA surface instead of an ARGB one, just swap the R and B
       values when creating the foreground and background colors.
    
    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_LCD"](font, text, fg, bg)

def TTF_RenderUTF8_LCD(font, text, fg, bg):
    """Renders a UTF8-encoded string to a solid antialiased 32-bit surface.

    See :func:`TTF_RenderText_LCD` for more details on the rendering style.
    
    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_LCD"](font, text, fg, bg)

def TTF_RenderUNICODE_LCD(font, text, fg, bg):
    """Renders a UCS-2 encoded string to a solid antialiased 32-bit surface.

    See :func:`TTF_RenderText_LCD` for more details on the rendering style,
    and :func:`TTF_RenderUNICODE_Solid` for documentation of the text format.
    
    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_LCD"](font, text, fg, bg)

def TTF_RenderText_LCD_Wrapped(font, text, fg, bg, wrapLength):
    """Renders an ASCII-encoded string to a solid antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderText_LCD`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.20.0`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): An ASCII-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderText_LCD_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderUTF8_LCD_Wrapped(font, text, fg, bg, wrapLength):
    """Renders a UTF8-encoded string to a solid antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderUTF8_LCD`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.20.0`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (byref(:obj:`~ctypes.c_uint16`)): A ctypes array containing a UCS-2
            encoded string of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUTF8_LCD_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderUNICODE_LCD_Wrapped(font, text, fg, bg, wrapLength):
    """Renders a UCS-2 encoded string to a solid antialiased 32-bit surface.

    This function is identical to :func:`TTF_RenderUNICODE_LCD`, except that
    any lines exceeding the specified wrap length will be wrapped to fit within
    the given width.

    `Note: Added in SDL_ttf 2.20.0`
   
    Args:
        font (:obj:`TTF_Font`): The font object to use.
        text (bytes): A UTF8-encoded bytestring of text to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the text.
        bg (:obj:`SDL_Color`): The background fill color for the text.
        wrapLength (int): The maximum width of the output surface (in pixels)

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered text, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderUNICODE_LCD_Wrapped"](font, text, fg, bg, wrapLength)

def TTF_RenderGlyph_LCD(font, ch, fg, bg):
    """Renders a unicode character to a 32-bit surface using a given font.

    See :func:`TTF_RenderText_LCD` for more details on the rendering style,
    and :func:`TTF_RenderGlyph_Solid` for additional usage information.
    
    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to use.
        ch (int): A unicode integer representing the glyph to render.
        fg (:obj:`SDL_Color`): The color to use for rendering the glyph.
        bg (:obj:`SDL_Color`): The background fill color for the glyph.

    Returns:
        POINTER(:obj:`SDL_Surface`): A pointer to the new surface containing the
        rendered glyph, or a null pointer if there was an error.

    """
    return _ctypes["TTF_RenderGlyph_LCD"](font, ch, fg, bg)

def TTF_RenderGlyph32_LCD(font, ch, fg, bg):
    """Renders a unicode character to a 32-bit surface using a given font.

    Functionally identical to :func:`TTF_RenderGlyph_LCD`, except it supports
    32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.20.0`

    """
    return _ctypes["TTF_RenderGlyph32_LCD"](font, ch, fg, bg)

TTF_RenderText = TTF_RenderText_Shaded
TTF_RenderUTF8 = TTF_RenderUTF8_Shaded
TTF_RenderUNICODE = TTF_RenderUNICODE_Shaded


def TTF_SetDirection(direction):
    """Sets the global text direction to use for rendering.

    .. note:: This function has been deprecated in favor of
              :func:`TTF_SetFontDirection` and should not be used in new
              projects.

    This function lets you manually specify the direction in which SDL_ttf
    should render text, and can be set or changed at any time.

    The direction value is passed to the underlying HarfBuzz library, meaning
    that the direction must be one of the following HarfBuzz constants:

    =============== ====================
    Text Direction  Constant
    =============== ====================
    Left-to-right   ``HB_DIRECTION_LTR``
    Right-to-left   ``HB_DIRECTION_RTL``
    Top-to-bottom   ``HB_DIRECTION_TTB``
    Bottom-to-top   ``HB_DIRECTION_BTT``
    =============== ====================

    For convenience, these constants are provided by the ``sdl2.sdlttf`` module.
    If not specified, SDL_ttf defaults to left-to-right text rendering.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        direction (int): A constant specifying the direction to use for text
            rendering with the TTF library.

    Returns:
        int: 0 on success, or -1 if HarfBuzz not available.

    """
    return _ctypes["TTF_SetDirection"](direction)

def TTF_SetScript(script):
    """Sets the global script (e.g. Arabic) to use for rendering text.

    .. note:: This function has been deprecated in favor of
              :func:`TTF_SetFontScriptName` and should not be used in new
              projects.

    Setting the script gives the text renderer extra information about how
    to best shape words and characters for a given language. This can produce
    better results when rendering with non-Latin languages and fonts.

    The script value is passed to the underlying HarfBuzz library, meaning that
    it needs to be specified as a HarfBuzz script constant. To make this
    convenient, the ``sdl2.sdlttf`` module implements HarfBuzz's :func:`HB_TAG`
    macro for converting ISO 15924 character codes to HarfBuzz scripts::

        arabic_script = HB_TAG('A', 'r', 'a', 'b')
        TTF_SetScript(arabic_script)

    If no script has been set, the TTF library defaults to the unknown ('Zzzz')
    script.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        script (int): An integer specifying the script style to use for text
            shaping.

    Returns:
        int: 0 on success, or -1 if HarfBuzz not available.

    """
    return _ctypes["TTF_SetScript"](script)

def TTF_SetFontDirection(font, direction):
    """Sets the text direction to use for rendering a given font.

    This function lets you manually specify the direction to use for rendering
    text with a given font, using the following constants:

    =============== =====================
    Text Direction  Constant
    =============== =====================
    Left-to-right   ``TTF_DIRECTION_LTR``
    Right-to-left   ``TTF_DIRECTION_RTL``
    Top-to-bottom   ``TTF_DIRECTION_TTB``
    Bottom-to-top   ``TTF_DIRECTION_BTT``
    =============== =====================

    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to configure.
        direction (int): A constant specifying the direction to use for
            rendering text with the given font.

    Returns:
        int: 0 on success, -1 on error.

    """
    return _ctypes["TTF_SetFontDirection"](font, direction)

def TTF_SetFontScriptName(font, script):
    """Sets the script (e.g. Arabic) to use for rendering a given font.

    Setting the script gives the text renderer extra information about how
    to best shape words and characters for a given language. This can produce
    better results when rendering with non-Latin languages and fonts.

    The script type is specified as a 4-character ISO 15924 character code (e.g.
    'Arab' for Arabic). A full list of possible 4-character script codes can be
    found here: https://unicode.org/iso15924/iso15924-codes.html

    `Note: Added in SDL_ttf 2.20.0`

    Args:
        font (:obj:`TTF_Font`): The font object to configure.
        script (bytes): A 4-character ISO 15924 character code indicating the
            script type to use for text shaping.

    Returns:
        int: 0 on success, -1 on error.

    """
    return _ctypes["TTF_SetFontScriptName"](font, script)

def TTF_CloseFont(font):
    """Closes and frees the memory associated with a given font.

    This function should be called on a font when you are done with it. A
    :obj:`TTF_Font` cannot be used after it has been closed.
   
    Args:
        font (:obj:`TTF_Font`): The font to close.

    """
    return _ctypes["TTF_CloseFont"](font)

def TTF_Quit():
    """De-initializes the TTF engine.
   
    Once this has been called, other functions in the module should not be used
    until :func:`TTF_Init` is called to re-initialize the engine (except for
    :func:`TTF_WasInit`).

    .. note::
       If :func:`TTF_Init` is called multiple times, this function should be
       called an equal number of times to properly de-initialize the library.

    """
    return _ctypes["TTF_Quit"]()

def TTF_WasInit():
    """Checks if the TTF engine is initialized.
   
    This function can be used before calling :func:`TTF_Init` to avoid
    initializing twice in a row, or to determine if need to call
    :func:`TTF_Quit`.
   
    Returns:
        int: The number of times :func:`TTF_Init` has been called without a
        corresponding :func:`TTF_Quit`.

    """
    return _ctypes["TTF_WasInit"]()

def TTF_GetFontKerningSize(font, prev_index, index):
    # NOTE: Deprecated in SDL_ttf
    return _ctypes["TTF_GetFontKerningSize"](font, prev_index, index)

def TTF_GetFontKerningSizeGlyphs(font, previous_ch, ch):
    """Gets the kerning size of two glyphs (by FreeType index) for a given font.

    .. note::
       The units of kerning size returned by this function differ between fonts
       depending on their format and how they were designed.

    `Note: Added in SDL_ttf 2.0.14`

    Args:
        font (:obj:`TTF_Font`): The font object for which the kerning size
            should be retrieved.
        previous_ch (int): The unicode integer representing the first glyph.
        ch (int): The unicode integer representing the second glyph.

    Returns:
        int: The kerning size of the two glyphs in the current font.

    """
    return _ctypes["TTF_GetFontKerningSizeGlyphs"](font, previous_ch, ch)

def TTF_GetFontKerningSizeGlyphs32(font, previous_ch, ch):
    """Gets the kerning size of two glyphs (by FreeType index) for a given font.

    Functionally identical to :func:`TTF_GetFontKerningSizeGlyphs`, except it
    supports 32-bit character codes instead of just 16-bit ones.

    `Note: Added in SDL_ttf 2.0.18`

    """
    return _ctypes["TTF_GetFontKerningSizeGlyphs32"](font, previous_ch, ch)

def TTF_SetFontSDF(font, on_off):
    """Enables or disables Signed Distance Field rendering for a given font.

    Requires a version of FreeType that supports SDF rendering (2.11.0 or
    newer). As of SDL2_ttf 2.0.18, the FreeType version bundled with the
    official binaries is too old to support SDF.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object for which SDF should be
            enabled or disabled.
        on_off (int): Whether to enable (``SDL_TRUE``) or disable
            (``SDL_FALSE``) SDF rendering for the given font.

    Returns:
        int: 0 on success, or -1 if SDF support not available.

    """
    return _ctypes["TTF_SetFontSDF"](font, on_off)

def TTF_GetFontSDF(font):
    """Checks if Signed Distance Field rendering is enabled for a given font.

    If using a version of FreeType without SDF support, this will always
    return 0.

    `Note: Added in SDL_ttf 2.0.18`

    Args:
        font (:obj:`TTF_Font`): The font object for which SDF usage should
            be checked.

    Returns:
        int: 1 if the font is using SDF, otherwise 0.

    """
    return _ctypes["TTF_GetFontSDF"](font)

TTF_SetError = SDL_SetError
TTF_GetError = SDL_GetError
