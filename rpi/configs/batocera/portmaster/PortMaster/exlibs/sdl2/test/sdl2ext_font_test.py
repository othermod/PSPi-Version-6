# -*- coding: utf-8 -*-
import gc
import pytest
from sdl2 import ext as sdl2ext
from sdl2.ext.compat import byteify
from sdl2.ext.pixelaccess import pixels2d
from sdl2.ext.surface import _create_surface
from sdl2 import surface, pixels, rwops, SDL_ClearError, SDL_GetError

_HASSDLTTF = True
try:
    from sdl2 import sdlttf
except ImportError:
    _HASSDLTTF = False


RESOURCES = sdl2ext.Resources(__file__, "resources")
RED_RGBA = (255, 0, 0, 255)
FONTMAP = ["0123456789",
           "ABCDEFGHIJ",
           "KLMNOPQRST",
           "UVWXYZ    ",
           "abcdefghij",
           "klmnopqrst",
           "uvwxyz    ",
           ",;.:!?-+()"
           ]


@pytest.fixture(scope="module")
def with_sdl():
    sdl2ext.init()
    yield
    sdl2ext.quit()

@pytest.fixture()
def with_font_ttf(with_sdl):
    if _HASSDLTTF:
        SDL_ClearError()
        fontpath = RESOURCES.get_path("tuffy.ttf")
        font = sdl2ext.FontTTF(fontpath, 20, RED_RGBA)
        assert SDL_GetError() == b""
        assert font
        yield font
        font.close()
        gc.collect()


class TestBitmapFont(object):
    __tags__ = ["sdl", "sdl2ext"]

    @classmethod
    def setup_class(cls):
        try:
            sdl2ext.init()
        except sdl2ext.SDLError:
            raise pytest.skip('Video subsystem not supported')

    @classmethod
    def teardown_class(cls):
        sdl2ext.quit()

    def setup_method(self):
        SDL_ClearError()

    def teardown_method(self):
        gc.collect()

    def test_init(self):
        # Initialize surface and sprite for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        sf = surface.SDL_LoadBMP(fontpath)
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)

        # Try SoftwareSprite surface
        font = sdl2ext.BitmapFont(sprite, (32, 32), FONTMAP)
        assert font.size == (32, 32)

        # Try SDL_Surface surface
        font = sdl2ext.BitmapFont(sf.contents, (32, 32), FONTMAP)
        assert font.size == (32, 32)

        # Try SDL_Surface pointer surface
        font = sdl2ext.BitmapFont(sf, (32, 32), FONTMAP)
        assert font.size == (32, 32)

        # Try loading a font directly from a .bmp
        font = sdl2ext.BitmapFont(fontpath, (32, 32), FONTMAP)
        assert font.size == (32, 32)

        # Test use of default fontmap and inferred character size
        font = sdl2ext.BitmapFont(sf)
        assert font.size == (32, 32)

        # Try invalid surface type
        with pytest.raises(TypeError):
            sdl2ext.BitmapFont([], (32, 32), FONTMAP)

    def test_render(self):
        # Initialize font and BitmapFont for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        sf = surface.SDL_LoadBMP(fontpath)
        font = sdl2ext.BitmapFont(sf.contents, (32, 32), FONTMAP)

        # Try rendering some text
        msg = "hello there!"
        text = font.render(msg)
        assert isinstance(text, sdl2ext.SoftwareSprite)
        assert text.size[0] == 32 * len(msg)

        # Test exception for missing glyph
        with pytest.raises(ValueError):
            font.render("this_should_fail")

    def test_render_text(self):
        # Initialize BitmapFont and dummy RGB888 surface for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        font = sdl2ext.BitmapFont(fontpath)
        rgb_surf = _create_surface(size=(320, 256), fmt="RGB888")
        font_rgb = sdl2ext.BitmapFont(rgb_surf)

        # Try rendering some text
        msg = "hello there!"
        text = font.render_text(msg)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * len(msg)
        assert text.h == 32
        surface.SDL_FreeSurface(text)

        # Try rendering with a different line height
        text = font.render_text(msg, line_h=40)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * len(msg)
        assert text.h == 40
        surface.SDL_FreeSurface(text)

        # Make sure ARGB converion works
        text = font_rgb.render_text(msg)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * len(msg)
        assert text.h == 32
        assert text.format.contents.format == pixels.SDL_PIXELFORMAT_ARGB8888
        surface.SDL_FreeSurface(text)

        # Try rendering without ARGB conversion
        text = font_rgb.render_text(msg, as_argb=False)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * len(msg)
        assert text.h == 32
        assert text.format.contents.format == pixels.SDL_PIXELFORMAT_RGB888
        surface.SDL_FreeSurface(text)

        # Test multiline rendering
        msg = "hello\nthere!"
        text = font.render_text(msg)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * 6
        assert text.h == 64
        surface.SDL_FreeSurface(text)

        # Test strings with empty lines
        msg = "hello\n\nthere!\n"
        text = font.render_text(msg)
        assert isinstance(text, surface.SDL_Surface)
        assert text.w == 32 * 6
        assert text.h == 32 * 4
        surface.SDL_FreeSurface(text)

        # Test exception for missing glyph
        with pytest.raises(ValueError):
            font.render_text("this_should_fail")

    def test_render_on(self):
        np = pytest.importorskip("numpy", reason="numpy module is not available")
        # Initialize BitmapFont for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        font = sdl2ext.BitmapFont(fontpath)

        # Try rendering some text
        target = _create_surface(size=(32*5, 32))
        view = pixels2d(target, transpose=False)
        mid_row = view[16, :].copy()
        outrect = font.render_on(target, "TEST!")
        assert not np.all(mid_row == view[16, :]) # ensure surface changed
        assert outrect == (0, 0, 32*5, 32)

        # Try rendering some text with an offset
        target2 = _create_surface(size=(32*5, 32))
        view2 = pixels2d(target2, transpose=False)
        outrect2 = font.render_on(target2, "TEST!", offset=(5, 0))
        assert not np.all(mid_row == view2[16, :]) # ensure surface changed
        assert not np.all(view[16, :] == view2[16, :]) # ensure offset worked
        assert outrect2 == (5, 0, 32*5 + 5, 32)

        surface.SDL_FreeSurface(target)
        surface.SDL_FreeSurface(target2)

        # Test exception for missing glyph
        with pytest.raises(ValueError):
            font.render_on(target, "%nope")

    def test_remap(self):
        # Initialize BitmapFont for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        font = sdl2ext.BitmapFont(fontpath)
        msg = "hello there!"

        # Remap the l to be narrower and try rendering
        font.remap("l", 32, 160, 12, 32)
        text = font.render_text(msg)
        assert text.w == (32 * len(msg) - 40)
        assert text.h == 32

        surface.SDL_FreeSurface(text)

        # Test exceptions on bad input
        with pytest.raises(ValueError):
            font.remap("hi", 4, 4, 4, 4)
        with pytest.raises(ValueError):
            font.remap("h", 10, 32, 32, 0)
        with pytest.raises(ValueError):
            font.remap("h", 32, 1000, 32, 32)

    def test_contains(self):
        # Initialize BitmapFont for tests
        fontpath = byteify(RESOURCES.get_path("font.bmp"), "utf-8")
        font = sdl2ext.BitmapFont(fontpath)

        for ch in "abcde12345.-,+":
            assert font.contains(ch)
        del font.offsets[" "]
        for ch in u" äöüß":
            assert not font.contains(ch)

    def test_can_render(self):
        sf = surface.SDL_LoadBMP(byteify(RESOURCES.get_path("font.bmp"),
                                         "utf-8"))
        assert isinstance(sf.contents, surface.SDL_Surface)
        font = sdl2ext.BitmapFont(sf, (32, 32), FONTMAP)
        assert isinstance(font, sdl2ext.BitmapFont)

        assert font.can_render("text")
        assert font.can_render("473285435hfsjadfhriuewtrhefd")
        assert not font.can_render("testä")



@pytest.mark.skipif(not _HASSDLTTF, reason="SDL_TTF library not available")
class TestFontTTF(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        # Try opening and closing a font
        fontpath = RESOURCES.get_path("tuffy.ttf")
        font = sdl2ext.FontTTF(fontpath, 20, RED_RGBA)
        assert SDL_GetError() == b""
        assert font
        font.close()

        # Try opening a font with size specified in pt
        font = sdl2ext.FontTTF(fontpath, "20pt", RED_RGBA)
        assert SDL_GetError() == b""
        assert font
        font.close()

        # Try opening a font with size specified in pixels
        font = sdl2ext.FontTTF(fontpath, "20px", RED_RGBA)
        assert SDL_GetError() == b""
        assert font
        
        # Try opening a font with a custom set of height chars
        chars = "aeiou"
        font2 = sdl2ext.FontTTF(fontpath, "20px", RED_RGBA, height_chars=chars)
        assert SDL_GetError() == b""
        assert font
        assert font._parse_size("20px") != font2._parse_size("20px")
        font.close()
        font2.close()

        # Test exception on invalid font path
        with pytest.raises(IOError):
            sdl2ext.FontTTF("missing.ttf", 16, RED_RGBA)
        
        # Text exception on invalid size
        with pytest.raises(ValueError):
            sdl2ext.FontTTF(fontpath, 0, RED_RGBA)

        # Test exception on missing height chars
        with pytest.raises(RuntimeError):
            sdl2ext.FontTTF(fontpath, 20, RED_RGBA, height_chars=u"的是不")

    def test_init_rw(self, with_sdl):
        # Try opening and closing a font
        fontpath = RESOURCES.get_path("tuffy.ttf")
        font_file = open(fontpath, "rb")
        font_rw = rwops.rw_from_object(font_file)
        font = sdl2ext.FontTTF(font_rw, 20, RED_RGBA)
        assert SDL_GetError() == b""
        assert font
        font.close()

    def test_get_ttf_font(self, with_font_ttf):
        font = with_font_ttf
        ttf_font = font.get_ttf_font()
        assert isinstance(ttf_font, sdlttf.TTF_Font)

        # Test exception for missing style
        with pytest.raises(ValueError):
            font.get_ttf_font("small")

    def test_add_style(self, with_font_ttf):
        font = with_font_ttf

        # Add some new styles
        font.add_style('large', '40px', RED_RGBA)
        font.add_style('red', 20, pixels.SDL_Color(255, 0, 0))
        font.add_style('red_on_white', 20, (255, 0, 0), (255, 255, 255))

        # Test exception for existing style name
        with pytest.raises(ValueError):
            font.add_style('large', '50px', RED_RGBA)

        # Test exception for invalid size unit
        with pytest.raises(ValueError):
            font.add_style('unit_err', '10cm', RED_RGBA)

        # Test exception for non-integer size
        with pytest.raises(ValueError):
            font.add_style('float_err', '10.5pt', RED_RGBA)

    def test_render_text(self, with_font_ttf):
        font = with_font_ttf

        # Try rendering some text
        msg = "hello there!"
        text = font.render_text(msg)
        assert SDL_GetError() == b""
        assert isinstance(text, surface.SDL_Surface)
        assert text.format.contents.format == pixels.SDL_PIXELFORMAT_ARGB8888

        # Test multiline rendering
        msg = "hello\nthere!"
        text2 = font.render_text(msg)
        assert SDL_GetError() == b""
        assert isinstance(text2, surface.SDL_Surface)
        assert text2.h > text.h

        # Test strings with empty lines
        msg = "hello\n\nthere!\n"
        text3 = font.render_text(msg)
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        assert text3.h > text2.h
        surface.SDL_FreeSurface(text3)

        # Test custom line height
        msg = "hello\nthere!"
        text3 = font.render_text(msg, line_h=100)
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        assert text3.h > text2.h
        surface.SDL_FreeSurface(text3)

        # Test custom line height as a string (in px)
        msg = "hello\nthere!"
        text3 = font.render_text(msg, line_h='100px')
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        assert text3.h > text2.h
        surface.SDL_FreeSurface(text3)

        # Test custom line height as a percentage
        msg = "hello\nthere!"
        text3 = font.render_text(msg, line_h='110%')
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        assert text3.h > text2.h
        surface.SDL_FreeSurface(text3)

        # Test wrap width
        msg = "hello there! This is a very long line of text."
        text3 = font.render_text(msg, width=200)
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        assert text3.h > text.h
        surface.SDL_FreeSurface(text3)

        # Test custom font style (no bg color)
        msg = "hello there!"
        font.add_style("blue", 30, (0, 0, 255, 255))
        text3 = font.render_text(msg, "blue")
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        surface.SDL_FreeSurface(text3)

        # Test custom font style (w/ bg color)
        msg = "hello there!"
        font.add_style("red_on_white", 30, RED_RGBA, (255, 255, 255))
        text3 = font.render_text(msg, "red_on_white")
        assert SDL_GetError() == b""
        assert isinstance(text3, surface.SDL_Surface)
        surface.SDL_FreeSurface(text3)

        # Test font alignment (not extensive)
        msg = "hello there!\nThis is a very long line of\ntext."
        for align in ["left", "center", "right"]:
            tmp = font.render_text(msg, align=align)
            assert SDL_GetError() == b""
            assert isinstance(text3, surface.SDL_Surface)
            surface.SDL_FreeSurface(tmp)

        surface.SDL_FreeSurface(text)
        surface.SDL_FreeSurface(text2)

        # Test exception for empty string
        with pytest.raises(ValueError):
            font.render_text("")

        # Test exception for missing style
        with pytest.raises(ValueError):
            font.render_text(msg, "small")

        # Test exceptions for bad line height
        with pytest.raises(ValueError):
            font.render_text(msg, line_h=12.4)
        with pytest.raises(ValueError):
            font.render_text(msg, line_h=0)
        with pytest.raises(ValueError):
            font.render_text(msg, line_h='-50%')
        with pytest.raises(ValueError):
            font.render_text(msg, line_h='100pt')

        # Test exception for bad alignment
        with pytest.raises(ValueError):
            font.render_text(msg, align="flush")

    def test_close(self, with_font_ttf):
        font = with_font_ttf
        font.close()

        # Test that you can close the font multiple times
        font.close()

        # Make sure you can't use font after closing it
        with pytest.raises(RuntimeError):
            font.get_ttf_font()
        with pytest.raises(RuntimeError):
            font.add_style('large', 40, RED_RGBA)
        with pytest.raises(RuntimeError):
            font.render_text("hello!")
        with pytest.raises(RuntimeError):
            font.contains("A")
        with pytest.raises(RuntimeError):
            font.family_name
        with pytest.raises(RuntimeError):
            font.style_name
        with pytest.raises(RuntimeError):
            font.is_fixed_width

    def test_contains(self, with_font_ttf):
        font = with_font_ttf
        for ch in "abcde12345":
            assert font.contains(ch)
        for ch in u"的是不":
            assert not font.contains(ch)

    def test_family_name(self, with_font_ttf):
        font = with_font_ttf
        name = font.family_name
        assert name == None or isinstance(name, str)

    def test_style_name(self, with_font_ttf):
        font = with_font_ttf
        name = font.style_name
        assert name == None or isinstance(name, str)

    def test_is_fixed_width(self, with_font_ttf):
        font = with_font_ttf
        assert font.is_fixed_width == False


@pytest.mark.skipif(not _HASSDLTTF, reason="SDL_TTF library not available")
class TestFontManager(object):
    __tags__ = ["sdl", "sdl2ext"]

    @classmethod
    def setup_class(cls):
        try:
            sdl2ext.init()
        except sdl2ext.SDLError:
            raise pytest.skip('Video subsystem not supported')

    @classmethod
    def teardown_class(cls):
        sdl2ext.quit()

    def setup_method(self):
        SDL_ClearError()

    def teardown_method(self):
        gc.collect()

    def test_init(self):
        fm = sdl2ext.FontManager(RESOURCES.get_path("tuffy.ttf"),
                                 bg_color=(100, 0, 0))
        assert isinstance(fm, sdl2ext.FontManager)
        assert fm.default_font == "tuffy"
        assert fm.size == 16
        assert fm.bg_color == sdl2ext.Color(100, 0, 0, 0)

    def test_default_font(self):
        fontpath = RESOURCES.get_path("tuffy.ttf")
        fm = sdl2ext.FontManager(fontpath)
        assert fm.default_font == "tuffy"
        assert fm.size == 16
        with pytest.raises(ValueError):
            fm.default_font = "Inexistent Alias"
        fm.add(fontpath, alias = "tuffy.copy", size = 10)
        fm.default_font = "tuffy.copy"
        fm.size = 10
        assert fm.default_font == "tuffy.copy"
        assert fm.size == 10
        fm.default_font = "tuffy.copy"
        fm.size = 16
        assert fm.default_font == "tuffy.copy"
        assert fm.size == 16

    def test_add(self):
        fm = sdl2ext.FontManager(RESOURCES.get_path("tuffy.ttf"))
        assert "tuffy" in fm.aliases
        assert "tuffy" in fm.fonts
        assert 16 in fm.fonts["tuffy"]
        assert isinstance(fm.fonts["tuffy"][16].contents, sdlttf.TTF_Font)

        # Do some metrics tests
        # NOTE: Ascent & other font metrics changed in FreeType 2.10, so we 
        # test against both < 2.10 and >= 2.10 values
        font = fm.fonts["tuffy"][16]
        assert sdlttf.TTF_FontAscent(font) in [13, 16]
        fm.add(RESOURCES.get_path("tuffy.ttf"), size=12)
        font = fm.fonts["tuffy"][12]
        assert sdlttf.TTF_FontAscent(font) in [10, 12]

        with pytest.raises(IOError):
            fm.add("inexistent.ttf")
        # I don't find a scenario raising a TTF_Error.
        # self.assertRaises(sdl2ext.SDLError, fm.add, "resources/tuffy.ttf",
        #                   size=-1)

        # Close the font manager and add a new font
        fm.close()
        fm.add(RESOURCES.get_path("tuffy.ttf"), size=12)
        assert isinstance(fm.fonts["tuffy"][12].contents, sdlttf.TTF_Font)

    def test_close(self):
        fm = sdl2ext.FontManager(RESOURCES.get_path("tuffy.ttf"))
        fm.add(RESOURCES.get_path("tuffy.ttf"), size=20)
        fm.add(RESOURCES.get_path("tuffy.ttf"), alias="Foo", size=10)
        fm.close()
        assert fm.fonts == {}
        # How to make sure TTF_CloseFont was called on each loaded font?

    def test_render(self):
        fm = sdl2ext.FontManager(RESOURCES.get_path("tuffy.ttf"))
        text_surf = fm.render("text")
        assert isinstance(text_surf, surface.SDL_Surface)
        assert text_surf.w > 1

        text_surf = fm.render("text", size=10)
        assert isinstance(text_surf, surface.SDL_Surface)

        text_surf = fm.render("""
text long enough to have it wrapped at 100 px width.""", size=20, width=100)
        assert isinstance(text_surf, surface.SDL_Surface)
        assert text_surf.w > 1
        assert text_surf.w == 100
        with pytest.raises(KeyError):
            fm.render("text", alias="inexistent")
