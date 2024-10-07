import sys
import pytest
import sdl2
from sdl2 import (
    SDL_INIT_TIMER, SDL_INIT_AUDIO, SDL_INIT_VIDEO, SDL_INIT_JOYSTICK, SDL_INIT_HAPTIC,
    SDL_INIT_GAMECONTROLLER, SDL_INIT_EVENTS, SDL_INIT_SENSOR, SDL_INIT_EVERYTHING
)

subsystems = {
    'timer': SDL_INIT_TIMER,
    'audio': SDL_INIT_AUDIO,
    'video': SDL_INIT_VIDEO,
    'joystick': SDL_INIT_JOYSTICK,
    'haptic': SDL_INIT_HAPTIC,
    'gamecontroller': SDL_INIT_GAMECONTROLLER,
    'events': SDL_INIT_EVENTS,
    'sensor': SDL_INIT_SENSOR,
}


def test_SDL_Init():
    supported = []
    sdl2.SDL_ClearError()
    for name, flags in subsystems.items():
        ret = sdl2.SDL_Init(flags)
        err = sdl2.SDL_GetError()
        if name in ['timer', 'audio', 'video', 'events']:
            assert ret == 0
        if err:
            err = err.decode('utf-8')
            print("Error loading {0} subsystem: {1}".format(name, err))
            sdl2.SDL_ClearError()
        else:
            if ret == 0 and sdl2.SDL_WasInit(0) & flags == flags:
                supported.append(name)
        sdl2.SDL_Quit()
    print("Supported SDL2 subsystems:")
    print(supported)

def test_SDL_InitSubSystem():
    sdl2.SDL_ClearError()
    ret = sdl2.SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO)
    assert sdl2.SDL_GetError() == b""
    assert ret == 0
    # Test initializing an additional subsystem
    assert sdl2.SDL_WasInit(0) & SDL_INIT_TIMER != SDL_INIT_TIMER
    ret = sdl2.SDL_InitSubSystem(SDL_INIT_TIMER)
    assert sdl2.SDL_GetError() == b""
    assert sdl2.SDL_WasInit(0) & SDL_INIT_TIMER == SDL_INIT_TIMER
    # Test shutting down a single subsystem
    sdl2.SDL_QuitSubSystem(SDL_INIT_AUDIO)
    assert sdl2.SDL_WasInit(0) & SDL_INIT_AUDIO != SDL_INIT_AUDIO
    remaining = SDL_INIT_VIDEO | SDL_INIT_TIMER
    assert sdl2.SDL_WasInit(remaining) == remaining
    # Shut down all subsystems once complete
    sdl2.SDL_Quit()
    assert sdl2.SDL_WasInit(0) == 0

def test_SDL_INIT_EVERYTHING():
    # Make sure all the other flags are in the everything flag
    for name, flags in subsystems.items():
        assert sdl2.SDL_INIT_EVERYTHING & flags == flags
