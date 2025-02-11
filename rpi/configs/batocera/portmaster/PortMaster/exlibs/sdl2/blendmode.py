from ctypes import c_int
from .dll import _bind, SDLFunc, AttributeDict

__all__ = [
    # Enums
    "SDL_BlendMode",
    "SDL_BLENDMODE_NONE", "SDL_BLENDMODE_BLEND", "SDL_BLENDMODE_ADD",
    "SDL_BLENDMODE_MOD", "SDL_BLENDMODE_MUL", "SDL_BLENDMODE_INVALID",

    "SDL_BlendOperation",
    "SDL_BLENDOPERATION_ADD", "SDL_BLENDOPERATION_SUBTRACT",
    "SDL_BLENDOPERATION_REV_SUBTRACT", "SDL_BLENDOPERATION_MINIMUM",
    "SDL_BLENDOPERATION_MAXIMUM",

    "SDL_BlendFactor",
    "SDL_BLENDFACTOR_ZERO", "SDL_BLENDFACTOR_ONE",
    "SDL_BLENDFACTOR_SRC_COLOR", "SDL_BLENDFACTOR_ONE_MINUS_SRC_COLOR",
    "SDL_BLENDFACTOR_SRC_ALPHA", "SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA",
    "SDL_BLENDFACTOR_DST_COLOR", "SDL_BLENDFACTOR_ONE_MINUS_DST_COLOR",
    "SDL_BLENDFACTOR_DST_ALPHA", "SDL_BLENDFACTOR_ONE_MINUS_DST_ALPHA",
]


# Constants & enums

SDL_BlendMode = c_int
SDL_BLENDMODE_NONE = 0x00000000
SDL_BLENDMODE_BLEND = 0x00000001
SDL_BLENDMODE_ADD = 0x00000002
SDL_BLENDMODE_MOD = 0x00000004
SDL_BLENDMODE_MUL = 0x00000008
SDL_BLENDMODE_INVALID = 0x7FFFFFFF

SDL_BlendOperation = c_int
SDL_BLENDOPERATION_ADD = 0x1
SDL_BLENDOPERATION_SUBTRACT = 0x2
SDL_BLENDOPERATION_REV_SUBTRACT = 0x3
SDL_BLENDOPERATION_MINIMUM = 0x4
SDL_BLENDOPERATION_MAXIMUM = 0x5

SDL_BlendFactor = c_int
SDL_BLENDFACTOR_ZERO                = 0x1
SDL_BLENDFACTOR_ONE                 = 0x2
SDL_BLENDFACTOR_SRC_COLOR           = 0x3
SDL_BLENDFACTOR_ONE_MINUS_SRC_COLOR = 0x4
SDL_BLENDFACTOR_SRC_ALPHA           = 0x5
SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA = 0x6
SDL_BLENDFACTOR_DST_COLOR           = 0x7
SDL_BLENDFACTOR_ONE_MINUS_DST_COLOR = 0x8
SDL_BLENDFACTOR_DST_ALPHA           = 0x9
SDL_BLENDFACTOR_ONE_MINUS_DST_ALPHA = 0xA


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_ComposeCustomBlendMode",
        args = [SDL_BlendFactor, SDL_BlendFactor, SDL_BlendOperation, SDL_BlendFactor,
                SDL_BlendFactor, SDL_BlendOperation],
        returns = SDL_BlendMode, added = '2.0.6'
    ),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_ComposeCustomBlendMode = _ctypes["SDL_ComposeCustomBlendMode"]
