import io
import os
import sys
import ctypes
import pytest

import sdl2
from sdl2 import SDL_Init, SDL_Quit, version, surface, rwops, render

sdlimage = pytest.importorskip("sdl2.sdlimage")


formats = [
    "bmp",
    "cur",
    "gif",
    "ico",
    "jpg",
    "lbm",
    "pbm",
    "pcx",
    "pgm",
    "png",
    "pnm",
    "ppm",
    "svg",
    "tga",
    "tif",
    "webp",
    "xcf",
    "xpm",
    #"xv", # no idea how to create one, seems like a long-dead format?
    "qoi",
    #"jxl", # not yet available in official Windows/macOS binaries
    #"avif", # not yet available in official Windows/macOS binaries
]

animation_formats = [
    "gif",
]


### Disable problem formats on specific versions/platforms ###

img_ver = sdlimage.dll.version
is32bit = sys.maxsize <= 2**32
ismacos = sys.platform == "darwin"
iswindows = "win" in sys.platform
isconda = os.getenv("CONDA_PREFIX") != None

# QOI unsupported on SDL2_image < 2.6.0
if img_ver < 2060:
    formats.remove("qoi")

# SVG unsupported on SDL2_image < 2.0.2 as well as in Conda's current (2.0.5)
# Windows binaries
if img_ver < 2002 or (isconda and iswindows):
    formats.remove("svg")

# Prior to 2.6.0, XCF was broken on official 32-bit builds and macOS frameworks. 
# It is also currently broken in Conda's SDL2_image Windows binaries
bad_xcf = False
xcf_broken = img_ver <= 2005 and (is32bit or ismacos)
if xcf_broken or (isconda and iswindows):
    formats.remove("xcf")
    bad_xcf = True

# WEBP support seems to be broken in the 32-bit Windows SDL2_image 2.0.2 binary
# and is missing in the official macOS 2.6.0 binary
bad_webp = (is32bit and img_ver == 2002) or (ismacos and img_ver == 2060)
if bad_webp:
    formats.remove("webp")

# JPG saving requires SDL2_image >= 2.0.2 and is broken in older macOS binaries
no_jpeg_save = img_ver < 2002 or (ismacos and img_ver < 2060)


@pytest.fixture(scope="module")
def with_sdl_image(with_sdl):
    flags = (
        sdlimage.IMG_INIT_JPG | sdlimage.IMG_INIT_PNG |
        sdlimage.IMG_INIT_TIF  | sdlimage.IMG_INIT_WEBP
    )
    sdlimage.IMG_Init(flags)
    yield
    sdlimage.IMG_Quit()

@pytest.fixture
def sw_renderer(with_sdl_image):
    sf = surface.SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)
    rd = render.SDL_CreateSoftwareRenderer(sf)
    yield rd
    render.SDL_DestroyRenderer(rd)
    surface.SDL_FreeSurface(sf)

def _get_image_path(fmt):
    fname = "surfacetest.{0}".format(fmt)
    testdir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(testdir, "resources", fname)

def _get_image_rw(fmt):
    fpath = _get_image_path(fmt).encode('utf-8')
    return sdl2.SDL_RWFromFile(fpath, b"r")

def _get_animation_path(fmt):
    fname = "animationtest.{0}".format(fmt)
    testdir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(testdir, "resources", fname)

def _verify_img_load(surf):
    if not surf:
        assert sdlimage.IMG_GetError() == b""
        assert surf
    assert isinstance(surf.contents, surface.SDL_Surface)

def _verify_anim_load(anim):
    if not anim:
        assert sdlimage.IMG_GetError() == b""
        assert anim
    assert isinstance(anim.contents, sdlimage.IMG_Animation)
    assert anim.contents.w == 32
    assert anim.contents.h == 32
    assert anim.contents.count == 4


def test_IMG_Linked_Version():
    v = sdlimage.IMG_Linked_Version()
    assert isinstance(v.contents, version.SDL_version)
    assert v.contents.major == 2
    assert v.contents.minor >= 0
    assert v.contents.patch >= 0
    t = (v.contents.major, v.contents.minor, v.contents.patch)
    assert t >= (2, 0, 1)
    assert t == sdlimage.dll.version_tuple

def test_IMG_Init():
    global formats
    SDL_Init(0)
    supported = []
    libs = {
        'JPEG': sdlimage.IMG_INIT_JPG,
        'PNG': sdlimage.IMG_INIT_PNG,
        'TIFF': sdlimage.IMG_INIT_TIF,
        'WEBP': sdlimage.IMG_INIT_WEBP,
        'JPEG XL': sdlimage.IMG_INIT_JXL,
        'AVIF': sdlimage.IMG_INIT_AVIF,
    }
    for lib in libs.keys():
        flags = libs[lib]
        ret = sdlimage.IMG_Init(flags)
        err = sdlimage.IMG_GetError()
        if err:
            err = err.decode('utf-8')
            print("Error loading {0} library: {1}".format(lib, err))
            sdl2.SDL_ClearError()
        if ret & flags == flags:
            supported.append(lib)
        elif lib.lower() in formats:
            formats.remove(lib.lower())
        sdlimage.IMG_Quit()
    print("Supported image libraries:")
    print(supported)
    assert len(supported) # Only fail if none supported

def test_IMG_Load(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        sf = sdlimage.IMG_Load(fpath.encode("utf-8"))
        _verify_img_load(sf)
        surface.SDL_FreeSurface(sf)

def test_IMG_Load_RW(with_sdl_image):
    skip = ['tga'] # TGA broken for Load_RW
    for fmt in formats:
        if fmt in skip:
            continue
        rw = _get_image_rw(fmt)
        sf = sdlimage.IMG_Load_RW(rw, False)
        sdl2.SDL_RWclose(rw)
        _verify_img_load(sf)
        surface.SDL_FreeSurface(sf)

def test_IMG_LoadTexture(sw_renderer):
    rd = sw_renderer
    skip = []
    for fmt in formats:
        if fmt in skip:
            continue
        fpath = _get_image_path(fmt)
        tex = sdlimage.IMG_LoadTexture(rd, fpath.encode("utf-8"))
        if not tex:
            assert sdlimage.IMG_GetError() == b""
            assert tex
        assert isinstance(tex.contents, render.SDL_Texture)
        render.SDL_DestroyTexture(tex)

def test_IMG_LoadTexture_RW(sw_renderer):
    rd = sw_renderer
    skip = ['svg', 'tga'] # TGA & SVG broken for LoadTexture_RW
    for fmt in formats:
        if fmt in skip:
            continue
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            tex = sdlimage.IMG_LoadTexture_RW(rd, rwops.rw_from_object(fp), 0)
            if not tex:
                assert sdlimage.IMG_GetError() == b""
                assert tex
            assert isinstance(tex.contents, render.SDL_Texture)
            render.SDL_DestroyTexture(tex)

def test_IMG_LoadTextureTyped_RW(sw_renderer):
    rd = sw_renderer
    skip = ['svg'] # SVG broken for LoadTextureTyped_RW
    for fmt in formats:
        if fmt in skip:
            continue
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            rw = rwops.rw_from_object(fp)
            fmtx = fmt.upper().encode("utf-8")
            tex = sdlimage.IMG_LoadTextureTyped_RW(rd, rw, 0, fmtx)
            if not tex:
                assert sdlimage.IMG_GetError() == b""
                assert tex
            assert isinstance(tex.contents, render.SDL_Texture)
        render.SDL_DestroyTexture(tex)

def test_IMG_LoadTyped_RW(with_sdl_image):
    skip = []
    for fmt in formats:
        if fmt in skip:
            continue
        rw = _get_image_rw(fmt)
        sf = sdlimage.IMG_LoadTyped_RW(rw, False, fmt.upper().encode("utf-8"))
        sdl2.SDL_RWclose(rw)
        _verify_img_load(sf)
        surface.SDL_FreeSurface(sf)

@pytest.mark.skip("not yet available in official binaries")
@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadAVIF_RW(with_sdl_image):
    fp = io.open(_get_image_path("avif"), "rb")
    sf = sdlimage.IMG_LoadBMP_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadBMP_RW(with_sdl_image):
    fp = io.open(_get_image_path("bmp"), "rb")
    sf = sdlimage.IMG_LoadBMP_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadCUR_RW(with_sdl_image):
    fp = io.open(_get_image_path("cur"), "rb")
    sf = sdlimage.IMG_LoadCUR_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadGIF_RW(with_sdl_image):
    fp = io.open(_get_image_path("gif"), "rb")
    sf = sdlimage.IMG_LoadGIF_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadICO_RW(with_sdl_image):
    fp = io.open(_get_image_path("ico"), "rb")
    sf = sdlimage.IMG_LoadICO_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadJPG_RW(with_sdl_image):
    fp = io.open(_get_image_path("jpg"), "rb")
    sf = sdlimage.IMG_LoadJPG_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skip("not yet available in official binaries")
@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadJXL_RW(with_sdl_image):
    fp = io.open(_get_image_path("jxl"), "rb")
    sf = sdlimage.IMG_LoadBMP_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadLBM_RW(with_sdl_image):
    fp = io.open(_get_image_path("lbm"), "rb")
    sf = sdlimage.IMG_LoadLBM_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadPCX_RW(with_sdl_image):
    fp = io.open(_get_image_path("pcx"), "rb")
    sf = sdlimage.IMG_LoadPCX_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadPNG_RW(with_sdl_image):
    fp = io.open(_get_image_path("png"), "rb")
    sf = sdlimage.IMG_LoadPNG_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadPNM_RW(with_sdl_image):
    fp = io.open(_get_image_path("pnm"), "rb")
    sf = sdlimage.IMG_LoadPNM_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skipif(sdlimage.dll.version < 2002, reason="Added in 2.0.2")
@pytest.mark.xfail(isconda and iswindows, reason="Broken w/ win64 Conda")
def test_IMG_LoadSVG_RW(with_sdl_image):
    fp = io.open(_get_image_path("svg"), "rb")
    sf = sdlimage.IMG_LoadSVG_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadQOI_RW(with_sdl_image):
    fp = io.open(_get_image_path("qoi"), "rb")
    sf = sdlimage.IMG_LoadQOI_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadTGA_RW(with_sdl_image):
    fp = io.open(_get_image_path("tga"), "rb")
    sf = sdlimage.IMG_LoadTGA_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadTIF_RW(with_sdl_image):
    fp = io.open(_get_image_path("tif"), "rb")
    sf = sdlimage.IMG_LoadTIF_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.xfail(bad_webp, reason="WEBP not availale or broken")
def test_IMG_LoadWEBP_RW(with_sdl_image):
    fp = io.open(_get_image_path("webp"), "rb")
    sf = sdlimage.IMG_LoadWEBP_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.xfail(bad_xcf, reason="XCF currently broken on some platforms")
def test_IMG_LoadXCF_RW(with_sdl_image):
    fp = io.open(_get_image_path("xcf"), "rb")
    sf = sdlimage.IMG_LoadXCF_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

def test_IMG_LoadXPM_RW(with_sdl_image):
    fp = io.open(_get_image_path("xpm"), "rb")
    sf = sdlimage.IMG_LoadXPM_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skip("not implemented")
def test_IMG_LoadXV_RW(with_sdl_image):
    fp = io.open(_get_image_path("xv"), "rb")
    sf = sdlimage.IMG_LoadXV_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.xfail(isconda and iswindows, reason="Broken w/ win64 Conda")
@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadSizedSVG_RW(with_sdl_image):
    fp = io.open(_get_image_path("svg"), "rb")
    sf = sdlimage.IMG_LoadSizedSVG_RW(rwops.rw_from_object(fp), 100, 0)
    fp.close()
    _verify_img_load(sf)
    assert sf.contents.w == 100
    assert sf.contents.h == 100
    surface.SDL_FreeSurface(sf)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_isAVIF(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "avif":
                assert sdlimage.IMG_isAVIF(imgrw)
            else:
                assert not sdlimage.IMG_isAVIF(imgrw)

def test_IMG_isBMP(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "bmp":
                assert sdlimage.IMG_isBMP(imgrw)
            else:
                assert not sdlimage.IMG_isBMP(imgrw)

def test_IMG_isCUR(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "cur":
                assert sdlimage.IMG_isCUR(imgrw)
            else:
                assert not sdlimage.IMG_isCUR(imgrw)

def test_IMG_isGIF(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "gif":
                assert sdlimage.IMG_isGIF(imgrw)
            else:
                assert not sdlimage.IMG_isGIF(imgrw)

def test_IMG_isICO(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "ico":
                assert sdlimage.IMG_isICO(imgrw)
            else:
                assert not sdlimage.IMG_isICO(imgrw)

def test_IMG_isJPG(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "jpg":
                assert sdlimage.IMG_isJPG(imgrw)
            else:
                assert not sdlimage.IMG_isJPG(imgrw)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_isJXL(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "jxl":
                assert sdlimage.IMG_isJXL(imgrw)
            else:
                assert not sdlimage.IMG_isJXL(imgrw)

def test_IMG_isLBM(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "lbm":
                assert sdlimage.IMG_isLBM(imgrw)
            else:
                assert not sdlimage.IMG_isLBM(imgrw)

def test_IMG_isPCX(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "pcx":
                assert sdlimage.IMG_isPCX(imgrw)
            else:
                assert not sdlimage.IMG_isPCX(imgrw)

def test_IMG_isPNG(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "png":
                assert sdlimage.IMG_isPNG(imgrw)
            else:
                assert not sdlimage.IMG_isPNG(imgrw)

def test_IMG_isPNM(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt in ("pnm", "pbm", "ppm", "pgm"):
                assert sdlimage.IMG_isPNM(imgrw)
            else:
                assert not sdlimage.IMG_isPNM(imgrw)

@pytest.mark.skipif(sdlimage.dll.version < 2002, reason="Added in 2.0.2")
@pytest.mark.xfail(isconda and iswindows, reason="Broken w/ win64 Conda")
def test_IMG_isSVG(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "svg":
                assert sdlimage.IMG_isSVG(imgrw)
            else:
                assert not sdlimage.IMG_isSVG(imgrw)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_isQOI(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "qoi":
                assert sdlimage.IMG_isQOI(imgrw)
            else:
                assert not sdlimage.IMG_isQOI(imgrw)

def test_IMG_isTIF(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "tif":
                assert sdlimage.IMG_isTIF(imgrw)
            else:
                assert not sdlimage.IMG_isTIF(imgrw)

@pytest.mark.xfail(bad_webp, reason="WEBP not availale or broken")
def test_IMG_isWEBP(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "webp":
                assert sdlimage.IMG_isWEBP(imgrw)
            else:
                assert not sdlimage.IMG_isWEBP(imgrw)

@pytest.mark.xfail(bad_xcf, reason="XCF currently broken on some platforms")
def test_IMG_isXCF(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "xcf":
                assert sdlimage.IMG_isXCF(imgrw)
            else:
                assert not sdlimage.IMG_isXCF(imgrw)

def test_IMG_isXPM(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "xpm":
                assert sdlimage.IMG_isXPM(imgrw)
            else:
                assert not sdlimage.IMG_isXPM(imgrw)

@pytest.mark.skip("not implemented")
def test_IMG_isXV(with_sdl_image):
    for fmt in formats:
        fpath = _get_image_path(fmt)
        with io.open(fpath, "rb") as fp:
            imgrw = rwops.rw_from_object(fp)
            if fmt == "xv":
                assert sdlimage.IMG_isXV(imgrw)
            else:
                assert not sdlimage.IMG_isXV(imgrw)

@pytest.mark.skipif(hasattr(sys, "pypy_version_info"),
    reason="PyPy's ctypes fails to pass a correct string array")
def test_IMG_ReadXPMFromArray(with_sdl_image):
    fp = io.open(_get_image_path("xpm"), "rb")
    xpm = b""
    fp.readline()  # /* XPM */
    fp.readline()  # static char * surfacetest_xpm[] = {
    lbuf = fp.readlines()
    fp.close()
    for line in lbuf:
        if line.endswith(b"};"):
            xpm += line[1:-4]
        else:
            xpm += line[1:-3]
    pxpm = ctypes.c_char_p(xpm)
    sf = sdlimage.IMG_ReadXPMFromArray(ctypes.byref(pxpm))
    _verify_img_load(sf)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_ReadXPMFromArrayToRGB888(with_sdl_image):
    fp = io.open(_get_image_path("xpm"), "rb")
    xpm = b""
    fp.readline()  # /* XPM */
    fp.readline()  # static char * surfacetest_xpm[] = {
    lbuf = fp.readlines()
    fp.close()
    for line in lbuf:
        if line.endswith(b"};"):
            xpm += line[1:-4]
        else:
            xpm += line[1:-3]
    pxpm = ctypes.c_char_p(xpm)
    sf = sdlimage.IMG_ReadXPMFromArrayToRGB888(ctypes.byref(pxpm))
    _verify_img_load(sf)
    assert sf.contents.format.contents.format == sdl2.SDL_PIXELFORMAT_ARGB8888
    surface.SDL_FreeSurface(sf)

def test_IMG_SavePNG(tmpdir):
    # Open a PNG that we can re-save
    fpath = _get_image_path("png")
    sf = sdlimage.IMG_Load(fpath.encode("utf-8"))
    assert isinstance(sf.contents, surface.SDL_Surface)

    # Try saving the PNG to a new folder
    outpath = os.path.join(str(tmpdir), "save_test.png")
    ret = sdlimage.IMG_SavePNG(sf, outpath.encode("utf-8"))
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert os.path.exists(outpath)
    surface.SDL_FreeSurface(sf)

def test_IMG_SavePNG_RW(tmpdir):
    # Open a PNG that we can re-save
    fpath = _get_image_path("png")
    sf = sdlimage.IMG_Load(fpath.encode("utf-8"))
    assert isinstance(sf.contents, surface.SDL_Surface)

    # Try saving the PNG to a new folder
    outpath = os.path.join(str(tmpdir), "save_test.png")
    rw = rwops.SDL_RWFromFile(outpath.encode("utf-8"), b"wb")
    ret = sdlimage.IMG_SavePNG_RW(sf, rw, 0)
    sdl2.SDL_RWclose(rw)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert os.path.exists(outpath)

    # Try reopening the RW as a PNG
    sf2 = sdlimage.IMG_Load(outpath.encode("utf-8"))
    _verify_img_load(sf2)
    surface.SDL_FreeSurface(sf)
    surface.SDL_FreeSurface(sf2)

@pytest.mark.skipif(no_jpeg_save, reason="Added in 2.0.2, not in macOS bnaries")
def test_IMG_SaveJPG(tmpdir):
    # Open a PNG that we can save to JPG
    fpath = _get_image_path("png")
    sf = sdlimage.IMG_Load(fpath.encode("utf-8"))
    assert isinstance(sf.contents, surface.SDL_Surface)

    # Try saving as JPG to a new folder
    outpath = os.path.join(str(tmpdir), "save_test.jpg")
    ret = sdlimage.IMG_SaveJPG(sf, outpath.encode("utf-8"), 90)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert os.path.exists(outpath)
    surface.SDL_FreeSurface(sf)

@pytest.mark.skipif(no_jpeg_save, reason="Added in 2.0.2, not in macOS bnaries")
def test_IMG_SaveJPG_RW(tmpdir):
    # Open a PNG that we can save to JPG
    fpath = _get_image_path("png")
    sf = sdlimage.IMG_Load(fpath.encode("utf-8"))
    assert isinstance(sf.contents, surface.SDL_Surface)

    # Try saving as JPG to a new folder
    outpath = os.path.join(str(tmpdir), "save_test.jpg")
    rw = rwops.SDL_RWFromFile(outpath.encode("utf-8"), b"wb")
    ret = sdlimage.IMG_SaveJPG_RW(sf, rw, 0, 90)
    sdl2.SDL_RWclose(rw)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    assert os.path.exists(outpath)

    # Try reopening the RW as a JPG
    sf2 = sdlimage.IMG_Load(outpath.encode("utf-8"))
    _verify_img_load(sf2)
    surface.SDL_FreeSurface(sf)
    surface.SDL_FreeSurface(sf2)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadFreeAnimation(with_sdl_image):
    for fmt in animation_formats:
        fpath = _get_animation_path(fmt)
        anim = sdlimage.IMG_LoadAnimation(fpath.encode("utf-8"))
        _verify_anim_load(anim)
        # Do full test of IMG_Animation structure
        for frame in range(anim.contents.count):
            assert anim.contents.delays[frame] == 1000
            framesurf = anim.contents.frames[frame].contents
            assert isinstance(framesurf, surface.SDL_Surface)
            assert framesurf.w == 32
        sdlimage.IMG_FreeAnimation(anim)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadAnimation_RW():
    for fmt in animation_formats:
        fpath = _get_animation_path(fmt)
        with io.open(fpath, "rb") as fp:
            anim = sdlimage.IMG_LoadAnimation_RW(rwops.rw_from_object(fp), 0)
            _verify_anim_load(anim)
            sdlimage.IMG_FreeAnimation(anim)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadAnimationTyped_RW():
    for fmt in animation_formats:
        fpath = _get_animation_path(fmt)
        with io.open(fpath, "rb") as fp:
            anim = sdlimage.IMG_LoadAnimationTyped_RW(
                rwops.rw_from_object(fp), 0, fmt.upper().encode("utf-8")
            )
            _verify_anim_load(anim)
            sdlimage.IMG_FreeAnimation(anim)

@pytest.mark.skipif(sdlimage.dll.version < 2060, reason="Added in 2.6.0")
def test_IMG_LoadGIFAnimation_RW():
    fp = io.open(_get_animation_path("gif"), "rb")
    anim = sdlimage.IMG_LoadGIFAnimation_RW(rwops.rw_from_object(fp))
    fp.close()
    _verify_anim_load(anim)
    sdlimage.IMG_FreeAnimation(anim)
