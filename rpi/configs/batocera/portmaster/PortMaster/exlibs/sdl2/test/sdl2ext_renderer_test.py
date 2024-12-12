import gc
import sys
import pytest
from ctypes import addressof

from sdl2 import ext as sdl2ext
from sdl2 import dll
from sdl2.rect import SDL_Point, SDL_Rect
from sdl2.render import SDL_Renderer, SDL_Texture
from sdl2.surface import SDL_CreateRGBSurface, SDL_FreeSurface

# NOTE: These tests still have some legacy cruft to clean

def check_pixels(view, w, h, sprite, c1, c2, cx=0, cy=0):
    msg = "color mismatch at %d,%d: %d not in %s"
    cx = cx + sprite.x
    cy = cy + sprite.y
    cw, ch = sprite.size
    cmy = cy + ch
    cmx = cx + cw
    for y in range(w):
        for x in range(h):
            if cy <= y < cmy and cx <= x < cmx:
                assert view[y][x] == c1, msg % (x, y, view[y][x], c1)
            else:
                assert view[y][x] in c2, msg % (x, y, view[y][x], c2)

def check_areas(view, w, h, rects, c1, c2):
    def _inarea(x, y, rs):
        for r in rs:
            if (x >= r[0] and x < (r[0] + r[2]) and
                    y >= r[1] and y < (r[1] + r[3])):
                return True
        return False
    msg = "color mismatch at %d,%d: %d not in %s"
    for y in range(w):
        for x in range(h):
            if _inarea(x, y, rects):
                assert view[y][x] == c1, msg % (x, y, view[y][x], c1)
            else:
                assert view[y][x] in c2, msg % (x, y, view[y][x], c2)

def check_lines(view, w, h, points, c1, c2):
    def _online(x, y, pts):
        for p1, p2 in pts:
            if sdl2ext.point_on_line(p1, p2, (x, y)):
                return True
        return False
    msg = "color mismatch at %d,%d: %d not in %s"
    for y in range(w):
        for x in range(h):
            if _online(x, y, points):
                assert view[y][x] == c1, msg % (x, y, view[y][x], c1)
            else:
                assert view[y][x] in c2, msg % (x, y, view[y][x], c2)


class TestExtRenderer(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32, 0, 0, 0, 0)

        # Create renderer with SDL_Surface
        renderer = sdl2ext.Renderer(sf.contents)
        assert addressof(renderer.rendertarget) == addressof(sf.contents)
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Create renderer with SDL_Surface pointer
        renderer = sdl2ext.Renderer(sf)
        assert renderer.rendertarget == sf
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Create renderer with SoftwareSprite
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)
        renderer = sdl2ext.Renderer(sprite)
        assert renderer.rendertarget == sprite
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Create renderer with Window
        window = sdl2ext.Window("Test", size=(1, 1))
        renderer = sdl2ext.Renderer(window)
        assert renderer.rendertarget == window
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Create software renderer with Window
        renderer = sdl2ext.Renderer(window, backend='software')
        assert renderer.rendertarget == window
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Create renderer with SDL_Window
        sdlwindow = window.window
        renderer = sdl2ext.Renderer(sdlwindow)
        assert renderer.rendertarget == sdlwindow
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        renderer.destroy()

        # Test exception on invalid renderer backend
        with pytest.raises(RuntimeError):
            sdl2ext.Renderer(window, backend='QuickDraw3D')
        with pytest.raises(sdl2ext.SDLError):
            sdl2ext.Renderer(window, backend=100)
        del window

        # Test exception on using a destroyed renderer (and random type errors)
        with pytest.raises(RuntimeError):
            tst = renderer.sdlrenderer
        with pytest.raises(TypeError):
            sdl2ext.Renderer(None)
        with pytest.raises(TypeError):
            sdl2ext.Renderer(1234)
        with pytest.raises(TypeError):
            sdl2ext.Renderer("test")

    def test_logical_size(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 150, 50, 32, 0, 0, 0, 0)
        window = sdl2ext.Window("Test", size=(150, 50))
        sprite = sdl2ext.SoftwareSprite(sf.contents, True)

        # Test initializing with custom logical size
        renderer = sdl2ext.Renderer(window, logical_size=(200, 200))
        assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
        assert renderer.logical_size == (200, 200)
        renderer.reset_logical_size()
        assert renderer.logical_size == (150, 50)
        renderer.destroy()

        # Test changing and resetting logical size with different target types
        targets = {
            "SDL_Surface": sf.contents,
            "SDL_Surface_pointer": sf,
            "SoftwareSprite": sprite,
            "Window": window,
            "SDL_Window": window.window
        }
        for name, target in targets.items():
            target_name = name
            renderer = sdl2ext.Renderer(target)
            assert isinstance(renderer.sdlrenderer.contents, SDL_Renderer)
            assert renderer.logical_size == (150, 50)
            renderer.logical_size = (200, 100)
            assert renderer.logical_size == (200, 100)
            renderer.reset_logical_size()
            assert renderer.logical_size == (150, 50)
            renderer.destroy()

        window.close()
        
    def test_color(self, with_sdl):
        sf = SDL_CreateRGBSurface(
            0, 10, 10, 32, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF
        )
        renderer = sdl2ext.Renderer(sf.contents)
        assert isinstance(renderer.color, sdl2ext.Color)
        assert renderer.color == sdl2ext.Color(0, 0, 0, 0)
        renderer.color = 0x00FF0000
        assert renderer.color == sdl2ext.Color(0xFF, 0, 0, 0)
        renderer.clear()
        view = sdl2ext.PixelView(sf.contents)
        check_areas(view, 10, 10, [[0, 0, 10, 10]], 0xFF000000, (0x0,))
        del view
        renderer.color = 0xAABBCCDD
        assert renderer.color == sdl2ext.Color(0xBB, 0xCC, 0xDD, 0xAA)
        renderer.clear()
        view = sdl2ext.PixelView(sf.contents)
        check_areas(view, 10, 10, [[0, 0, 10, 10]], 0xBBCCDDAA, (0x0,))
        del view
        renderer.destroy()
        SDL_FreeSurface(sf)

    @pytest.mark.skip("not implemented")
    def test_blendmode(self, with_sdl):
        pass

    @pytest.mark.skip("not implemented")
    def test_scale(self, with_sdl):
        pass

    def test_clear(self, with_sdl):
        sf = SDL_CreateRGBSurface(0, 10, 10, 32,
                                  0xFF000000,
                                  0x00FF0000,
                                  0x0000FF00,
                                  0x000000FF)
        renderer = sdl2ext.Renderer(sf.contents)
        assert isinstance(renderer.color, sdl2ext.Color)
        assert renderer.color == sdl2ext.Color(0, 0, 0, 0)
        renderer.color = 0x00FF0000
        assert renderer.color == sdl2ext.Color(0xFF, 0, 0, 0)
        renderer.clear()
        view = sdl2ext.PixelView(sf.contents)
        check_areas(view, 10, 10, [[0, 0, 10, 10]], 0xFF000000, (0x0,))
        del view
        renderer.clear(0xAABBCCDD)
        assert renderer.color == sdl2ext.Color(0xFF, 0, 0, 0)
        view = sdl2ext.PixelView(sf.contents)
        check_areas(view, 10, 10, [[0, 0, 10, 10]], 0xBBCCDDAA, (0x0,))
        del view
        renderer.destroy()
        SDL_FreeSurface(sf)

    def test_copy(self, with_sdl):
        # Initialize target surface and renderer
        surface = SDL_CreateRGBSurface(0, 128, 128, 32, 0, 0, 0, 0).contents
        renderer = sdl2ext.Renderer(surface)
        renderer.clear(0xAABBCC)
        view = sdl2ext.PixelView(surface)

        # Test copying a Texture without any arguments (should fill surface)
        sf = SDL_CreateRGBSurface(0, 16, 16, 32, 0, 0, 0, 0)
        sdl2ext.fill(sf, (0, 0, 0, 0))
        tx = sdl2ext.Texture(renderer, sf)
        renderer.copy(tx)
        renderer.present()
        assert view[0][0] == 0
        assert view[127][127] == 0

        # Test copying a Texture with only location argument
        renderer.clear(0xAABBCC) # reset surface
        renderer.copy(tx, dstrect=(10, 10))
        renderer.present()
        assert view[0][0] == 0xAABBCC
        assert view[10][10] == 0
        assert view[25][25] == 0
        assert view[26][26] == 0xAABBCC

        # Test copying a subset of a Texture
        renderer.clear(0xAABBCC) # reset surface
        renderer.copy(tx, srcrect=(0, 0, 10, 10), dstrect=(10, 10))
        renderer.present()
        assert view[0][0] == 0xAABBCC
        assert view[10][10] == 0
        assert view[19][19] == 0
        assert view[20][20] == 0xAABBCC

        # Test copying a subset of a Texture w/ point/rect args
        renderer.clear(0xAABBCC) # reset surface
        renderer.copy(tx, srcrect=SDL_Rect(0, 0, 10, 10), dstrect=SDL_Point(10, 10))
        renderer.present()
        assert view[0][0] == 0xAABBCC
        assert view[10][10] == 0
        assert view[19][19] == 0
        assert view[20][20] == 0xAABBCC

        # Test copying a Texture with location and size
        renderer.clear(0xAABBCC) # reset surface
        renderer.copy(tx, dstrect=(10, 10, 30, 40))
        renderer.present()
        assert view[0][0] == 0xAABBCC
        assert view[10][10] == 0
        assert view[49][39] == 0
        assert view[50][40] == 0xAABBCC

        if dll.version > 2005:
            # Test copying a Texture with rotation
            renderer.clear(0xAABBCC) # reset surface
            renderer.copy(tx, dstrect=(32, 32), angle=180, center=(0, 0))
            renderer.present()
            assert view[0][0] == 0xAABBCC
            assert view[16][16] == 0xFF000000  # Rotation suddenly adds alpha?
            assert view[31][31] == 0xFF000000  # Rotation suddenly adds alpha?
            assert view[32][32] == 0xAABBCC

        # (legacy): Test copying texture from a SpriteFactory
        renderer.clear(0)  # reset surface
        factory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        w, h = 32, 32
        sp = factory.from_color(0xFF0000, (w, h))
        sp.x, sp.y = 40, 50
        renderer.copy(sp, (0, 0, w, h), (sp.x, sp.y, w, h))
        check_pixels(view, 128, 128, sp, 0xFF0000, (0x0,))

        del view

    def test_draw_line(self, with_sdl):
        surface = SDL_CreateRGBSurface(0, 128, 128, 32, 0, 0, 0, 0).contents
        sdl2ext.fill(surface, 0x0)
        renderer = sdl2ext.Renderer(surface)
        renderer.draw_line((20, 10, 20, 86), 0x0000FF)
        view = sdl2ext.PixelView(surface)
        check_lines(view, 128, 128,
                         [((20, 10), (20, 86))], 0x0000FF, (0x0,))
        del view

    def test_draw_point(self, with_sdl):
        # Initialize target surface and renderer
        surface = SDL_CreateRGBSurface(0, 128, 128, 32, 0, 0, 0, 0).contents
        sdl2ext.fill(surface, 0x0)
        renderer = sdl2ext.Renderer(surface)

        # Try drawing a single point
        renderer.draw_point((1, 1), 0x0000FF)
        view = sdl2ext.PixelView(surface)
        assert view[1][1] == 0x0000FF

        # Try drawing a single SDL_Point
        renderer.draw_point(SDL_Point(3, 3), 0x0000FF)
        assert view[3][3] == 0x0000FF

        # Try drawing multiple points
        renderer.draw_point([(8, 8), SDL_Point(5, 5)], 0x0000FF)
        assert view[5][5] == 0x0000FF
        assert view[8][8] == 0x0000FF

        # Try subpixel rendering (if supported)
        if dll.version >= 2010:
            assert view[6][6] == 0x0
            renderer.draw_point((6.5, 6.5), 0x0000FF)
            assert view[6][6] != 0x0
        else:
            with pytest.raises(RuntimeError):
               renderer.draw_point((6.5, 6.5), 0x0000FF) 
        del view

        # Test exceptions on bad input
        with pytest.raises(ValueError):
            renderer.draw_point((0, 0, 2), 0x0000FF)
        with pytest.raises(ValueError):
            renderer.draw_point([(0, 0), (1, 2, 3)], 0x0000FF)
        
    def test_draw_rect(self, with_sdl):
        surface = SDL_CreateRGBSurface(0, 128, 128, 32, 0, 0, 0, 0).contents
        sdl2ext.fill(surface, 0x0)
        renderer = sdl2ext.Renderer(surface)
        renderer.draw_rect((40, 50, 32, 32), 0x0000FF)
        view = sdl2ext.PixelView(surface)
        check_lines(view, 128, 128, [
            ((40, 50), (71, 50)),
            ((40, 50), (40, 81)),
            ((40, 81), (71, 81)),
            ((71, 50), (71, 81))], 0x0000FF, (0x0,))
        del view
        sdl2ext.fill(surface, 0x0)
        renderer.draw_rect([(5, 5, 10, 10), (20, 15, 8, 10)], 0x0000FF)
        view = sdl2ext.PixelView(surface)
        check_lines(view, 128, 128, [
            ((5, 5), (14, 5)),
            ((5, 5), (5, 14)),
            ((5, 14), (14, 14)),
            ((14, 5), (14, 14)),
            ((20, 15), (27, 15)),
            ((20, 15), (20, 24)),
            ((20, 24), (27, 24)),
            ((27, 15), (27, 24))], 0x0000FF, (0x0,))
        del view

    def test_fill(self, with_sdl):
        surface = SDL_CreateRGBSurface(0, 128, 128, 32, 0, 0, 0, 0).contents
        sdl2ext.fill(surface, 0x0)
        renderer = sdl2ext.Renderer(surface)
        factory = sdl2ext.SpriteFactory(sdl2ext.TEXTURE, renderer=renderer)
        w, h = 32, 32
        sp = factory.from_color(0xFF0000, (w, h))
        sp.x, sp.y = 40, 50
        renderer.fill((sp.x, sp.y, w, h), 0x0000FF)
        view = sdl2ext.PixelView(surface)
        check_pixels(view, 128, 128, sp, 0x0000FF, (0x0,))
        del view

        sdl2ext.fill(surface, 0x0)
        renderer.fill([(5, 5, 10, 10), (20, 15, 8, 10)], 0x0000FF)
        view = sdl2ext.PixelView(surface)
        check_areas(view, 128, 128, [(5, 5, 10, 10), (20, 15, 8, 10)],
                         0x0000FF, (0x0,))
        del view


class TestExtTexture(object):
    __tags__ = ["sdl", "sdl2ext"]

    def test_init_destroy(self):
        # Create renderer and test surface
        rendertarget = SDL_CreateRGBSurface(0, 100, 100, 32, 0, 0, 0, 0)
        renderer = sdl2ext.Renderer(rendertarget.contents)
        sf = SDL_CreateRGBSurface(
            0, 16, 16, 32, 0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF
        )

        # Test creation with surface pointer
        tx = sdl2ext.Texture(renderer, sf)
        assert isinstance(tx.tx.contents, SDL_Texture)

        # Test destruction and associated behaviour
        tx.destroy()
        with pytest.raises(RuntimeError):
            sdl_tx = tx.tx

        # Test creation with surface contents
        tx = sdl2ext.Texture(renderer, sf.contents)
        assert isinstance(tx.tx.contents, SDL_Texture)
        
        # Test texture size
        assert tx.size == (16, 16)

        # Test exception on bad input
        with pytest.raises(TypeError):
            sdl2ext.Texture(sf, sf)
        with pytest.raises(TypeError):
            sdl2ext.Texture(renderer, renderer)

        # Test exception when accessing Texture with destroyed Renderer
        renderer.destroy()
        with pytest.raises(RuntimeError):
            sdl_tx = tx.tx
        tx.destroy()  # Ensure texture destruction method doesn't error
        SDL_FreeSurface(sf)

    @pytest.mark.skip("not implemented")
    def test_size(self, with_sdl):
        pass

    @pytest.mark.skip("not implemented")
    def test_scale_mode(self, with_sdl):
        pass


@pytest.mark.skip("not implemented")
def test_set_texture_scale_quality(with_sdl):
    pass
