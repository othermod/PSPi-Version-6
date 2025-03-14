import os
from .. import endian, surface, pixels, error, rwops
from .err import raise_sdl_err
from .compat import UnsupportedError, byteify, stringify
from .resources import _validate_path
from .surface import _get_target_surface

_HASPIL = True
try:
    from PIL import Image
except ImportError:
    _HASPIL = False

_HASSDLIMAGE = True
try:
    from .. import sdlimage
except ImportError:
    _HASSDLIMAGE = False

__all__ = [
    "get_image_formats", "load_bmp", "load_img", "load_svg", "save_bmp",
    "pillow_to_surface", "load_image"
]


_SDL_IMAGE_FLAGS = -1


def _sdl_image_init():
    global _SDL_IMAGE_FLAGS
    if _SDL_IMAGE_FLAGS == -1:
        _SDL_IMAGE_FLAGS = sdlimage.IMG_Init(
            sdlimage.IMG_INIT_JPG | sdlimage.IMG_INIT_PNG |
            sdlimage.IMG_INIT_TIF | sdlimage.IMG_INIT_WEBP
        )
    return _SDL_IMAGE_FLAGS


def _get_mode_properties(mode):
    le = endian.SDL_BYTEORDER == endian.SDL_LIL_ENDIAN
    rmask, gmask, bmask, amask = (0, 0, 0, 0)
    if mode in ("1", "L", "P"):
        # "1" = B/W, 1 bit per byte
        # "L" = greyscale, 8-bit
        # "P" = palette-based, 8-bit
        depth = 8
    elif mode == "RGB":
        # RGB: 3x8-bit, 24bpp
        depth = 24
        rmask = 0x0000FF if le else 0xFF0000
        gmask = 0x00FF00
        bmask = 0xFF0000 if le else 0x0000FF
    elif mode in ("RGBA", "RGBX"):
        # RGBX: 4x8-bit, no alpha
        # RGBA: 4x8-bit, alpha
        depth = 32
        rmask = 0x000000FF if le else 0xFF000000
        gmask = 0x0000FF00 if le else 0x00FF0000
        bmask = 0x00FF0000 if le else 0x0000FF00
        if mode == "RGBA":
            amask = 0xFF000000 if le else 0x000000FF
    else:
        raise TypeError("Cannot convert {0} data to surface.".format(mode))
    return (rmask, gmask, bmask, amask, depth)


def _ensure_argb32(sf, fname):
    # Check if image already ARGB32 and return if True
    ARGB32 = pixels.SDL_PIXELFORMAT_ARGB8888
    if sf.contents.format.contents.format == ARGB32:
        return sf

    # Convert the image to ARGB32. Note that this frees the original surface.
    out_fmt = pixels.SDL_AllocFormat(ARGB32)
    converted = surface.SDL_ConvertSurface(sf, out_fmt, 0)
    surface.SDL_FreeSurface(sf)
    if not converted:
        raise_sdl_err("converting '{0}' to ARGB format".format(fname))

    return converted


def get_image_formats():
    # This function is deprecated and gives inaccurate results
    if not _HASPIL and not _HASSDLIMAGE:
        return ("bmp", )
    return ("bmp", "cur", "gif", "ico", "jpg", "lbm", "pbm", "pcx", "pgm",
            "png", "pnm", "ppm", "svg", "tga", "tif", "webp", "xcf", "xpm")


def load_bmp(path):
    """Imports a BMP (bitmap image) file as an SDL surface.

    Because BMP importing and exporting is part of the core SDL2 library,
    this function is guaranteed to be available on all platforms and
    installations that support PySDL2.

    Args:
        path (str): The relative (or absolute) path to the BMP image to import.

    Returns:
        :obj:`~sdl2.SDL_Surface`: An SDL surface containing the imported image.

    """
    fullpath, fname = _validate_path(path, "an image")
    img_surf = surface.SDL_LoadBMP(byteify(fullpath))
    if not img_surf:
        raise_sdl_err("importing '{0}' as a BMP".format(fname))

    return img_surf.contents


def save_bmp(source, path, overwrite=False):
    """Exports an SDL surface to a BMP (bitmap image) file.

    Because BMP importing and exporting is part of the core SDL2 library,
    this function is guaranteed to be available on all platforms and
    installations that support PySDL2.

    Args:
        source (:obj:`~sdl2.SDL_Surface`): The surface to save as a BMP file.
        path (str): The relative (or absolute) path to which the BMP should be
            saved.
        overwrite (bool, optional): Whether the image should be overwritten if
            a file at that path already exists. Defaults to False.

    """
    fullpath, fname = _validate_path(path, "", write=True)
    if os.path.exists(fullpath):
        if overwrite:
            os.remove(fullpath)
        else:
            e = "A file already exists at the given path: {0}"
            raise RuntimeError(e.format(fullpath))
    surf = _get_target_surface(source, argname="source")
    ret = surface.SDL_SaveBMP(surf, byteify(fullpath))
    if ret != 0:
        raise_sdl_err("saving '{0}' as a BMP".format(fname))


def load_img(path, as_argb=True):
    """Imports an image file as an SDL surface using the **SDL_image** library.

    This function supports a wide range of image formats, including GIF, BMP,
    JPEG, PNG, TIFF, and WebP. For a full list, consult the SDL_image
    documentation.

    By default, this function also converts the imported surface to 32-bit ARGB
    format for consistency across functions and better compatibility with SDL2
    renderers. To disable ARGB conversion, set the ``as_argb`` parameter to
    ``False``.

    .. note::
       Because SDL_image is not part of the core SDL2 library, this function
       will only work on systems where the SDL_image library is installed.
       Additionally, support for PNG, JPEG, TIFF, and WebP in SDL_image is
       dynamic and are not guaranteed to be available on all systems.

    Args:
        path (str): The relative (or absolute) path to the image to import.
        as_argb (bool, optional): Whether the obtained surface should be
            converted to 32-bit ARGB pixel format or left as-is. Defaults to
            ``True`` (convert to ARGB).

    Returns:
        :obj:`~sdl2.SDL_Surface`: An SDL surface containing the imported image.

    """
    if not _HASSDLIMAGE:
        err = "'{0}' requires the SDL_image library, which could not be found."
        raise RuntimeError(err.format("load_img"))

    # Import the image file using the generic SDL_Image loader
    fullpath, fname = _validate_path(path, "an image")
    _sdl_image_init()
    img_surf = sdlimage.IMG_Load(byteify(fullpath))
    if not img_surf:
        raise_sdl_err("importing '{0}' using SDL_image".format(fname))

    # If requested, ensure output surface is 32-bit ARGB
    if as_argb:
        img_surf = _ensure_argb32(img_surf, fname)

    error.SDL_ClearError() # Clear any non-critical errors during loading
    return img_surf.contents


def load_svg(path, width=0, height=0, as_argb=True):
    """Loads an SVG image at a given resolution, preserving aspect ratio.

    Only one dimension (height or width) will have any effect on a given image
    as the aspect ratio will always be preserved (e.g. setting an output size
    of 200x150 on a 100x100 SVG will result in a 200x200 surface).
    
    If both dimensions are specified, whichever one results in a larger output
    surface will be used. If neither height or width are specified, the SVG
    will be loaded at its original internal resolution.

    .. note:: SVG support in SDL2_image is currently focused on simple images
              and does not support font rendering. More complex or modern SVG
              files may not render correctly.

    `Note: This function requires SDL2_image 2.6.0 or newer`.

    Args:
        path (str): The relative (or absolute) path to the image to import.
        width (int, optional): The width (in pixels) at which to load the SVG.
        height (int, optional): The height (in pixels) at which to load the SVG.
        as_argb (bool, optional): Whether the obtained surface should be
            converted to 32-bit ARGB pixel format or left as-is. Defaults to
            ``True`` (convert to ARGB).

    Returns:
        :obj:`~sdl2.SDL_Surface`: An SDL surface containing the imported SVG.
    
    """
    if not _HASSDLIMAGE:
        err = "'{0}' requires the SDL_image library, which could not be found."
        raise RuntimeError(err.format("load_svg"))

    # Import the image file using the scaled SVG loader
    fullpath, fname = _validate_path(path, "an SVG")
    _sdl_image_init()
    rw = rwops.SDL_RWFromFile(byteify(fullpath), b"r")
    svg_surf = sdlimage.IMG_LoadSizedSVG_RW(rw, width, height)
    rwops.SDL_RWclose(rw)
    if not svg_surf:
        raise_sdl_err("importing '{0}' using SDL_image".format(fname))

    # If requested, ensure output surface is 32-bit ARGB
    if as_argb:
        svg_surf = _ensure_argb32(svg_surf, fname)
    
    error.SDL_ClearError() # Clear any non-critical errors during loading
    return svg_surf.contents


def pillow_to_surface(img, as_argb=True):
    """Converts a :obj:`PIL.Image.Image` object to an SDL surface.

    This function returns a copy of the original object's pixel data, meaning
    that the original Image can be modified or deleted without affecting the
    returned surface (and vice versa).
    
    By default, this function also converts the surface to 32-bit ARGB format
    for consistency across functions and better compatibility with SDL2
    renderers. To disable ARGB conversion, set the ``as_argb`` parameter to
    ``False``.

    Args:
        img (:obj:`PIL.Image.Image`): The Image object to convert to an SDL
            surface.
        as_argb (bool, optional): Whether the obtained surface should be
            converted to 32-bit ARGB pixel format or left as-is. Defaults to
            ``True`` (convert to ARGB).
    
    Returns:
        :obj:`~sdl2.SDL_Surface`: An SDL surface copy of the PIL image.

    """
    if not (hasattr(img, "mode") and hasattr(img, "size")):
        raise TypeError("'img' must be a valid PIL Image.")

    # Determine correct properties for new surface from PIL data
    mode = img.mode
    width, height = img.size
    rmask, gmask, bmask, amask, depth = _get_mode_properties(mode)
    pitch = width * int(depth / 8)

    # Get PIL pixel bytes and cast them to an SDL surface
    pxbuf = img.tobytes()
    imgsurface = surface.SDL_CreateRGBSurfaceFrom(
        pxbuf, width, height, depth, pitch, rmask, gmask, bmask, amask
    )
    if not imgsurface:
        raise_sdl_err("creating a surface from a PIL Image")
    imgsurface = imgsurface.contents

    # Retrieve the palette for the image (if any)
    palette = []
    if mode == "P":
        palette = img.getpalette()
    elif mode in ("1", "L"):
        for i in range(256):
            palette += [i, i, i]

    if len(palette):
        # Convert the Pillow palette to an SDL palette
        num_colors = len(palette) // 3
        sdlpalette = pixels.SDL_AllocPalette(num_colors)
        if not sdlpalette:
            raise_sdl_err("initializing the palette for the SDL surface")
        for idx in range(num_colors):
            start, end = (idx * 3, idx * 3 + 3)
            r, g, b = palette[start:end]
            sdlpalette.contents.colors[idx] = pixels.SDL_Color(r, g, b)
        
        # Apply the converted palette to the surface
        ret = surface.SDL_SetSurfacePalette(imgsurface, sdlpalette)
        pixels.SDL_FreePalette(sdlpalette)
        if ret != 0:
            raise_sdl_err("converting the palette from the PIL Image")

        # If the image has a single transparent palette index, set that index as
        # the color key to make blitting correct.
        k = "transparency"
        if k in img.info and isinstance(img.info[k], int):
            surface.SDL_SetColorKey(imgsurface, True, img.info[k])

    # Determine whether to use 32-bit ARGB or original pixel format
    out_fmt = imgsurface.format
    if as_argb:
        out_fmt = pixels.SDL_AllocFormat(pixels.SDL_PIXELFORMAT_ARGB8888)

    # Create a new surface from the converted data for memory safety
    surfcopy = surface.SDL_ConvertSurface(imgsurface, out_fmt, 0)
    surface.SDL_FreeSurface(imgsurface)
    if not surfcopy:
        raise_sdl_err("copying the PIL Image data to a new surface")
    
    return surfcopy.contents


def load_image(fname, enforce=None):
    """**[Deprecated]** Imports an image file as an SDL surface.

    This function uses either the SDL_image library or the Pillow Python package
    for importing images, using SDL2's built-in BMP loader as a fall-back if
    neither are available.

    .. warning::
       Due to a long-standing bug, the resulting image surfaces can have
       different pixel formats depending on which backend was used, making
       behavior unpredictable across different systems. As such this function
       is deprecated, and is only maintained to avoid breaking existing code.
       For new projects, the :func:`load_bmp`, :func:`load_img`, and/or
       :func:`pillow_to_surface` functions should be used instead.

    Args:
        fname (str): The relative (or absolute) path to the image to import.
        enforce (str, optional): A string indicating the specific backend to
            use for loading images. Can be either "PIL" for Pillow-only, "SDL"
            for SDL2 and SDL_image only, or ``None`` for no enforced backend.
            Defaults to ``None``.

    Returns:
        :obj:`~sdl2.SDL_Surface`: An SDL surface containing the imported image.

    """
    if enforce is not None and enforce not in ("PIL", "SDL"):
        raise ValueError("enforce must be either 'PIL' or 'SDL', if set")
    elif enforce == "PIL" and not _HASPIL:
        raise UnsupportedError("cannot use PIL (not found)")
    if fname is None or not hasattr(fname, "upper"):
        raise ValueError("fname must be a string")

    name = byteify(fname)
    imgsurface = None
    err = "Unable to import '{0}'".format(fname)

    # Try importing image as a BMP if other decoders aren't available
    if (enforce == "SDL" or not _HASPIL) and not _HASSDLIMAGE:
        imgsurface = surface.SDL_LoadBMP(name)
        if not imgsurface:
            error.SDL_ClearError()
            err += " as a BMP (must have SDL_image or Pillow to support "
            err += "other formats)"
            raise RuntimeError(err)
        else:
            return imgsurface.contents

    # Try imporing the image using SDL_image
    if enforce != "PIL" and _HASSDLIMAGE:
        _sdl_image_init()
        imgsurface = sdlimage.IMG_Load(name)
        if not imgsurface:
            # An error occured - if we do not try PIL, break out now
            if not _HASPIL or enforce == "SDL":
                err += " using SDL_image: " + stringify(error.SDL_GetError())
                error.SDL_ClearError()
                raise RuntimeError(err)
        else:
            return imgsurface.contents

    # Try importing the image using Pillow and converting to an SDL surface
    if enforce != "SDL" and _HASPIL:
        image = Image.open(fname)
        return pillow_to_surface(image, as_argb=False)
