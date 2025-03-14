import sys
import os
import pytest
from ctypes import c_int, byref
import sdl2


def test_SDL_GetPowerInfo():
    has_battery = [
        sdl2.SDL_POWERSTATE_ON_BATTERY,
        sdl2.SDL_POWERSTATE_CHARGING,
        sdl2.SDL_POWERSTATE_CHARGED
    ]
    no_battery = [
        sdl2.SDL_POWERSTATE_NO_BATTERY
    ]
    remaining, pct = c_int(), c_int()
    state = sdl2.SDL_GetPowerInfo(byref(remaining), byref(pct))
    if state in has_battery:
        assert pct.value <= 100
        assert pct.value > 0
    elif state in no_battery:
        assert remaining.value == -1
        assert pct.value == -1
    # else no assertion about remaining and pct:
    # we can have state SDL_POWERSTATE_UNKNOWN and still know a percentage
    # if a battery is present but is not being charged
