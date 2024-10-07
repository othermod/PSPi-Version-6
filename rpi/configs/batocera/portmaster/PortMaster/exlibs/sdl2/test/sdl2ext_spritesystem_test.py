import gc
import sys
import pytest
from ctypes import ArgumentError
from sdl2 import ext as sdl2ext
from sdl2.ext.resources import Resources
from sdl2.render import (
    SDL_TEXTUREACCESS_STATIC, SDL_TEXTUREACCESS_STREAMING, SDL_TEXTUREACCESS_TARGET
)
from sdl2.surface import SDL_Surface, SDL_CreateRGBSurface, SDL_FreeSurface
from sdl2.pixels import SDL_MapRGBA
from sdl2.error import SDL_GetError, SDL_ClearError

try:
    import PIL
    _HASPIL = True
except ImportError:
    _HASPIL = False

RESOURCES = Resources(__file__, "resources")

BLACK = (0, 0, 0, 255)
RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)

sprite_test_sizes = [
    (1, 1), (100, 100), (16, 32), (55, 77), (20, 4)
]


def check_pixels(surf, w, h, sprite, c1, c2, cx=0, cy=0):
    cx = cx + sprite.x
    cy = cy + sprite.y
    cw, ch = sprite.size
    cmy = cy + ch
    cmx = cx + cw
    c1 = SDL_MapRGBA(surf.format, c1[0], c1[1], c1[2], c1[3])
    c2 = [SDL_MapRGBA(surf.format, c[0], c[1], c[2], c[3]) for c in c2]
    view = sdl2ext.PixelView(surf)
    for y in range(w):
        for x in range(h):
            if cy <= y < cmy and cx <= x < cmx:
                assert view[y][x] == c1
            else:
                assert view[y][x] in c2
    del view


class TestSpriteFactory(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        factory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)
        assert isinstance(factory, sdl2ext.SpriteFactory)
        assert factory.default_args == {}

        factory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE, bananas="tasty")
        assert isinstance(factory, sdl2ext.SpriteFactory)
        assert factory.default_args == {"bananas": "tasty"}

        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)

        factory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        assert isinstance(factory, sdl2ext.SpriteFactory)

        factory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        assert isinstance(factory, sdl2ext.SpriteFactory)
        assert factory.default_args == {"renderer": renderer}

        with pytest.raises(ValueError):
            sdl2ext.SpriteFactory("Test")
        with pytest.raises(ValueError):
            sdl2ext.SpriteFactory(-456)

    def test_create_sprite(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        tfactory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        sfactory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)

        for w, h in sprite_test_sizes:
            for bpp in (1, 4, 8, 12, 15, 16, 24, 32):
                sprite = sfactory.create_sprite(size=(w, h), bpp=bpp)
                assert isinstance(sprite, sdl2ext.SoftwareSprite)
                assert SDL_GetError() == b""
            sprite = tfactory.create_sprite(size=(w, h))
            assert isinstance(sprite, sdl2ext.TextureSprite)
            assert SDL_GetError() == b""

        with pytest.raises(sdl2ext.SDLError):
            tfactory.create_sprite(size=(0, 1))

    def test_create_software_sprite(self, with_sdl):
        factory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)
        for w, h in sprite_test_sizes:
            for bpp in (1, 4, 8, 12, 15, 16, 24, 32):
                sprite = factory.create_software_sprite((w, h), bpp)
                assert isinstance(sprite, sdl2ext.SoftwareSprite)
                assert SDL_GetError() == b""

        with pytest.raises(TypeError):
            factory.create_software_sprite(size=None)
        with pytest.raises(sdl2ext.SDLError):
            factory.create_software_sprite(size=(10, 10), bpp=-1)
        with pytest.raises(TypeError):
            factory.create_software_sprite(masks=5)
        with pytest.raises((ArgumentError, TypeError)):
            factory.create_software_sprite(
                size=(10, 10), masks=(None, None, None, None)
            )
        with pytest.raises((ArgumentError, TypeError)):
            factory.create_software_sprite(
                size=(10, 10), masks=("Test", 1, 2, 3)
            )

    def test_create_texture_sprite(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        factory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        for w, h in sprite_test_sizes:
            sprite = factory.create_texture_sprite(renderer, size=(w, h))
            assert isinstance(sprite, sdl2ext.TextureSprite)
            assert SDL_GetError() == b""
            del sprite

        # Test different access flags
        for flag in (
            SDL_TEXTUREACCESS_STATIC,
            SDL_TEXTUREACCESS_STREAMING,
            SDL_TEXTUREACCESS_TARGET
        ):
            sprite = factory.create_texture_sprite(
                renderer, size=(64, 64), access=flag
            )
            assert isinstance(sprite, sdl2ext.TextureSprite)
            assert SDL_GetError() == b""
            del sprite

    def test_from_image(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        tfactory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        sfactory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)

        for suffix in ("tif", "png", "jpg"):
            imgname = RESOURCES.get_path("surfacetest.%s" % suffix)
            tsprite = tfactory.from_image(imgname)
            assert isinstance(tsprite, sdl2ext.TextureSprite)
            ssprite = sfactory.from_image(imgname)
            assert isinstance(ssprite, sdl2ext.SoftwareSprite)

        if _HASPIL:
            from PIL import Image
            imgname = RESOURCES.get_path("surfacetest.png")
            img = Image.open(imgname)
            tsprite = tfactory.from_image(img)
            assert isinstance(tsprite, sdl2ext.TextureSprite)
            ssprite = sfactory.from_image(img)
            assert isinstance(ssprite, sdl2ext.SoftwareSprite)

        for factory in (tfactory, sfactory):
            with pytest.raises(ValueError):
                factory.from_image(None)
            with pytest.raises(ValueError):
                factory.from_image(12345)

    @pytest.mark.skip("not implemented")
    def test_from_object(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        tfactory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        sfactory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)

    def test_from_surface(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        tfactory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        sfactory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)

        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)
        tsprite = tfactory.from_surface(sf.contents)
        assert isinstance(tsprite, sdl2ext.TextureSprite)
        ssprite = sfactory.from_surface(sf.contents)
        assert isinstance(ssprite, sdl2ext.SoftwareSprite)
        SDL_FreeSurface(sf)

        for factory in (tfactory, sfactory):
            with pytest.raises((sdl2ext.SDLError, AttributeError, ArgumentError,
                               TypeError)):
                factory.from_surface(None)
            with pytest.raises((AttributeError, ArgumentError, TypeError)):
                factory.from_surface("test")

    def test_from_text(self, with_sdl):
        sfactory = sdl2ext.SpriteFactory(sdl2ext.SOFTWARE)
        fm = sdl2ext.FontManager(RESOURCES.get_path("tuffy.ttf"))

        # No Fontmanager passed
        with pytest.raises(KeyError):
            sfactory.from_text("Test")

        # Passing various keywords arguments
        sprite = sfactory.from_text("Test", fontmanager=fm)
        assert isinstance(sprite, sdl2ext.SoftwareSprite)

        sprite = sfactory.from_text("Test", fontmanager=fm, alias="tuffy")
        assert isinstance(sprite, sdl2ext.SoftwareSprite)

        # Get text from a texture sprite factory
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.Renderer(window)
        tfactory = sdl2ext.SpriteFactory(
            sdl2ext.TEXTURE, renderer=renderer, fontmanager=fm
        )
        sprite = tfactory.from_text("Test", alias="tuffy")
        assert isinstance(sprite, sdl2ext.TextureSprite)


class TestSpriteRenderSystem(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        renderer = sdl2ext.SpriteRenderSystem()
        assert isinstance(renderer, sdl2ext.SpriteRenderSystem)
        assert renderer.sortfunc is not None
        assert sdl2ext.Sprite in renderer.componenttypes

    def test_sortfunc(self, with_sdl):
        def func(p):
            pass

        renderer = sdl2ext.SpriteRenderSystem()
        assert renderer.sortfunc is not None
        renderer.sortfunc = func
        assert renderer.sortfunc == func

        def setf(x, f):
            x.sortfunc = f
        with pytest.raises(TypeError):
            setf(renderer, None)
        with pytest.raises(TypeError):
            setf(renderer, "Test")
        with pytest.raises(TypeError):
            setf(renderer, 1234)

    @pytest.mark.skip("not implemented")
    def test_render(self, with_sdl):
        pass

    @pytest.mark.skip("not implemented")
    def test_process(self, with_sdl):
        pass


class TestSoftwareSpriteRenderSystem(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        window = sdl2ext.Window("Test", size=(10, 10))
        renderer = sdl2ext.SoftwareSpriteRenderSystem(window)
        assert isinstance(renderer, sdl2ext.SpriteRenderSystem)
        assert renderer.window == window.window
        assert isinstance(renderer.surface, SDL_Surface)

        renderer = sdl2ext.SoftwareSpriteRenderSystem(window.window)
        assert isinstance(renderer, sdl2ext.SpriteRenderSystem)
        assert renderer.window == window.window
        assert isinstance(renderer.surface, SDL_Surface)

        assert renderer.sortfunc is not None
        assert not (sdl2ext.Sprite in renderer.componenttypes)
        assert sdl2ext.SoftwareSprite in renderer.componenttypes

        with pytest.raises(TypeError):
            sdl2ext.SoftwareSpriteRenderSystem()
        with pytest.raises(TypeError):
            sdl2ext.SoftwareSpriteRenderSystem(None)

    def test_render(self, with_sdl):
        # Create two software sprites for testing
        sf1 = SDL_CreateRGBSurface(0, 12, 7, 32, 0, 0, 0, 0)
        sp1 = sdl2ext.SoftwareSprite(sf1.contents, True)
        sdl2ext.fill(sp1, RED)
        sf2 = SDL_CreateRGBSurface(0, 3, 9, 32, 0, 0, 0, 0)
        sp2 = sdl2ext.SoftwareSprite(sf2.contents, True)
        sdl2ext.fill(sp2, BLUE)
        sprites = [sp1, sp2]

        # Create a window and renderer for the tests
        window = sdl2ext.Window("Test", size=(20, 20))
        renderer = sdl2ext.SoftwareSpriteRenderSystem(window)
        assert isinstance(renderer, sdl2ext.SpriteRenderSystem)
        sdl2ext.fill(renderer.surface, BLACK)

        # Test rendering a single sprite to different locations
        surf = renderer.surface
        for x, y in ((0, 0), (3, 3), (20, 20), (1, 12), (5, 6)):
            sp1.position = x, y
            renderer.render(sp1)
            check_pixels(surf, 20, 20, sp1, RED, [BLACK])
            sdl2ext.fill(surf, BLACK)
        
        # Test rendering multiple sprites in different positions
        sp1.position = 0, 0
        sp2.position = 14, 1
        renderer.render(sprites)
        check_pixels(surf, 20, 20, sp1, RED, [BLACK, BLUE])
        check_pixels(surf, 20, 20, sp2, BLUE, [BLACK, RED])
        sdl2ext.fill(surf, BLACK)

        # Test rendering multiple sprites with an x/y offset
        renderer.render(sprites, 1, 2)
        check_pixels(surf, 20, 20, sp1, RED, [BLACK, BLUE], 1, 2)
        check_pixels(surf, 20, 20, sp2, BLUE, [BLACK, RED], 1, 2)

    def test_process(self, with_sdl):
        # Create two software sprites for testing & give them depths
        sf1 = SDL_CreateRGBSurface(0, 5, 10, 32, 0, 0, 0, 0)
        sp1 = sdl2ext.SoftwareSprite(sf1.contents, True)
        sdl2ext.fill(sp1, RED)
        sf2 = SDL_CreateRGBSurface(0, 5, 10, 32, 0, 0, 0, 0)
        sp2 = sdl2ext.SoftwareSprite(sf2.contents, True)
        sdl2ext.fill(sp2, BLUE)
        sp1.depth = 0
        sp2.depth = 99
        sprites = [sp1, sp2]

        # Create a window and renderer for the tests
        window = sdl2ext.Window("Test", size=(20, 20))
        renderer = sdl2ext.SoftwareSpriteRenderSystem(window)
        assert isinstance(renderer, sdl2ext.SpriteRenderSystem)
        sdl2ext.fill(renderer.surface, BLACK)

        # Make sure only sp2 visible on surface, since its depth is higher
        renderer.process("fakeworld", sprites)
        check_pixels(renderer.surface, 20, 20, sp1, BLUE, [BLACK])
        check_pixels(renderer.surface, 20, 20, sp2, BLUE, [BLACK])


class TestTextureSpriteRenderSystem(object):
    __tags__ = ["sdl", "sdl2ext"]

    @pytest.mark.skip("not implemented")
    def test_init(self, with_sdl):
        pass

    @pytest.mark.skip("not implemented")
    def test_render(self, with_sdl):
        pass

    @pytest.mark.skip("not implemented")
    def test_process(self, with_sdl):
        pass
