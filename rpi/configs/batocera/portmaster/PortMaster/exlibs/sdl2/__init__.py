"""SDL2 wrapper package"""
from .dll import get_dll_file, _bind

from ._sdl_init import *
from .audio import *
from .blendmode import *
from .clipboard import *
from .cpuinfo import *
from .endian import *
from .error import *
from .events import *
from .filesystem import *
from .gamecontroller import *
from .gesture import *
from .guid import *
from .haptic import *
from .hidapi import *
from .hints import *
from .joystick import *
from .keyboard import *
from .loadso import *
from .log import *
from .messagebox import *
from .metal import *
from .mouse import *
from .pixels import *
from .platform import *
from .power import *
from .rect import *
from .render import *
from .rwops import *
from .sensor import *
from .shape import *
from .stdinc import *
from .surface import *
from .syswm import *
from .timer import *
from .touch import *
from .version import *
from .video import *
from .locale import *
from .misc import *

from .keycode import *
from .scancode import *


# At least Win32 platforms need this now.
_SDL_SetMainReady = _bind("SDL_SetMainReady")
_SDL_SetMainReady()

__version__ = "0.9.15"
version_info = (0, 9, 15)
