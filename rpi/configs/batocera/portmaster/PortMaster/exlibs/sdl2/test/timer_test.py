import sys
import time
import pytest
import sdl2

if sys.version_info[0] >= 3:
    long = int


def test_SDL_TICKS_PASSED(with_sdl):
    for A in (0, 9999, 0xFFFF0000, 0xFFFFFFFF):
        assert sdl2.SDL_TICKS_PASSED(A, A)
        for delta in (1, 100, 1000000, 0x7FFFFFFF):
            assert sdl2.SDL_TICKS_PASSED(A, (A - delta) & 0xFFFFFFFF)
            assert not sdl2.SDL_TICKS_PASSED(A, (A + delta) & 0xFFFFFFFF)

def test_SDL_GetTicks(with_sdl):
    ticks = sdl2.SDL_GetTicks()
    time.sleep(0.05)
    ticks2 = sdl2.SDL_GetTicks()
    time.sleep(0.05)
    ticks3 = sdl2.SDL_GetTicks()
    assert ticks2 > ticks
    assert ticks3 > ticks2

@pytest.mark.skipif(sdl2.dll.version < 2018, reason="not available")
def test_SDL_GetTicks64(with_sdl):
    ticks = sdl2.SDL_GetTicks64()
    time.sleep(0.05)
    ticks2 = sdl2.SDL_GetTicks64()
    time.sleep(0.05)
    ticks3 = sdl2.SDL_GetTicks64()
    assert ticks2 > ticks
    assert ticks3 > ticks2

def test_SDL_GetPerformanceCounter(with_sdl):
    perf = sdl2.SDL_GetPerformanceCounter()
    assert type(perf) in (int, long)
    assert perf > 0

def test_SDL_GetPerformanceFrequency(with_sdl):
    freq = sdl2.SDL_GetPerformanceFrequency()
    assert type(freq) in (int, long)
    assert freq > 0

@pytest.mark.xfail(reason="Unreliable on CI runners")
def test_SDL_Delay(with_sdl):
    for wait in [5, 10, 50, 100]:
        start = sdl2.SDL_GetTicks()
        sdl2.SDL_Delay(wait)
        end = sdl2.SDL_GetTicks()
        actual = (end - start)
        assert (wait - 2) <= actual <= (wait + 2)
                
@pytest.mark.skipif(hasattr(sys, "pypy_version_info"),
    reason="PyPy can't access other vars properly from a separate thread")
@pytest.mark.xfail(reason="Unreliable on CI runners")
def test_SDL_AddRemoveTimer(with_sdl):
    # Create a timer callback that adds a value to a Python list
    calls = []
    def timerfunc(interval, param):
        calls.append(param)
        return interval
    callback = sdl2.SDL_TimerCallback(timerfunc)
    timerid = sdl2.SDL_AddTimer(50, callback, "Test")
    # Run a loop for 300 ms and make sure the callback runs 5 or 6 times
    start = sdl2.SDL_GetTicks()
    while (sdl2.SDL_GetTicks() - start) <= 300:
        sdl2.SDL_Delay(10)
    assert len(calls) in [5, 6]
    # Try removing the timer and make sure the callback doesn't run anymore
    sdl2.SDL_RemoveTimer(timerid)
    sdl2.SDL_Delay(10)
    orig_calls = len(calls)
    start = sdl2.SDL_GetTicks()
    while (sdl2.SDL_GetTicks() - start) <= 200:
        sdl2.SDL_Delay(10)
    assert len(calls) == orig_calls
    # Wait a bit, so the last executing handlers can finish
    sdl2.SDL_Delay(10)
