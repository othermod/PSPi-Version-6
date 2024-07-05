import sys
import gc
import pytest
from ctypes import POINTER, byref, addressof

from sdl2 import ext as sdl2ext
from sdl2.render import (
    SDL_Renderer, SDL_CreateWindowAndRenderer, SDL_DestroyRenderer,
    SDL_Texture, SDL_CreateTexture
)
from sdl2.surface import SDL_CreateRGBSurface
from sdl2.video import SDL_Window, SDL_WINDOW_HIDDEN, SDL_DestroyWindow


class MSprite(sdl2ext.Sprite):

    def __init__(self, w=0, h=0):
        super(MSprite, self).__init__()
        self._size = w, h

    @property
    def size(self):
        return self._size


@pytest.fixture
def positions():
    test_positions = []
    for x in range(-50, 50, 5):
        for y in range(-50, 50, 5):
            test_positions.append((x, y))
    return test_positions

@pytest.fixture
def sizes():
    test_sizes = [(4, 4)]
    for w in range(16, 256, 16):
        for h in range(16, 256, 16):
            test_sizes.append((w, h))
    return test_sizes


class TestExtSprite(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self):
        sprite = MSprite()
        assert isinstance(sprite, MSprite)
        assert isinstance(sprite, sdl2ext.Sprite)

    def test_position_xy(self, positions):
        sprite = MSprite()
        for x, y in positions:
            sprite.position = x, y
            assert sprite.position == (x, y)
            sprite.x = x + 1
            sprite.y = y + 1
            assert sprite.position == (x + 1, y + 1)

    def test_area(self, sizes):
        for w, h in sizes:
            sprite = MSprite(w, h)
            assert sprite.size == (w, h)
            assert sprite.area == (0, 0, w, h)
            sprite.position = w, h
            assert sprite.area == (w, h, 2 * w, 2 * h)


class TestExtSoftwareSprite(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)

        # Test with SDL_Surface
        sprite = sdl2ext.SoftwareSprite(sf.contents, False)
        assert addressof(sprite.surface) == addressof(sf.contents)
        assert not sprite.free

        # Test with SDL_Surface pointer
        sprite = sdl2ext.SoftwareSprite(sf, False)
        assert addressof(sprite.surface) == addressof(sf.contents)
        assert not sprite.free

        with pytest.raises(TypeError):
            sdl2ext.SoftwareSprite(None, True)

    def test___repr__(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)
        assert repr(sprite) == "SoftwareSprite(size=(10, 10), bpp=32)"

    def test_position_xy(self, with_sdl, positions):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)
        assert isinstance(sprite, sdl2ext.SoftwareSprite)
        assert sprite.position == (0, 0)
        for x, y in positions:
            sprite.position = x, y
            assert sprite.position == (x, y)
            sprite.x = x + 1
            sprite.y = y + 1
            assert sprite.position == (x + 1, y + 1)

    def test_size(self, with_sdl, sizes):
        for w, h in sizes:
            sf = SDL_CreateRGBSurface(0, w, h, 32, 0, 0, 0, 0)
            sprite = sdl2ext.SoftwareSprite(sf.contents, True)
            assert isinstance(sprite, sdl2ext.SoftwareSprite)
            assert sprite.size == (w, h)

    def test_area(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)
        assert sprite.area == (0, 0, 10, 10)
        sprite.position = 7, 3
        assert sprite.area == (7, 3, 17, 13)
        sprite.position = -22, 99
        assert sprite.area == (-22, 99, -12, 109)
        def setarea(s, v):
            s.area = v
        with pytest.raises(AttributeError):
            setarea(sprite, (1, 2, 3, 4))


class TestExtTextureSprite(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        window = POINTER(SDL_Window)()
        renderer = POINTER(SDL_Renderer)()
        SDL_CreateWindowAndRenderer(
            10, 10, SDL_WINDOW_HIDDEN, byref(window), byref(renderer)
        )
        tex = SDL_CreateTexture(renderer, 0, 0, 10, 10)
        assert isinstance(tex.contents, SDL_Texture)
        sprite = sdl2ext.TextureSprite(tex.contents)
        assert isinstance(sprite, sdl2ext.TextureSprite)
        SDL_DestroyRenderer(renderer)
        SDL_DestroyWindow(window)

    def test_position_xy(self, with_sdl, positions):
        window = POINTER(SDL_Window)()
        renderer = POINTER(SDL_Renderer)()
        SDL_CreateWindowAndRenderer(
            10, 10, SDL_WINDOW_HIDDEN, byref(window), byref(renderer)
        )
        tex = SDL_CreateTexture(renderer, 0, 0, 10, 10)
        assert isinstance(tex.contents, SDL_Texture)
        sprite = sdl2ext.TextureSprite(tex.contents)
        assert isinstance(sprite, sdl2ext.TextureSprite)
        assert sprite.position == (0, 0)
        for x, y in positions:
            sprite.position = x, y
            assert sprite.position == (x, y)
            sprite.x = x + 1
            sprite.y = y + 1
            assert sprite.position == (x + 1, y + 1)
        SDL_DestroyRenderer(renderer)
        SDL_DestroyWindow(window)

    def test_size(self, with_sdl, sizes):
        window = POINTER(SDL_Window)()
        renderer = POINTER(SDL_Renderer)()
        SDL_CreateWindowAndRenderer(
            10, 10, SDL_WINDOW_HIDDEN, byref(window), byref(renderer)
        )
        for w, h in sizes:
            tex = SDL_CreateTexture(renderer, 0, 0, w, h)
            assert isinstance(tex.contents, SDL_Texture)
            sprite = sdl2ext.TextureSprite(tex.contents)
            assert isinstance(sprite, sdl2ext.TextureSprite)
            assert sprite.size == (w, h)
            del sprite
        SDL_DestroyRenderer(renderer)
        SDL_DestroyWindow(window)

    def test_area(self, with_sdl):
        window = POINTER(SDL_Window)()
        renderer = POINTER(SDL_Renderer)()
        SDL_CreateWindowAndRenderer(
            10, 10, SDL_WINDOW_HIDDEN, byref(window), byref(renderer)
        )
        tex = SDL_CreateTexture(renderer, 0, 0, 10, 20)
        assert isinstance(tex.contents, SDL_Texture)
        sprite = sdl2ext.TextureSprite(tex.contents)
        assert isinstance(sprite, sdl2ext.TextureSprite)
        assert sprite.area == (0, 0, 10, 20)
        sprite.position = 7, 3
        assert sprite.area == (7, 3, 17, 23)
        sprite.position = -22, 99
        assert sprite.area == (-22, 99, -12, 119)
        def setarea(s, v):
            s.area = v
        with pytest.raises(AttributeError):
            setarea(sprite, (1, 2, 3, 4))
        SDL_DestroyRenderer(renderer)
        SDL_DestroyWindow(window)
