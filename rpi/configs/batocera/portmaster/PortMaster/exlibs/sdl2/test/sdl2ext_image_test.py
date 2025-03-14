import os
import sys
import pytest
import sdl2
from sdl2 import ext as sdl2ext
from sdl2.ext import color
from sdl2 import surface as surf
from sdl2 import pixels

try:
    from sdl2 import sdlimage
    _HASSDLIMAGE=True
except:
    _HASSDLIMAGE=False

try:
    import PIL
    _HASPIL = True
except ImportError:
    _HASPIL = False


parent_path = os.path.abspath(os.path.dirname(__file__))
resource_path = os.path.join(parent_path, "resources")

is32bit = sys.maxsize <= 2**32
ismacos = sys.platform == "darwin"
skip_formats = []

if _HASSDLIMAGE:
    # SVG unsupported on SDL2_image < 2.0.2
    if sdlimage.dll.version < 2002:
        skip_formats.append("svg")

    # As of SDL2_image 2.0.5, XCF support seems to be broken (fails to load
    # on 32-bit, transparent surface on 64-bit)
    # XCF support is also broken in official SDL2_image macOS .frameworks
    if sdlimage.dll.version == 2005 or ismacos:
        skip_formats.append("xcf")

    # WEBP support is broken in the 32-bit Windows SDL2_image 2.0.2 binary
    if is32bit and sdlimage.dll.version == 2002:
        skip_formats.append("webp")
    
    # QOI support requires SDL2_image 2.6.0 or newer
    if sdlimage.dll.version < 2060:
        skip_formats.append("qoi")


# List of lossy/non-color formats that shouldn't be compared against reference
# during tests
skip_color_check = ['gif', 'jpg', 'lbm', 'pbm', 'pgm', 'svg', 'webp']

# Skip ICO and CUR tests on big-endian, since they don't seem to work yet
if sys.byteorder == "big":
    skip_color_check += ['ico', 'cur']

# SDL 2.0.10 has a bug that messes up converting surfaces with transparency
if sdl2.dll.version == 2010:
    skip_color_check.append('xpm')

colors = {
    'red': color.Color(255, 0, 0, 255),
    'blue': color.Color(0, 0, 255, 255),
    'black': color.Color(0, 0, 0, 255),
    'white': color.Color(255, 255, 255, 255)
}

def check_image_contents(img):
    # Test different coordinates on surface
    pxview = sdl2ext.PixelView(img)
    img_red = color.ARGB(pxview[0][0])
    img_blue = color.ARGB(pxview[0][16])
    img_white = color.ARGB(pxview[0][31])
    img_black = color.ARGB(pxview[31][31])
    assert img_red == colors['red']
    assert img_blue == colors['blue']
    assert img_white == colors['white']
    assert img_black == colors['black']



def test_load_bmp(with_sdl):
    # Test loading a basic BMP image
    img_path = os.path.join(resource_path, "surfacetest.bmp")
    sf = sdl2ext.load_bmp(img_path)
    assert isinstance(sf, surf.SDL_Surface)
    check_image_contents(sf)
    surf.SDL_FreeSurface(sf)

    # Test exception on missing file
    bad_path = os.path.join(resource_path, "doesnt_exist.bmp")
    with pytest.raises(IOError):
        sdl2ext.load_bmp(bad_path)

    # Test exception on bad file type
    bad_type = os.path.join(resource_path, "surfacetest.png")
    with pytest.raises(sdl2ext.SDLError):
        sdl2ext.load_bmp(bad_type)


def test_save_bmp(with_sdl, tmpdir):
    # Open a BMP that we can re-save
    img_path = os.path.join(resource_path, "surfacetest.bmp")
    sf = sdl2ext.load_bmp(img_path)
    assert isinstance(sf, surf.SDL_Surface)

    # Try saving the BMP to a new folder and re-loading it
    outpath = os.path.join(str(tmpdir), "save_test.bmp")
    sdl2ext.save_bmp(sf, outpath)
    assert os.path.exists(outpath)
    sf_saved = sdl2ext.load_bmp(outpath)
    assert isinstance(sf_saved, surf.SDL_Surface)
    check_image_contents(sf_saved)

    # Try modifying/overwriting the existing BMP
    sdl2ext.fill(sf, (0, 255, 0, 255))
    sdl2ext.save_bmp(sf, outpath, overwrite=True)
    sf_saved2 = sdl2ext.load_bmp(outpath)
    assert isinstance(sf_saved2, surf.SDL_Surface)
    with pytest.raises(AssertionError):
        check_image_contents(sf_saved2)

    surf.SDL_FreeSurface(sf)
    surf.SDL_FreeSurface(sf_saved)
    surf.SDL_FreeSurface(sf_saved2)

    # Test existing file exception with overwrite=False
    with pytest.raises(RuntimeError):
        sdl2ext.save_bmp(sf_saved, outpath, overwrite=False)
    
    # Test exception with non-existent save directory
    bad_path = os.path.join(resource_path, "doesnt_exist", "tst.bmp")
    with pytest.raises(IOError):
        sdl2ext.save_bmp(sf_saved, bad_path)


@pytest.mark.skipif(not _HASSDLIMAGE, reason="Requires SDL2_image")
def test_load_img(with_sdl):
    # Test loading all test images, with and without ARGB conversion
    resources = os.listdir(resource_path)
    test_imgs = [f for f in resources if f[:11] == "surfacetest"]
    for img in test_imgs:
        img_path = os.path.join(resource_path, img)
        fmt = img.split(".")[-1]
        if fmt in skip_formats:
            continue

        sf = sdl2ext.load_img(img_path)
        assert isinstance(sf, surf.SDL_Surface)
        assert sf.format.contents.format == pixels.SDL_PIXELFORMAT_ARGB8888
        if fmt not in skip_color_check:
            check_image_contents(sf)
        surf.SDL_FreeSurface(sf)

        sf2 = sdl2ext.load_img(img_path, as_argb=False)
        assert isinstance(sf2, surf.SDL_Surface)
        surf.SDL_FreeSurface(sf2)

    # Test exception on missing file
    bad_path = os.path.join(resource_path, "doesnt_exist.bmp")
    with pytest.raises(IOError):
        sdl2ext.load_img(bad_path)

    # Test exception on bad file type
    bad_type = os.path.join(resource_path, "tuffy.ttf")
    with pytest.raises(sdl2ext.SDLError):
        sdl2ext.load_img(bad_type)


@pytest.mark.skipif(not _HASSDLIMAGE, reason="Requires SDL2_image")
def test_load_svg(with_sdl):
    # Function requires SDL_image >= 2.6.0
    if sdlimage.dll.version_tuple < (2, 6, 0):
        pytest.skip("Requires SDL2_image >= 2.6.0")

    # Test loading SVG without size
    svg_path = os.path.join(resource_path, "surfacetest.svg")
    sf = sdl2ext.load_svg(svg_path)
    assert isinstance(sf, surf.SDL_Surface)
    assert sf.format.contents.format == pixels.SDL_PIXELFORMAT_ARGB8888
    surf.SDL_FreeSurface(sf)

    # Test loading SVG at a specific size
    sf = sdl2ext.load_svg(svg_path, width = 100)
    assert isinstance(sf, surf.SDL_Surface)
    assert sf.w == 100
    surf.SDL_FreeSurface(sf)

    # Test exception on missing file
    bad_path = os.path.join(resource_path, "doesnt_exist.svg")
    with pytest.raises(IOError):
        sdl2ext.load_svg(bad_path)

    # Test exception on bad file type
    bad_type = os.path.join(resource_path, "tuffy.ttf")
    with pytest.raises(sdl2ext.SDLError):
        sdl2ext.load_svg(bad_type)


@pytest.mark.skipif(not _HASPIL, reason="Pillow library is not installed")
def test_pillow_to_image(with_sdl):
    # Import an image using Pillow
    from PIL import Image
    try:
        from PIL.Image import Palette
        WEB_PALETTE = Palette.WEB
    except ImportError:
        WEB_PALETTE = Image.WEB
    img_path = os.path.join(resource_path, "surfacetest.bmp")
    pil_img = Image.open(img_path)

    # Convert the image to an SDL surface and verify it worked
    sf = sdl2ext.pillow_to_surface(pil_img)
    assert isinstance(sf, surf.SDL_Surface)
    check_image_contents(sf)
    surf.SDL_FreeSurface(sf)

    # Try converting a palette image
    palette_img = pil_img.convert("P", palette=WEB_PALETTE)
    sfp = sdl2ext.pillow_to_surface(palette_img)
    pxformat = sfp.format.contents
    assert isinstance(sfp, surf.SDL_Surface)
    check_image_contents(sfp)
    assert pxformat.BytesPerPixel == 4
    surf.SDL_FreeSurface(sfp)

    # Try converting a palette image without ARGB conversion
    sfp2 = sdl2ext.pillow_to_surface(palette_img, False)
    pxformat = sfp2.format.contents
    assert isinstance(sfp2, surf.SDL_Surface)
    assert pxformat.BytesPerPixel == 1
    sdl_palette = pxformat.palette.contents
    pil_palette = palette_img.getpalette()
    assert sdl_palette.colors[0].r == pil_palette[0]
    assert sdl_palette.colors[0].g == pil_palette[1]
    assert sdl_palette.colors[0].b == pil_palette[2]
    surf.SDL_FreeSurface(sfp2)

    # Test loading all supported test images and compare against reference
    resources = os.listdir(resource_path)
    test_imgs = [f for f in resources if f[:11] == "surfacetest"]
    for img in test_imgs:
        fmt = img.split(".")[-1]
        if fmt in ("webp", "xcf", "lbm", "svg", "qoi"):
            continue
        pil_img = Image.open(os.path.join(resource_path, img))
        sf = sdl2ext.pillow_to_surface(pil_img)
        assert isinstance(sf, surf.SDL_Surface)
        assert sf.format.contents.format == pixels.SDL_PIXELFORMAT_ARGB8888
        if fmt not in skip_color_check:
            check_image_contents(sf)
        surf.SDL_FreeSurface(sf)


@pytest.mark.skipif(not _HASSDLIMAGE, reason="Requires SDL2_image")
def test_load_image(with_sdl):
    resources = os.listdir(resource_path)
    test_imgs = [f for f in resources if f[:11] == "surfacetest"]
    for img in test_imgs:
        img_path = os.path.join(resource_path, img)
        fmt = img.split(".")[-1]
        if fmt in skip_formats:
            continue

        # Try normal loading
        sf = sdl2ext.load_image(img_path)
        assert isinstance(sf, surf.SDL_Surface)

        # Force only PIL
        if _HASPIL and fmt not in ("webp", "xcf", "lbm", "svg", "qoi"):
            sf = sdl2ext.load_image(img_path, enforce="PIL")
            assert isinstance(sf, surf.SDL_Surface)

        # Force only sdlimage
        sf = sdl2ext.load_image(img_path, enforce="SDL")
        assert isinstance(sf, surf.SDL_Surface)

        # Clean up surface now that we're done with it
        surf.SDL_FreeSurface(sf)
