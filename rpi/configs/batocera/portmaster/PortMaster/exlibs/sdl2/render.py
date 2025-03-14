from ctypes import Structure, c_int, c_char_p, c_void_p, c_float, c_double
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint8, Uint32, SDL_bool
from .pixels import SDL_Color
from .blendmode import SDL_BlendMode
from .rect import SDL_Point, SDL_FPoint, SDL_Rect, SDL_FRect
from .surface import SDL_Surface
from .video import SDL_Window

__all__ = [
    # Structs & Opaque Types
    "SDL_RendererInfo", "SDL_Renderer", "SDL_Texture", "SDL_Vertex",

    # Enums
    "SDL_RendererFlags",
    "SDL_RENDERER_SOFTWARE", "SDL_RENDERER_ACCELERATED",
    "SDL_RENDERER_PRESENTVSYNC", "SDL_RENDERER_TARGETTEXTURE",

    "SDL_ScaleMode",
    "SDL_ScaleModeNearest", "SDL_ScaleModeLinear", "SDL_ScaleModeBest",

    "SDL_TextureAccess",
    "SDL_TEXTUREACCESS_STATIC", "SDL_TEXTUREACCESS_STREAMING",
    "SDL_TEXTUREACCESS_TARGET",

    "SDL_TextureModulate",
    "SDL_TEXTUREMODULATE_NONE", "SDL_TEXTUREMODULATE_COLOR",
    "SDL_TEXTUREMODULATE_ALPHA",

    "SDL_RendererFlip",
    "SDL_FLIP_NONE", "SDL_FLIP_HORIZONTAL", "SDL_FLIP_VERTICAL",
]


# Constants & enums

SDL_RendererFlags = c_int
SDL_RENDERER_SOFTWARE = 0x00000001
SDL_RENDERER_ACCELERATED = 0x00000002
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_RENDERER_TARGETTEXTURE = 0x00000008

SDL_ScaleMode = c_int
SDL_ScaleModeNearest = 0
SDL_ScaleModeLinear = 1
SDL_ScaleModeBest = 2

SDL_TextureAccess = c_int
SDL_TEXTUREACCESS_STATIC = 0
SDL_TEXTUREACCESS_STREAMING = 1
SDL_TEXTUREACCESS_TARGET = 2

SDL_TextureModulate = c_int
SDL_TEXTUREMODULATE_NONE = 0x00000000
SDL_TEXTUREMODULATE_COLOR = 0x00000001
SDL_TEXTUREMODULATE_ALPHA = 0x00000002

SDL_RendererFlip = c_int
SDL_FLIP_NONE = 0x00000000
SDL_FLIP_HORIZONTAL = 0x00000001
SDL_FLIP_VERTICAL = 0x00000002


# Structs & opaque typedefs

class SDL_RendererInfo(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("flags", Uint32),
        ("num_texture_formats", Uint32),
        ("texture_formats", Uint32 * 16),
        ("max_texture_width", c_int),
        ("max_texture_height", c_int),
    ]

class SDL_Vertex(Structure):
    _fields_ = [
        ("position", SDL_FPoint),
        ("color", SDL_Color),
        ("tex_coord", SDL_FPoint),
    ]

    def __init__(
        self, position=SDL_FPoint(), color=SDL_Color(), tex_coord=SDL_FPoint()
    ):
        super(SDL_Vertex, self).__init__()
        self.position = self._get_point(position, "position")
        self.color = self._get_color(color)
        self.tex_coord = self._get_point(tex_coord, "tex_coord")

    def _get_point(self, p, argname):
        if type(p) in (tuple, list) and len(p) == 2:
            p = SDL_FPoint(p[0], p[1])
        elif type(p) == SDL_FPoint:
            p = SDL_FPoint(p.x, p.y)
        else:
            err = "'{0}' must be an (x, y) tuple or an SDL_FPoint."
            raise ValueError(err.format(argname))
        return p

    def _get_color(self, col):
        if type(col).__name__ in ("Color", "SDL_Color"):
            col = SDL_Color(col.r, col.g, col.b, col.a)
        elif type(col) in (tuple, list) and len(col) in (3, 4):
            if len(col) == 3:
                col = SDL_Color(col[0], col[1], col[2], 255)
            else:
                col = SDL_Color(col[0], col[1], col[2], col[3])
        else:
            err = "'color' must be an RGBA tuple or an SDL_Color."
            raise ValueError(err)
        return col

    def __repr__(self):
        x = round(self.position.x, 4)
        y = round(self.position.y, 4)
        c = self.color
        col = str([c.r, c.g, c.b, c.a])
        return "SDL_Vertex(x={0}, y={1}, color={2})".format(x, y, col)

    def __copy__(self):
        return SDL_Vertex(self.position, self.color, self.tex_coord)

    def __deepcopy__(self, memo):
        return SDL_Vertex(self.position, self.color, self.tex_coord)

class SDL_Renderer(c_void_p):
    pass

class SDL_Texture(c_void_p):
    pass


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetNumRenderDrivers", None, c_int),
    SDLFunc("SDL_GetRenderDriverInfo", [c_int, _P(SDL_RendererInfo)], c_int),
    SDLFunc("SDL_CreateWindowAndRenderer",
        [c_int, c_int, Uint32, _P(_P(SDL_Window)), _P(_P(SDL_Renderer))],
        returns = c_int
    ),
    SDLFunc("SDL_CreateRenderer", [_P(SDL_Window), c_int, Uint32], _P(SDL_Renderer)),
    SDLFunc("SDL_CreateSoftwareRenderer", [_P(SDL_Surface)], _P(SDL_Renderer)),
    SDLFunc("SDL_GetRenderer", [_P(SDL_Window)], _P(SDL_Renderer)),
    SDLFunc("SDL_RenderGetWindow", [_P(SDL_Renderer)], _P(SDL_Window), added='2.0.22'),
    SDLFunc("SDL_GetRendererInfo", [_P(SDL_Renderer), _P(SDL_RendererInfo)], c_int),
    SDLFunc("SDL_GetRendererOutputSize", [_P(SDL_Renderer), _P(c_int), _P(c_int)], c_int),
    SDLFunc("SDL_CreateTexture", [_P(SDL_Renderer), Uint32, c_int, c_int, c_int], _P(SDL_Texture)),
    SDLFunc("SDL_CreateTextureFromSurface", [_P(SDL_Renderer), _P(SDL_Surface)], _P(SDL_Texture)),
    SDLFunc("SDL_QueryTexture",
        [_P(SDL_Texture), _P(Uint32), _P(c_int), _P(c_int), _P(c_int)],
        returns = c_int
    ),
    SDLFunc("SDL_SetTextureColorMod", [_P(SDL_Texture), Uint8, Uint8, Uint8], c_int),
    SDLFunc("SDL_GetTextureColorMod", [_P(SDL_Texture), _P(Uint8), _P(Uint8), _P(Uint8)], c_int),
    SDLFunc("SDL_SetTextureAlphaMod", [_P(SDL_Texture), Uint8], c_int),
    SDLFunc("SDL_GetTextureAlphaMod", [_P(SDL_Texture), _P(Uint8)], c_int),
    SDLFunc("SDL_SetTextureBlendMode", [_P(SDL_Texture), SDL_BlendMode], c_int),
    SDLFunc("SDL_GetTextureBlendMode", [_P(SDL_Texture), _P(SDL_BlendMode)], c_int),
    SDLFunc("SDL_SetTextureScaleMode",
        [_P(SDL_Texture), SDL_ScaleMode],
        returns = c_int, added = '2.0.12'
    ),
    SDLFunc("SDL_GetTextureScaleMode",
        [_P(SDL_Texture), _P(SDL_ScaleMode)],
        returns = c_int, added = '2.0.12'
    ),
    SDLFunc("SDL_SetTextureUserData", [_P(SDL_Texture), c_void_p], c_int, added='2.0.18'),
    SDLFunc("SDL_GetTextureUserData", [_P(SDL_Texture)], c_void_p, added='2.0.18'),
    SDLFunc("SDL_UpdateTexture", [_P(SDL_Texture), _P(SDL_Rect), c_void_p, c_int], c_int),
    SDLFunc("SDL_UpdateYUVTexture",
        [_P(SDL_Texture), _P(SDL_Rect), _P(Uint8), c_int, _P(Uint8), c_int, _P(Uint8), c_int],
        returns = c_int
    ),
    SDLFunc("SDL_UpdateNVTexture",
        [_P(SDL_Texture), _P(SDL_Rect), _P(Uint8), c_int, _P(Uint8), c_int],
        returns = c_int, added = '2.0.16'
    ),
    SDLFunc("SDL_LockTexture", [_P(SDL_Texture), _P(SDL_Rect), _P(c_void_p), _P(c_int)], c_int),
    SDLFunc("SDL_LockTextureToSurface",
        [_P(SDL_Texture), _P(SDL_Rect), _P(_P(SDL_Surface))],
        returns = c_int, added = '2.0.12'
    ),
    SDLFunc("SDL_UnlockTexture", [_P(SDL_Texture)]),
    SDLFunc("SDL_RenderTargetSupported", [_P(SDL_Renderer)], SDL_bool),
    SDLFunc("SDL_SetRenderTarget", [_P(SDL_Renderer), _P(SDL_Texture)], c_int),
    SDLFunc("SDL_GetRenderTarget", [_P(SDL_Renderer)], _P(SDL_Texture)),
    SDLFunc("SDL_RenderSetLogicalSize", [_P(SDL_Renderer), c_int, c_int], c_int),
    SDLFunc("SDL_RenderGetLogicalSize", [_P(SDL_Renderer), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_RenderSetIntegerScale", [_P(SDL_Renderer), SDL_bool], c_int, added='2.0.5'),
    SDLFunc("SDL_RenderGetIntegerScale", [_P(SDL_Renderer)], SDL_bool, added='2.0.5'),
    SDLFunc("SDL_RenderSetViewport", [_P(SDL_Renderer), _P(SDL_Rect)], c_int),
    SDLFunc("SDL_RenderGetViewport", [_P(SDL_Renderer), _P(SDL_Rect)]),
    SDLFunc("SDL_RenderGetClipRect", [_P(SDL_Renderer), _P(SDL_Rect)]),
    SDLFunc("SDL_RenderSetClipRect", [_P(SDL_Renderer), _P(SDL_Rect)], c_int),
    SDLFunc("SDL_RenderIsClipEnabled", [_P(SDL_Renderer)], SDL_bool, added='2.0.4'),
    SDLFunc("SDL_RenderSetScale", [_P(SDL_Renderer), c_float, c_float], c_int),
    SDLFunc("SDL_RenderGetScale", [_P(SDL_Renderer), _P(c_float), _P(c_float)]),
    SDLFunc("SDL_RenderWindowToLogical",
        [_P(SDL_Renderer), c_int, c_int, _P(c_float), _P(c_float)],
        returns = None, added = '2.0.18'
    ),
    SDLFunc("SDL_RenderLogicalToWindow",
        [_P(SDL_Renderer), c_float, c_float, _P(c_int), _P(c_int)],
        returns = None, added = '2.0.18'
    ),
    SDLFunc("SDL_SetRenderDrawColor", [_P(SDL_Renderer), Uint8, Uint8, Uint8, Uint8], c_int),
    SDLFunc("SDL_GetRenderDrawColor",
        [_P(SDL_Renderer), _P(Uint8), _P(Uint8), _P(Uint8), _P(Uint8)],
        returns = c_int
    ),
    SDLFunc("SDL_SetRenderDrawBlendMode", [_P(SDL_Renderer), SDL_BlendMode], c_int),
    SDLFunc("SDL_GetRenderDrawBlendMode", [_P(SDL_Renderer), _P(SDL_BlendMode)], c_int),
    SDLFunc("SDL_RenderClear", [_P(SDL_Renderer)], c_int),
    SDLFunc("SDL_RenderDrawPoint", [_P(SDL_Renderer), c_int, c_int], c_int),
    SDLFunc("SDL_RenderDrawPoints", [_P(SDL_Renderer), _P(SDL_Point), c_int], c_int),
    SDLFunc("SDL_RenderDrawLine", [_P(SDL_Renderer), c_int, c_int, c_int, c_int], c_int),
    SDLFunc("SDL_RenderDrawLines", [_P(SDL_Renderer), _P(SDL_Point), c_int], c_int),
    SDLFunc("SDL_RenderDrawRect", [_P(SDL_Renderer), _P(SDL_Rect)], c_int),
    SDLFunc("SDL_RenderDrawRects", [_P(SDL_Renderer), _P(SDL_Rect), c_int], c_int),
    SDLFunc("SDL_RenderFillRect", [_P(SDL_Renderer), _P(SDL_Rect)], c_int),
    SDLFunc("SDL_RenderFillRects", [_P(SDL_Renderer), _P(SDL_Rect), c_int], c_int),
    SDLFunc("SDL_RenderCopy",
        [_P(SDL_Renderer), _P(SDL_Texture), _P(SDL_Rect), _P(SDL_Rect)],
        returns = c_int
    ),
    SDLFunc("SDL_RenderCopyEx",
        args = [_P(SDL_Renderer), _P(SDL_Texture), _P(SDL_Rect), _P(SDL_Rect),
                c_double, _P(SDL_Point), SDL_RendererFlip],
        returns = c_int
    ),
    SDLFunc("SDL_RenderDrawPointF", [_P(SDL_Renderer), c_float, c_float], c_int, added='2.0.10'),
    SDLFunc("SDL_RenderDrawPointsF",
        [_P(SDL_Renderer), _P(SDL_FPoint), c_int],
        returns = c_int, added = '2.0.10'
    ),
    SDLFunc("SDL_RenderDrawLineF",
        [_P(SDL_Renderer), c_float, c_float, c_float, c_float],
        returns = c_int, added = '2.0.10'
    ),
    SDLFunc("SDL_RenderDrawLinesF",
        [_P(SDL_Renderer), _P(SDL_FPoint), c_int],
        returns = c_int, added = '2.0.10'
    ),
    SDLFunc("SDL_RenderDrawRectF", [_P(SDL_Renderer), _P(SDL_FRect)], c_int, added='2.0.10'),
    SDLFunc("SDL_RenderDrawRectsF", [_P(SDL_Renderer), _P(SDL_FRect), c_int], c_int, added='2.0.10'),
    SDLFunc("SDL_RenderFillRectF", [_P(SDL_Renderer), _P(SDL_FRect)], c_int, added='2.0.10'),
    SDLFunc("SDL_RenderFillRectsF", [_P(SDL_Renderer), _P(SDL_FRect), c_int], c_int, added='2.0.10'),
    SDLFunc("SDL_RenderCopyF",
        [_P(SDL_Renderer), _P(SDL_Texture), _P(SDL_Rect), _P(SDL_FRect)],
        returns = c_int, added = '2.0.10'
    ),
    SDLFunc("SDL_RenderCopyExF",
        args = [_P(SDL_Renderer), _P(SDL_Texture), _P(SDL_Rect), _P(SDL_FRect),
                c_double, _P(SDL_FPoint), SDL_RendererFlip],
        returns = c_int, added = '2.0.10'
    ),
    SDLFunc("SDL_RenderGeometry",
        [_P(SDL_Renderer), _P(SDL_Texture), _P(SDL_Vertex), c_int, _P(c_int), c_int],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_RenderGeometryRaw",
        args = [_P(SDL_Renderer), _P(SDL_Texture), _P(c_float), c_int, _P(SDL_Color),
                c_int, _P(c_float), c_int, c_int, c_void_p, c_int, c_int],
        returns = c_int, added = '2.0.18'
    ),
    SDLFunc("SDL_RenderReadPixels",
        [_P(SDL_Renderer), _P(SDL_Rect), Uint32, c_void_p, c_int],
        returns = c_int
    ),
    SDLFunc("SDL_RenderPresent", [_P(SDL_Renderer)]),
    SDLFunc("SDL_DestroyTexture", [_P(SDL_Texture)]),
    SDLFunc("SDL_DestroyRenderer", [_P(SDL_Renderer)]),
    SDLFunc("SDL_RenderFlush", [_P(SDL_Renderer)], c_int, added='2.0.10'),
    SDLFunc("SDL_GL_BindTexture", [_P(SDL_Texture), _P(c_float), _P(c_float)], c_int),
    SDLFunc("SDL_GL_UnbindTexture", [_P(SDL_Texture)], c_int),
    SDLFunc("SDL_RenderGetMetalLayer", [_P(SDL_Renderer)], c_void_p, added='2.0.8'),
    SDLFunc("SDL_RenderGetMetalCommandEncoder", [_P(SDL_Renderer)], c_void_p, added='2.0.8'),
    SDLFunc("SDL_RenderSetVSync", [_P(SDL_Renderer), c_int], c_int, added='2.0.18'),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetNumRenderDrivers = _ctypes["SDL_GetNumRenderDrivers"]
SDL_GetRenderDriverInfo = _ctypes["SDL_GetRenderDriverInfo"]
SDL_CreateWindowAndRenderer = _ctypes["SDL_CreateWindowAndRenderer"]
SDL_CreateRenderer = _ctypes["SDL_CreateRenderer"]
SDL_CreateSoftwareRenderer = _ctypes["SDL_CreateSoftwareRenderer"]
SDL_GetRenderer = _ctypes["SDL_GetRenderer"]
SDL_RenderGetWindow = _ctypes["SDL_RenderGetWindow"]
SDL_GetRendererInfo = _ctypes["SDL_GetRendererInfo"]
SDL_GetRendererOutputSize = _ctypes["SDL_GetRendererOutputSize"]
SDL_CreateTexture = _ctypes["SDL_CreateTexture"]
SDL_CreateTextureFromSurface = _ctypes["SDL_CreateTextureFromSurface"]
SDL_QueryTexture = _ctypes["SDL_QueryTexture"]
SDL_SetTextureColorMod = _ctypes["SDL_SetTextureColorMod"]
SDL_GetTextureColorMod = _ctypes["SDL_GetTextureColorMod"]
SDL_SetTextureAlphaMod = _ctypes["SDL_SetTextureAlphaMod"]
SDL_GetTextureAlphaMod = _ctypes["SDL_GetTextureAlphaMod"]
SDL_SetTextureBlendMode = _ctypes["SDL_SetTextureBlendMode"]
SDL_GetTextureBlendMode = _ctypes["SDL_GetTextureBlendMode"]
SDL_SetTextureScaleMode = _ctypes["SDL_SetTextureScaleMode"]
SDL_GetTextureScaleMode = _ctypes["SDL_GetTextureScaleMode"]
SDL_SetTextureUserData = _ctypes["SDL_SetTextureUserData"]
SDL_GetTextureUserData = _ctypes["SDL_GetTextureUserData"]
SDL_UpdateTexture = _ctypes["SDL_UpdateTexture"]
SDL_UpdateYUVTexture = _ctypes["SDL_UpdateYUVTexture"]
SDL_UpdateNVTexture = _ctypes["SDL_UpdateNVTexture"]
SDL_LockTexture = _ctypes["SDL_LockTexture"]
SDL_LockTextureToSurface = _ctypes["SDL_LockTextureToSurface"]
SDL_UnlockTexture = _ctypes["SDL_UnlockTexture"]
SDL_RenderTargetSupported = _ctypes["SDL_RenderTargetSupported"]
SDL_SetRenderTarget = _ctypes["SDL_SetRenderTarget"]
SDL_GetRenderTarget = _ctypes["SDL_GetRenderTarget"]
SDL_RenderSetLogicalSize = _ctypes["SDL_RenderSetLogicalSize"]
SDL_RenderGetLogicalSize = _ctypes["SDL_RenderGetLogicalSize"]
SDL_RenderSetIntegerScale = _ctypes["SDL_RenderSetIntegerScale"]
SDL_RenderGetIntegerScale = _ctypes["SDL_RenderGetIntegerScale"]
SDL_RenderSetViewport = _ctypes["SDL_RenderSetViewport"]
SDL_RenderGetViewport = _ctypes["SDL_RenderGetViewport"]
SDL_RenderGetClipRect = _ctypes["SDL_RenderGetClipRect"]
SDL_RenderSetClipRect = _ctypes["SDL_RenderSetClipRect"]
SDL_RenderIsClipEnabled = _ctypes["SDL_RenderIsClipEnabled"]
SDL_RenderSetScale = _ctypes["SDL_RenderSetScale"]
SDL_RenderGetScale = _ctypes["SDL_RenderGetScale"]
SDL_RenderWindowToLogical = _ctypes["SDL_RenderWindowToLogical"]
SDL_RenderLogicalToWindow = _ctypes["SDL_RenderLogicalToWindow"]
SDL_SetRenderDrawColor = _ctypes["SDL_SetRenderDrawColor"]
SDL_GetRenderDrawColor = _ctypes["SDL_GetRenderDrawColor"]
SDL_SetRenderDrawBlendMode = _ctypes["SDL_SetRenderDrawBlendMode"]
SDL_GetRenderDrawBlendMode = _ctypes["SDL_GetRenderDrawBlendMode"]
SDL_RenderClear = _ctypes["SDL_RenderClear"]
SDL_RenderDrawPoint = _ctypes["SDL_RenderDrawPoint"]
SDL_RenderDrawPoints = _ctypes["SDL_RenderDrawPoints"]
SDL_RenderDrawLine = _ctypes["SDL_RenderDrawLine"]
SDL_RenderDrawLines = _ctypes["SDL_RenderDrawLines"]
SDL_RenderDrawRect = _ctypes["SDL_RenderDrawRect"]
SDL_RenderDrawRects = _ctypes["SDL_RenderDrawRects"]
SDL_RenderFillRect = _ctypes["SDL_RenderFillRect"]
SDL_RenderFillRects = _ctypes["SDL_RenderFillRects"]
SDL_RenderCopy = _ctypes["SDL_RenderCopy"]
SDL_RenderCopyEx = _ctypes["SDL_RenderCopyEx"]
SDL_RenderDrawPointF = _ctypes["SDL_RenderDrawPointF"]
SDL_RenderDrawPointsF = _ctypes["SDL_RenderDrawPointsF"]
SDL_RenderDrawLineF = _ctypes["SDL_RenderDrawLineF"]
SDL_RenderDrawLinesF = _ctypes["SDL_RenderDrawLinesF"]
SDL_RenderDrawRectF = _ctypes["SDL_RenderDrawRectF"]
SDL_RenderDrawRectsF = _ctypes["SDL_RenderDrawRectsF"]
SDL_RenderFillRectF = _ctypes["SDL_RenderFillRectF"]
SDL_RenderFillRectsF = _ctypes["SDL_RenderFillRectsF"]
SDL_RenderCopyF = _ctypes["SDL_RenderCopyF"]
SDL_RenderCopyExF = _ctypes["SDL_RenderCopyExF"]
SDL_RenderGeometry = _ctypes["SDL_RenderGeometry"]
SDL_RenderGeometryRaw = _ctypes["SDL_RenderGeometryRaw"]
SDL_RenderReadPixels = _ctypes["SDL_RenderReadPixels"]
SDL_RenderPresent = _ctypes["SDL_RenderPresent"]
SDL_DestroyTexture = _ctypes["SDL_DestroyTexture"]
SDL_DestroyRenderer = _ctypes["SDL_DestroyRenderer"]
SDL_RenderFlush = _ctypes["SDL_RenderFlush"]
SDL_GL_BindTexture = _ctypes["SDL_GL_BindTexture"]
SDL_GL_UnbindTexture = _ctypes["SDL_GL_UnbindTexture"]
SDL_RenderGetMetalLayer = _ctypes["SDL_RenderGetMetalLayer"]
SDL_RenderGetMetalCommandEncoder = _ctypes["SDL_RenderGetMetalCommandEncoder"]
SDL_RenderSetVSync = _ctypes["SDL_RenderSetVSync"]
