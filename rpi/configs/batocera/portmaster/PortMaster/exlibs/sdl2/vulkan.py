from ctypes import c_int, c_uint, c_uint64, c_void_p, c_char_p
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import SDL_bool
from .video import SDL_Window

# NOTE: I have no idea whether this module actually works

__all__ = []


# Raw ctypes function definitions

VkInstance = c_void_p
VkSurfaceKHR = c_uint64

_funcdefs = [
    SDLFunc("SDL_Vulkan_LoadLibrary", [c_char_p], c_int, added='2.0.6'),
    SDLFunc("SDL_Vulkan_GetVkGetInstanceProcAddr", None, c_void_p, added='2.0.6'),
    SDLFunc("SDL_Vulkan_UnloadLibrary", None, None, added='2.0.6'),
    SDLFunc("SDL_Vulkan_GetInstanceExtensions",
        [_P(SDL_Window), _P(c_uint), _P(c_char_p)],
        returns = SDL_bool, added = '2.0.6'
    ),
    SDLFunc("SDL_Vulkan_CreateSurface",
        [_P(SDL_Window), VkInstance, _P(VkSurfaceKHR)],
        returns = SDL_bool, added = '2.0.6'
    ),
    SDLFunc("SDL_Vulkan_GetDrawableSize",
        [_P(SDL_Window), _P(c_int), _P(c_int)],
        returns = None, added = '2.0.6'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_Vulkan_LoadLibrary = _ctypes["SDL_Vulkan_LoadLibrary"]
SDL_Vulkan_GetVkGetInstanceProcAddr = _ctypes["SDL_Vulkan_GetVkGetInstanceProcAddr"]
SDL_Vulkan_UnloadLibrary = _ctypes["SDL_Vulkan_UnloadLibrary"]
SDL_Vulkan_GetInstanceExtensions = _ctypes["SDL_Vulkan_GetInstanceExtensions"]
SDL_Vulkan_CreateSurface = _ctypes["SDL_Vulkan_CreateSurface"]
SDL_Vulkan_GetDrawableSize = _ctypes["SDL_Vulkan_GetDrawableSize"]
