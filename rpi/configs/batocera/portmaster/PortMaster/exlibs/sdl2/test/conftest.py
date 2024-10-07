# pytest configuration file
import os
import gc
import pytest
import sdl2
from sdl2 import ext as sdl2ext

# A flag to skip annoying audiovisual tests (e.g. window minimize).
# Defaults to True unless an environment variable is explicitly set.
SKIP_ANNOYING = os.getenv("PYSDL2_ALL_TESTS", "0") == "0"

@pytest.fixture(scope="module")
def with_sdl():
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_TIMER)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    yield
    sdl2.SDL_Quit()

@pytest.fixture(autouse=True)
def sdl_cleanup():
    sdl2.SDL_ClearError()
    yield
    sdl2.SDL_ClearError()
    gc.collect()
