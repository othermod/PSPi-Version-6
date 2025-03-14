import sys
import pytest
import sdl2

_HASMP = True
try:
    import multiprocessing
except:
    _HASMP = False


def test_SDL_GetCPUCacheLineSize():
    ret = sdl2.SDL_GetCPUCacheLineSize()
    assert isinstance(ret, int)

def test_SDL_GetCPUCount():
    if _HASMP:
        assert multiprocessing.cpu_count() == sdl2.SDL_GetCPUCount()
    else:
        assert sdl2.SDL_GetCPUCount() >= 1

def test_SDL_Has3DNow():
    ret = sdl2.SDL_Has3DNow()
    assert ret in (0, 1)

def test_SDL_HasAltiVec():
    ret = sdl2.SDL_HasAltiVec()
    assert ret in (0, 1)

def test_SDL_HasMMX():
    ret = sdl2.SDL_HasMMX()
    assert ret in (0, 1)

def test_SDL_HasRDTSC():
    ret = sdl2.SDL_HasRDTSC()
    assert ret in (0, 1)

def test_SDL_HasSSE():
    ret = sdl2.SDL_HasSSE()
    assert ret in (0, 1)

def test_SDL_HasSSE2():
    ret = sdl2.SDL_HasSSE2()
    assert ret in (0, 1)

def test_SDL_HasSSE3():
    ret = sdl2.SDL_HasSSE3()
    assert ret in (0, 1)

def test_SDL_HasSSE41():
    ret = sdl2.SDL_HasSSE41()
    assert ret in (0, 1)

def test_SDL_HasSSE42():
    ret = sdl2.SDL_HasSSE42()
    assert ret in (0, 1)

def test_SDL_HasAVX():
    ret = sdl2.SDL_HasAVX()
    assert ret in (0, 1)

def test_SDL_HasAVX2():
    ret = sdl2.SDL_HasAVX2()
    assert ret in (0, 1)

def test_SDL_GetSystemRAM():
    ret = sdl2.SDL_GetSystemRAM()
    assert ret > 0

@pytest.mark.skipif(sdl2.dll.version < 2009, reason="not available")
def test_SDL_HasAVX512F():
    ret = sdl2.SDL_HasAVX512F()
    assert ret in (0, 1)

@pytest.mark.skipif(sdl2.dll.version < 2012, reason="not available")
def test_SDL_HasARMSIMD():
    ret = sdl2.SDL_HasARMSIMD()
    assert ret in (0, 1)

@pytest.mark.skipif(sdl2.dll.version < 2006, reason="not available")
def test_SDL_HasNEON():
    ret = sdl2.SDL_HasNEON()
    assert ret in (0, 1)

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_HasLSX():
    ret = sdl2.SDL_HasLSX()
    assert ret in (0, 1)

@pytest.mark.skipif(sdl2.dll.version < 2231, reason="not available")
def test_SDL_HasLASX():
    ret = sdl2.SDL_HasLASX()
    assert ret in (0, 1)

@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_SIMDGetAlignment():
    ret = sdl2.SDL_SIMDGetAlignment()
    assert ret % 8 == 0 # Should be multiple of 8

@pytest.mark.skip("not implemented (no clue how)")
@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
def test_SDL_SIMDAllocFree():
    # Should test both SDL_SIMDAlloc and SDL_SIMDFree
    pass

@pytest.mark.skip("not implemented (no clue how)")
@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_SIMDRealloc():
    pass
