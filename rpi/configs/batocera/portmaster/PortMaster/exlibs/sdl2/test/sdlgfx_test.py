import os
import sys
from ctypes import c_int, byref
import pytest
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_INIT_VIDEO
from sdl2 import surface, render

sdlgfx = pytest.importorskip("sdl2.sdlgfx")



@pytest.fixture(scope="module")
def with_sdl():
    if SDL_Init(SDL_INIT_VIDEO) != 0:
        raise RuntimeError("Video subsystem not supported")
    yield
    SDL_Quit()

@pytest.fixture
def test_surf(with_sdl):
    w, h = 480, 320
    sf = surface.SDL_CreateRGBSurface(0, w, h, 32, 0, 0, 0, 0)
    assert isinstance(sf.contents, surface.SDL_Surface)
    yield sf
    surface.SDL_FreeSurface(sf)

@pytest.fixture
def software_renderer(with_sdl):
    height, width = (480, 320)
    sdl2.SDL_ClearError()
    # Create a new SDL surface and make it the target of a new renderer
    target = surface.SDL_CreateRGBSurface(0, height, width, 32, 0, 0, 0, 0)
    assert sdl2.SDL_GetError() == b""
    renderer = render.SDL_CreateSoftwareRenderer(target)
    assert sdl2.SDL_GetError() == b""
    # Return the renderer and surface for the test
    yield (renderer, target)
    # Free memory for the renderer and surface once we're done
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_FreeSurface(target)

RED_U32 = 0xFF0000FF
WHITE_U32 = 0xFFFFFFFF


class TestFramerate(object):
    __tags__ = ["sdl", "sdlgfx"]

    def test_SDL_initFramerate(self):
        manager = sdlgfx.FPSManager()
        sdlgfx.SDL_initFramerate(manager)
        assert manager.framecount == 0
        assert manager.rate == sdlgfx.FPS_DEFAULT

    def test_SDL_getsetFramerate(self):
        manager = sdlgfx.FPSManager()
        sdlgfx.SDL_initFramerate(manager)
        ret = sdlgfx.SDL_setFramerate(manager, 24)
        fps = sdlgfx.SDL_getFramerate(manager)
        assert ret == 0
        assert manager.rate == 24
        assert fps == 24

    def test_SDL_getFramecount(self):
        manager = sdlgfx.FPSManager()
        sdlgfx.SDL_initFramerate(manager)
        assert sdlgfx.SDL_getFramecount(manager) == 0
        sdlgfx.SDL_framerateDelay(manager)
        assert sdlgfx.SDL_getFramecount(manager) == 1

    @pytest.mark.xfail(reason="Timing can be super wonky on CI platforms")
    def test_SDL_framerateDelay(self):
        manager = sdlgfx.FPSManager()
        sdlgfx.SDL_initFramerate(manager)
        ret = sdlgfx.SDL_setFramerate(manager, 100)
        assert ret == 0
        sdlgfx.SDL_framerateDelay(manager)
        assert manager.framecount == 1
        frametimes = []
        for i in range(10):
            msec_since_last = sdlgfx.SDL_framerateDelay(manager)
            frametimes.append(msec_since_last)
        avg_framerate = round(sum(frametimes) / 10)
        assert abs(avg_framerate - 10) < 2
        assert manager.framecount == 11


class TestDrawing(object):
    __tags__ = ["sdl", "sdlgfx"]

    def test_pixel(self, software_renderer):
        renderer, sf = software_renderer
        ret = sdlgfx.pixelColor(renderer, 5, 5, RED_U32)
        assert ret == 0
        ret = sdlgfx.pixelRGBA(renderer, 5, 5, 255, 255, 255, 255)
        assert ret == 0

    @pytest.mark.skip("not implemented")
    def test_hline(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_vline(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_rectangle(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_roundedRectangle(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_box(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_roundedBox(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_line(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_aaline(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_thickLine(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_circle(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_arc(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_aacircle(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_filledCircle(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_ellipse(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_aaellipse(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_filledEllipse(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_pie(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_filledPie(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_trigon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_aatrigon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_filledTrigon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_polygon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_aapolygon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_filledPolygon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_texturedPolygon(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_bezier(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_gfxPrimitivesSetFont(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_gfxPrimitivesSetFontRotation(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_character(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_string(self):
        pass


class TestRotoZoom(object):
    __tags__ = ["sdl", "sdlgfx"]

    @pytest.mark.skip("not implemented")
    def test_rotozoomSurface(self, test_surf):
        pass

    @pytest.mark.skip("not implemented")
    def test_rotozoomSurfaceXY(self, test_surf):
        pass

    @pytest.mark.skip("not implemented")
    def test_rotozoomSurfaceSize(self, test_surf):
        pass

    @pytest.mark.skip("not implemented")
    def test_rotozoomSurfaceSizeXY(self, test_surf):
        pass

    def test_zoomSurface(self, test_surf):
        zoom_sf = sdlgfx.zoomSurface(test_surf, 1.5, 2.0, 0)
        assert isinstance(zoom_sf.contents, surface.SDL_Surface)
        assert zoom_sf.contents.w == test_surf.contents.w * 1.5
        assert zoom_sf.contents.h == test_surf.contents.h * 2.0
        surface.SDL_FreeSurface(zoom_sf)

    def test_zoomSurfaceSize(self, test_surf):
        out_w, out_h = (c_int(0), c_int(0))
        w, h = (test_surf.contents.w, test_surf.contents.h)
        sdlgfx.zoomSurfaceSize(w, h, 1.5, 2.0, byref(out_w), byref(out_h))
        assert out_w.value == w * 1.5
        assert out_h.value == h * 2.0

    def test_shrinkSurface(self, test_surf):
        shrunk_sf = sdlgfx.shrinkSurface(test_surf, 3, 2)
        assert isinstance(shrunk_sf.contents, surface.SDL_Surface)
        assert shrunk_sf.contents.w == test_surf.contents.w / 3
        assert shrunk_sf.contents.h == test_surf.contents.h / 2
        surface.SDL_FreeSurface(shrunk_sf)

    def test_rotateSurface90Degrees(self, test_surf):
        rotsf = sdlgfx.rotateSurface90Degrees(test_surf, 1)
        assert isinstance(rotsf.contents, surface.SDL_Surface)
        assert rotsf.contents.w == test_surf.contents.h
        assert rotsf.contents.h == test_surf.contents.w
        surface.SDL_FreeSurface(rotsf)
