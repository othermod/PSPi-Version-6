from ctypes import (
    c_int, c_void_p, c_char_p, c_float, c_size_t, py_object, Structure, CFUNCTYPE
)
from ctypes import POINTER as _P
from .dll import _bind, SDLFunc, AttributeDict
from .stdinc import Uint16, Uint32, SDL_bool
from .rect import SDL_Point, SDL_Rect
from .surface import SDL_Surface

__all__ = [
    # Structs & Opaque Types
    "SDL_DisplayMode", "SDL_Window", "SDL_GLContext",

    # Enums
    "SDL_WindowFlags",
    "SDL_WINDOW_FULLSCREEN", "SDL_WINDOW_OPENGL", "SDL_WINDOW_SHOWN",
    "SDL_WINDOW_HIDDEN", "SDL_WINDOW_BORDERLESS",
    "SDL_WINDOW_RESIZABLE", "SDL_WINDOW_MINIMIZED",
    "SDL_WINDOW_MAXIMIZED",
    "SDL_WINDOW_INPUT_GRABBED", "SDL_WINDOW_MOUSE_GRABBED",
    "SDL_WINDOW_INPUT_FOCUS", "SDL_WINDOW_MOUSE_FOCUS",
    "SDL_WINDOW_FULLSCREEN_DESKTOP", "SDL_WINDOW_FOREIGN",
    "SDL_WINDOW_ALLOW_HIGHDPI", "SDL_WINDOW_MOUSE_CAPTURE",
    "SDL_WINDOW_ALWAYS_ON_TOP", "SDL_WINDOW_SKIP_TASKBAR",
    "SDL_WINDOW_UTILITY", "SDL_WINDOW_TOOLTIP",
    "SDL_WINDOW_POPUP_MENU", "SDL_WINDOW_KEYBOARD_GRABBED",
    "SDL_WINDOW_VULKAN", "SDL_WINDOW_METAL",
    "SDL_WINDOW_INPUT_FOCUS",

    "SDL_WindowEventID",
    "SDL_WINDOWEVENT_NONE",
    "SDL_WINDOWEVENT_SHOWN", "SDL_WINDOWEVENT_HIDDEN",
    "SDL_WINDOWEVENT_EXPOSED", "SDL_WINDOWEVENT_MOVED",
    "SDL_WINDOWEVENT_RESIZED", "SDL_WINDOWEVENT_SIZE_CHANGED",
    "SDL_WINDOWEVENT_MINIMIZED", "SDL_WINDOWEVENT_MAXIMIZED",
    "SDL_WINDOWEVENT_RESTORED", "SDL_WINDOWEVENT_ENTER",
    "SDL_WINDOWEVENT_LEAVE", "SDL_WINDOWEVENT_FOCUS_GAINED",
    "SDL_WINDOWEVENT_FOCUS_LOST", "SDL_WINDOWEVENT_CLOSE",
    "SDL_WINDOWEVENT_TAKE_FOCUS", "SDL_WINDOWEVENT_HIT_TEST",
    "SDL_WINDOWEVENT_ICCPROF_CHANGED", "SDL_WINDOWEVENT_DISPLAY_CHANGED",

    "SDL_DisplayEventID",
    "SDL_DISPLAYEVENT_NONE", "SDL_DISPLAYEVENT_ORIENTATION",
    "SDL_DISPLAYEVENT_CONNECTED", "SDL_DISPLAYEVENT_DISCONNECTED",
    
    "SDL_DisplayOrientation",
    "SDL_ORIENTATION_UNKNOWN", "SDL_ORIENTATION_LANDSCAPE",
    "SDL_ORIENTATION_LANDSCAPE_FLIPPED", "SDL_ORIENTATION_PORTRAIT",
    "SDL_ORIENTATION_PORTRAIT_FLIPPED",

    "SDL_FlashOperation",
    "SDL_FLASH_CANCEL", "SDL_FLASH_BRIEFLY", "SDL_FLASH_UNTIL_FOCUSED",

    "SDL_GLattr",
    "SDL_GL_RED_SIZE",
    "SDL_GL_GREEN_SIZE", "SDL_GL_BLUE_SIZE", "SDL_GL_ALPHA_SIZE",
    "SDL_GL_BUFFER_SIZE", "SDL_GL_DOUBLEBUFFER", "SDL_GL_DEPTH_SIZE",
    "SDL_GL_STENCIL_SIZE", "SDL_GL_ACCUM_RED_SIZE",
    "SDL_GL_ACCUM_GREEN_SIZE", "SDL_GL_ACCUM_BLUE_SIZE",
    "SDL_GL_ACCUM_ALPHA_SIZE", "SDL_GL_STEREO",
    "SDL_GL_MULTISAMPLEBUFFERS", "SDL_GL_MULTISAMPLESAMPLES",
    "SDL_GL_ACCELERATED_VISUAL", "SDL_GL_RETAINED_BACKING",
    "SDL_GL_CONTEXT_MAJOR_VERSION", "SDL_GL_CONTEXT_MINOR_VERSION",
    "SDL_GL_CONTEXT_EGL", "SDL_GL_CONTEXT_FLAGS",
    "SDL_GL_CONTEXT_PROFILE_MASK", "SDL_GL_SHARE_WITH_CURRENT_CONTEXT",
    "SDL_GL_FRAMEBUFFER_SRGB_CAPABLE", "SDL_GL_CONTEXT_RELEASE_BEHAVIOR",
    "SDL_GL_CONTEXT_RESET_NOTIFICATION", "SDL_GL_CONTEXT_NO_ERROR",
    "SDL_GL_FLOATBUFFERS",

    "SDL_GLprofile",
    "SDL_GL_CONTEXT_PROFILE_CORE",
    "SDL_GL_CONTEXT_PROFILE_COMPATIBILITY",
    "SDL_GL_CONTEXT_PROFILE_ES",
           
    "SDL_GLcontextFlag",
    "SDL_GL_CONTEXT_DEBUG_FLAG",
    "SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG",
    "SDL_GL_CONTEXT_ROBUST_ACCESS_FLAG",
    "SDL_GL_CONTEXT_RESET_ISOLATION_FLAG",

    "SDL_GLcontextReleaseFlag",
    "SDL_GL_CONTEXT_RELEASE_BEHAVIOR_NONE",
    "SDL_GL_CONTEXT_RELEASE_BEHAVIOR_FLUSH",

    "SDL_GLContextResetNotification",
    "SDL_GL_CONTEXT_RESET_NO_NOTIFICATION",
    "SDL_GL_CONTEXT_RESET_LOSE_CONTEXT",

    "SDL_HitTestResult",
    "SDL_HITTEST_NORMAL", "SDL_HITTEST_DRAGGABLE", 
    "SDL_HITTEST_RESIZE_TOPLEFT", "SDL_HITTEST_RESIZE_TOP",
    "SDL_HITTEST_RESIZE_TOPRIGHT", "SDL_HITTEST_RESIZE_RIGHT",
    "SDL_HITTEST_RESIZE_BOTTOMRIGHT", "SDL_HITTEST_RESIZE_BOTTOM",
    "SDL_HITTEST_RESIZE_BOTTOMLEFT", "SDL_HITTEST_RESIZE_LEFT",

    # Macro Functions
    "SDL_WINDOWPOS_UNDEFINED_MASK", "SDL_WINDOWPOS_UNDEFINED_DISPLAY",
    "SDL_WINDOWPOS_UNDEFINED", "SDL_WINDOWPOS_ISUNDEFINED",
    "SDL_WINDOWPOS_CENTERED_MASK", "SDL_WINDOWPOS_CENTERED_DISPLAY",
    "SDL_WINDOWPOS_CENTERED", "SDL_WINDOWPOS_ISCENTERED",

    # Callback Functions
    "SDL_HitTest"
]


# Constants, enums, & macros

SDL_WindowFlags = c_int
SDL_WINDOW_FULLSCREEN = 0x00000001
SDL_WINDOW_OPENGL = 0x00000002
SDL_WINDOW_SHOWN = 0x00000004
SDL_WINDOW_HIDDEN = 0x00000008
SDL_WINDOW_BORDERLESS = 0x00000010
SDL_WINDOW_RESIZABLE = 0x00000020
SDL_WINDOW_MINIMIZED = 0x00000040
SDL_WINDOW_MAXIMIZED = 0x00000080
SDL_WINDOW_MOUSE_GRABBED = 0x00000100
SDL_WINDOW_INPUT_GRABBED = SDL_WINDOW_MOUSE_GRABBED  # for < 2.0.16
SDL_WINDOW_INPUT_FOCUS = 0x00000200
SDL_WINDOW_MOUSE_FOCUS = 0x00000400
SDL_WINDOW_FULLSCREEN_DESKTOP = (SDL_WINDOW_FULLSCREEN | 0x00001000)
SDL_WINDOW_FOREIGN = 0x00000800
SDL_WINDOW_ALLOW_HIGHDPI = 0x00002000
SDL_WINDOW_MOUSE_CAPTURE = 0x00004000
SDL_WINDOW_ALWAYS_ON_TOP = 0x00008000
SDL_WINDOW_SKIP_TASKBAR  = 0x00010000
SDL_WINDOW_UTILITY = 0x00020000
SDL_WINDOW_TOOLTIP = 0x00040000
SDL_WINDOW_POPUP_MENU = 0x00080000
SDL_WINDOW_KEYBOARD_GRABBED = 0x00100000
SDL_WINDOW_VULKAN = 0x10000000
SDL_WINDOW_METAL = 0x20000000

SDL_WindowEventID = c_int
SDL_WINDOWEVENT_NONE = 0
SDL_WINDOWEVENT_SHOWN = 1
SDL_WINDOWEVENT_HIDDEN = 2
SDL_WINDOWEVENT_EXPOSED = 3
SDL_WINDOWEVENT_MOVED = 4
SDL_WINDOWEVENT_RESIZED = 5
SDL_WINDOWEVENT_SIZE_CHANGED = 6
SDL_WINDOWEVENT_MINIMIZED = 7
SDL_WINDOWEVENT_MAXIMIZED = 8
SDL_WINDOWEVENT_RESTORED = 9
SDL_WINDOWEVENT_ENTER = 10
SDL_WINDOWEVENT_LEAVE = 11
SDL_WINDOWEVENT_FOCUS_GAINED = 12
SDL_WINDOWEVENT_FOCUS_LOST = 13
SDL_WINDOWEVENT_CLOSE = 14
SDL_WINDOWEVENT_TAKE_FOCUS = 15
SDL_WINDOWEVENT_HIT_TEST = 16
SDL_WINDOWEVENT_ICCPROF_CHANGED = 17
SDL_WINDOWEVENT_DISPLAY_CHANGED = 18

SDL_DisplayEventID = c_int
SDL_DISPLAYEVENT_NONE = 0
SDL_DISPLAYEVENT_ORIENTATION = 1
SDL_DISPLAYEVENT_CONNECTED = 2
SDL_DISPLAYEVENT_DISCONNECTED = 3

SDL_DisplayOrientation = c_int
SDL_ORIENTATION_UNKNOWN = 0
SDL_ORIENTATION_LANDSCAPE = 1
SDL_ORIENTATION_LANDSCAPE_FLIPPED = 2
SDL_ORIENTATION_PORTRAIT = 3
SDL_ORIENTATION_PORTRAIT_FLIPPED = 4

SDL_FlashOperation = c_int
SDL_FLASH_CANCEL = 0
SDL_FLASH_BRIEFLY = 1
SDL_FLASH_UNTIL_FOCUSED = 2

SDL_GLattr = c_int
SDL_GL_RED_SIZE = 0
SDL_GL_GREEN_SIZE = 1
SDL_GL_BLUE_SIZE = 2
SDL_GL_ALPHA_SIZE = 3
SDL_GL_BUFFER_SIZE = 4
SDL_GL_DOUBLEBUFFER = 5
SDL_GL_DEPTH_SIZE = 6
SDL_GL_STENCIL_SIZE = 7
SDL_GL_ACCUM_RED_SIZE = 8
SDL_GL_ACCUM_GREEN_SIZE = 9
SDL_GL_ACCUM_BLUE_SIZE = 10
SDL_GL_ACCUM_ALPHA_SIZE = 11
SDL_GL_STEREO = 12
SDL_GL_MULTISAMPLEBUFFERS = 13
SDL_GL_MULTISAMPLESAMPLES = 14
SDL_GL_ACCELERATED_VISUAL = 15
SDL_GL_RETAINED_BACKING = 16
SDL_GL_CONTEXT_MAJOR_VERSION = 17
SDL_GL_CONTEXT_MINOR_VERSION = 18
SDL_GL_CONTEXT_EGL = 19
SDL_GL_CONTEXT_FLAGS = 20
SDL_GL_CONTEXT_PROFILE_MASK = 21
SDL_GL_SHARE_WITH_CURRENT_CONTEXT = 22
SDL_GL_FRAMEBUFFER_SRGB_CAPABLE = 23
SDL_GL_CONTEXT_RELEASE_BEHAVIOR = 24
SDL_GL_CONTEXT_RESET_NOTIFICATION = 25
SDL_GL_CONTEXT_NO_ERROR = 26
SDL_GL_FLOATBUFFERS = 27

SDL_GLprofile = c_int
SDL_GL_CONTEXT_PROFILE_CORE = 0x0001
SDL_GL_CONTEXT_PROFILE_COMPATIBILITY = 0x0002
SDL_GL_CONTEXT_PROFILE_ES = 0x0004

SDL_GLcontextFlag = c_int
SDL_GL_CONTEXT_DEBUG_FLAG = 0x0001
SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG = 0x0002
SDL_GL_CONTEXT_ROBUST_ACCESS_FLAG = 0x0004
SDL_GL_CONTEXT_RESET_ISOLATION_FLAG = 0x0008

SDL_GLcontextReleaseFlag = c_int
SDL_GL_CONTEXT_RELEASE_BEHAVIOR_NONE = 0x0000
SDL_GL_CONTEXT_RELEASE_BEHAVIOR_FLUSH = 0x0001

SDL_GLContextResetNotification = c_int
SDL_GL_CONTEXT_RESET_NO_NOTIFICATION = 0x0000
SDL_GL_CONTEXT_RESET_LOSE_CONTEXT = 0x0001

SDL_HitTestResult = c_int
SDL_HITTEST_NORMAL = 0
SDL_HITTEST_DRAGGABLE = 1
SDL_HITTEST_RESIZE_TOPLEFT = 2
SDL_HITTEST_RESIZE_TOP = 3
SDL_HITTEST_RESIZE_TOPRIGHT = 4
SDL_HITTEST_RESIZE_RIGHT = 5
SDL_HITTEST_RESIZE_BOTTOMRIGHT = 6
SDL_HITTEST_RESIZE_BOTTOM = 7
SDL_HITTEST_RESIZE_BOTTOMLEFT = 8
SDL_HITTEST_RESIZE_LEFT = 9

SDL_WINDOWPOS_UNDEFINED_MASK = 0x1FFF0000
SDL_WINDOWPOS_UNDEFINED_DISPLAY = lambda x: (SDL_WINDOWPOS_UNDEFINED_MASK | x)
SDL_WINDOWPOS_UNDEFINED = SDL_WINDOWPOS_UNDEFINED_DISPLAY(0)
SDL_WINDOWPOS_ISUNDEFINED = lambda x: ((x & 0xFFFF0000) == SDL_WINDOWPOS_UNDEFINED_MASK)

SDL_WINDOWPOS_CENTERED_MASK = 0x2FFF0000
SDL_WINDOWPOS_CENTERED_DISPLAY = lambda x: (SDL_WINDOWPOS_CENTERED_MASK | x)
SDL_WINDOWPOS_CENTERED = SDL_WINDOWPOS_CENTERED_DISPLAY(0)
SDL_WINDOWPOS_ISCENTERED = lambda x: ((x & 0xFFFF0000) == SDL_WINDOWPOS_CENTERED_MASK)


# Struct defintions & typedefs

SDL_GLContext = c_void_p

class SDL_Window(c_void_p):
    pass

class SDL_DisplayMode(Structure):
    _fields_ = [("format", Uint32),
                ("w", c_int),
                ("h", c_int),
                ("refresh_rate", c_int),
                ("driverdata", c_void_p)
               ]

    def __init__(self, format_=0, w=0, h=0, refresh_rate=0):
        super(SDL_DisplayMode, self).__init__()
        self.format = format_
        self.w = w
        self.h = h
        self.refresh_rate = refresh_rate

    def __repr__(self):
        s = "SDL_DisplayMode({0}x{1} @ {2}Hz)"
        return s.format(self.w, self.h, self.refresh_rate)

    def __eq__(self, mode):
        return self.format == mode.format and self.w == mode.w and \
            self.h == mode.h and self.refresh_rate == mode.refresh_rate

    def __ne__(self, mode):
        return self.format != mode.format or self.w != mode.w or \
            self.h != mode.h or self.refresh_rate != mode.refresh_rate


# Callback function definitions

SDL_HitTest = CFUNCTYPE(SDL_HitTestResult, _P(SDL_Window), _P(SDL_Point), c_void_p)


# Raw ctypes function definitions

_funcdefs = [
    SDLFunc("SDL_GetNumVideoDrivers", None, c_int),
    SDLFunc("SDL_GetVideoDriver", [c_int], c_char_p),
    SDLFunc("SDL_VideoInit", [c_char_p], c_int),
    SDLFunc("SDL_VideoQuit"),
    SDLFunc("SDL_GetCurrentVideoDriver", None, c_char_p),
    SDLFunc("SDL_GetNumVideoDisplays", None, c_int),
    SDLFunc("SDL_GetDisplayName", [c_int], c_char_p),
    SDLFunc("SDL_GetDisplayBounds", [c_int, _P(SDL_Rect)], c_int),
    SDLFunc("SDL_GetDisplayUsableBounds", [c_int, _P(SDL_Rect)], c_int, added='2.0.5'),
    SDLFunc("SDL_GetDisplayDPI",
        [c_int, _P(c_float), _P(c_float), _P(c_float)],
        returns = c_int, added = '2.0.4'
    ),
    SDLFunc("SDL_GetDisplayOrientation", [c_int], SDL_DisplayOrientation, added='2.0.9'),
    SDLFunc("SDL_GetNumDisplayModes", [c_int], c_int),
    SDLFunc("SDL_GetDisplayMode", [c_int, c_int, _P(SDL_DisplayMode)], c_int),
    SDLFunc("SDL_GetDesktopDisplayMode", [c_int, _P(SDL_DisplayMode)], c_int),
    SDLFunc("SDL_GetCurrentDisplayMode", [c_int, _P(SDL_DisplayMode)], c_int),
    SDLFunc("SDL_GetClosestDisplayMode",
        [c_int, _P(SDL_DisplayMode), _P(SDL_DisplayMode)],
        returns = _P(SDL_DisplayMode)
    ),
    SDLFunc("SDL_GetPointDisplayIndex", [_P(SDL_Point)], c_int, added='2.24.0'),
    SDLFunc("SDL_GetRectDisplayIndex", [_P(SDL_Rect)], c_int, added='2.24.0'),
    SDLFunc("SDL_GetWindowDisplayIndex", [_P(SDL_Window)], c_int),
    SDLFunc("SDL_SetWindowDisplayMode", [_P(SDL_Window), _P(SDL_DisplayMode)], c_int),
    SDLFunc("SDL_GetWindowDisplayMode", [_P(SDL_Window), _P(SDL_DisplayMode)], c_int),
    SDLFunc("SDL_GetWindowICCProfile", [_P(SDL_Window), _P(c_size_t)], c_void_p, added='2.0.18'),
    SDLFunc("SDL_GetWindowPixelFormat", [_P(SDL_Window)], Uint32),
    SDLFunc("SDL_CreateWindow", [c_char_p, c_int, c_int, c_int, c_int, Uint32], _P(SDL_Window)),
    SDLFunc("SDL_CreateWindowFrom", [c_void_p], _P(SDL_Window)),
    SDLFunc("SDL_GetWindowID", [_P(SDL_Window)], Uint32),
    SDLFunc("SDL_GetWindowFromID", [Uint32], _P(SDL_Window)),
    SDLFunc("SDL_GetWindowFlags", [_P(SDL_Window)], Uint32),
    SDLFunc("SDL_SetWindowTitle", [_P(SDL_Window), c_char_p]),
    SDLFunc("SDL_GetWindowTitle", [_P(SDL_Window)], c_char_p),
    SDLFunc("SDL_SetWindowIcon", [_P(SDL_Window), _P(SDL_Surface)]),
    SDLFunc("SDL_SetWindowData", [_P(SDL_Window), c_char_p, _P(py_object)], _P(py_object)),
    SDLFunc("SDL_GetWindowData", [_P(SDL_Window), c_char_p], _P(py_object)),
    SDLFunc("SDL_SetWindowPosition", [_P(SDL_Window), c_int, c_int]),
    SDLFunc("SDL_GetWindowPosition", [_P(SDL_Window), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_SetWindowSize", [_P(SDL_Window), c_int, c_int]),
    SDLFunc("SDL_GetWindowSize", [_P(SDL_Window), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_GetWindowBordersSize",
        [_P(SDL_Window), _P(c_int), _P(c_int), _P(c_int), _P(c_int)],
        returns = c_int, added = '2.0.5'
    ),
    SDLFunc("SDL_GetWindowSizeInPixels", [_P(SDL_Window), _P(c_int), _P(c_int)], added='2.26.0'),
    SDLFunc("SDL_SetWindowMinimumSize", [_P(SDL_Window), c_int, c_int]),
    SDLFunc("SDL_GetWindowMinimumSize", [_P(SDL_Window), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_SetWindowMaximumSize", [_P(SDL_Window), c_int, c_int]),
    SDLFunc("SDL_GetWindowMaximumSize", [_P(SDL_Window), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_SetWindowBordered", [_P(SDL_Window), SDL_bool]),
    SDLFunc("SDL_SetWindowResizable", [_P(SDL_Window), SDL_bool], added='2.0.5'),
    SDLFunc("SDL_SetWindowAlwaysOnTop", [_P(SDL_Window), SDL_bool], added='2.0.16'),
    SDLFunc("SDL_ShowWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_HideWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_RaiseWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_MaximizeWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_MinimizeWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_RestoreWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_SetWindowFullscreen", [_P(SDL_Window), Uint32], c_int),
    SDLFunc("SDL_GetWindowSurface", [_P(SDL_Window)], _P(SDL_Surface)),
    SDLFunc("SDL_UpdateWindowSurface", [_P(SDL_Window)], c_int),
    SDLFunc("SDL_UpdateWindowSurfaceRects", [_P(SDL_Window), _P(SDL_Rect), c_int], c_int),
    SDLFunc("SDL_SetWindowGrab", [_P(SDL_Window), SDL_bool]),
    SDLFunc("SDL_SetWindowKeyboardGrab", [_P(SDL_Window), SDL_bool], added='2.0.16'),
    SDLFunc("SDL_SetWindowMouseGrab", [_P(SDL_Window), SDL_bool], added='2.0.16'),
    SDLFunc("SDL_GetWindowGrab", [_P(SDL_Window)], SDL_bool),
    SDLFunc("SDL_GetWindowKeyboardGrab", [_P(SDL_Window)], SDL_bool, added='2.0.16'),
    SDLFunc("SDL_GetWindowMouseGrab", [_P(SDL_Window)], SDL_bool, added='2.0.16'),
    SDLFunc("SDL_GetGrabbedWindow", None, _P(SDL_Window), added='2.0.4'),
    SDLFunc("SDL_SetWindowMouseRect", [_P(SDL_Window), _P(SDL_Rect)], c_int, added='2.0.18'),
    SDLFunc("SDL_GetWindowMouseRect", [_P(SDL_Window)], _P(SDL_Rect), added='2.0.18'),
    SDLFunc("SDL_SetWindowBrightness", [_P(SDL_Window), c_float], c_int),
    SDLFunc("SDL_GetWindowBrightness", [_P(SDL_Window)], c_float),
    SDLFunc("SDL_GetWindowOpacity", [_P(SDL_Window), _P(c_float)], c_int, added='2.0.5'),
    SDLFunc("SDL_SetWindowOpacity", [_P(SDL_Window), c_float], c_int, added='2.0.5'),
    SDLFunc("SDL_SetWindowModalFor", [_P(SDL_Window), _P(SDL_Window)], c_int, added='2.0.5'),
    SDLFunc("SDL_SetWindowInputFocus", [_P(SDL_Window)], c_int, added='2.0.5'),
    SDLFunc("SDL_SetWindowGammaRamp", [_P(SDL_Window), _P(Uint16), _P(Uint16), _P(Uint16)], c_int),
    SDLFunc("SDL_GetWindowGammaRamp", [_P(SDL_Window), _P(Uint16), _P(Uint16), _P(Uint16)], c_int),
    SDLFunc("SDL_SetWindowHitTest", [_P(SDL_Window), SDL_HitTest, c_void_p], c_int, added='2.0.4'),
    SDLFunc("SDL_FlashWindow", [_P(SDL_Window), SDL_FlashOperation], c_int, added='2.0.16'),
    SDLFunc("SDL_DestroyWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_IsScreenSaverEnabled", None, SDL_bool),
    SDLFunc("SDL_EnableScreenSaver"),
    SDLFunc("SDL_DisableScreenSaver"),
    SDLFunc("SDL_GL_LoadLibrary", [c_char_p], c_int),
    SDLFunc("SDL_GL_GetProcAddress", [c_char_p], c_void_p),
    SDLFunc("SDL_GL_UnloadLibrary"),
    SDLFunc("SDL_GL_ExtensionSupported", [c_char_p], SDL_bool),
    SDLFunc("SDL_GL_ResetAttributes"),
    SDLFunc("SDL_GL_SetAttribute", [SDL_GLattr, c_int], c_int),
    SDLFunc("SDL_GL_GetAttribute", [SDL_GLattr, _P(c_int)], c_int),
    SDLFunc("SDL_GL_CreateContext", [_P(SDL_Window)], SDL_GLContext),
    SDLFunc("SDL_GL_MakeCurrent", [_P(SDL_Window), SDL_GLContext], c_int),
    SDLFunc("SDL_GL_GetCurrentWindow", None, _P(SDL_Window)),
    SDLFunc("SDL_GL_GetCurrentContext", None, SDL_GLContext),
    SDLFunc("SDL_GL_GetDrawableSize", [_P(SDL_Window), _P(c_int), _P(c_int)]),
    SDLFunc("SDL_GL_SetSwapInterval", [c_int], c_int),
    SDLFunc("SDL_GL_GetSwapInterval", None, c_int),
    SDLFunc("SDL_GL_SwapWindow", [_P(SDL_Window)]),
    SDLFunc("SDL_GL_DeleteContext", [SDL_GLContext]),
]
_ctypes = AttributeDict()
for f in _funcdefs:
    _ctypes[f.name] = _bind(f.name, f.args, f.returns, f.added)
    __all__.append(f.name) # Add all bound functions to module namespace


# Aliases for ctypes bindings

SDL_GetNumVideoDrivers = _ctypes["SDL_GetNumVideoDrivers"]
SDL_GetVideoDriver = _ctypes["SDL_GetVideoDriver"]
SDL_VideoInit = _ctypes["SDL_VideoInit"]
SDL_VideoQuit = _ctypes["SDL_VideoQuit"]
SDL_GetCurrentVideoDriver = _ctypes["SDL_GetCurrentVideoDriver"]
SDL_GetNumVideoDisplays = _ctypes["SDL_GetNumVideoDisplays"]
SDL_GetDisplayName = _ctypes["SDL_GetDisplayName"]
SDL_GetDisplayBounds = _ctypes["SDL_GetDisplayBounds"]
SDL_GetDisplayOrientation = _ctypes["SDL_GetDisplayOrientation"]
SDL_GetNumDisplayModes = _ctypes["SDL_GetNumDisplayModes"]
SDL_GetDisplayMode = _ctypes["SDL_GetDisplayMode"]
SDL_GetDesktopDisplayMode = _ctypes["SDL_GetDesktopDisplayMode"]
SDL_GetCurrentDisplayMode = _ctypes["SDL_GetCurrentDisplayMode"]
SDL_GetClosestDisplayMode = _ctypes["SDL_GetClosestDisplayMode"]
SDL_GetPointDisplayIndex = _ctypes["SDL_GetPointDisplayIndex"]
SDL_GetRectDisplayIndex = _ctypes["SDL_GetRectDisplayIndex"]
SDL_GetWindowDisplayIndex = _ctypes["SDL_GetWindowDisplayIndex"]
SDL_SetWindowDisplayMode = _ctypes["SDL_SetWindowDisplayMode"]
SDL_GetWindowDisplayMode = _ctypes["SDL_GetWindowDisplayMode"]
SDL_GetWindowICCProfile = _ctypes["SDL_GetWindowICCProfile"]
SDL_GetWindowPixelFormat = _ctypes["SDL_GetWindowPixelFormat"]
SDL_CreateWindow = _ctypes["SDL_CreateWindow"]
SDL_CreateWindowFrom = _ctypes["SDL_CreateWindowFrom"]
SDL_GetWindowID = _ctypes["SDL_GetWindowID"]
SDL_GetWindowFromID = _ctypes["SDL_GetWindowFromID"]
SDL_GetWindowFlags = _ctypes["SDL_GetWindowFlags"]
SDL_SetWindowTitle = _ctypes["SDL_SetWindowTitle"]
SDL_GetWindowTitle = _ctypes["SDL_GetWindowTitle"]
SDL_SetWindowIcon = _ctypes["SDL_SetWindowIcon"]
SDL_SetWindowData = _ctypes["SDL_SetWindowData"]
SDL_GetWindowData = _ctypes["SDL_GetWindowData"]
SDL_SetWindowPosition = _ctypes["SDL_SetWindowPosition"]
SDL_GetWindowPosition = _ctypes["SDL_GetWindowPosition"]
SDL_SetWindowSize = _ctypes["SDL_SetWindowSize"]
SDL_GetWindowSize = _ctypes["SDL_GetWindowSize"]
SDL_GetWindowSizeInPixels = _ctypes["SDL_GetWindowSizeInPixels"]
SDL_SetWindowMinimumSize = _ctypes["SDL_SetWindowMinimumSize"]
SDL_GetWindowMinimumSize = _ctypes["SDL_GetWindowMinimumSize"]
SDL_SetWindowMaximumSize = _ctypes["SDL_SetWindowMaximumSize"]
SDL_GetWindowMaximumSize = _ctypes["SDL_GetWindowMaximumSize"]
SDL_SetWindowBordered = _ctypes["SDL_SetWindowBordered"]
SDL_ShowWindow = _ctypes["SDL_ShowWindow"]
SDL_HideWindow = _ctypes["SDL_HideWindow"]
SDL_RaiseWindow = _ctypes["SDL_RaiseWindow"]
SDL_MaximizeWindow = _ctypes["SDL_MaximizeWindow"]
SDL_MinimizeWindow = _ctypes["SDL_MinimizeWindow"]
SDL_RestoreWindow = _ctypes["SDL_RestoreWindow"]
SDL_SetWindowFullscreen = _ctypes["SDL_SetWindowFullscreen"]
SDL_GetWindowSurface = _ctypes["SDL_GetWindowSurface"]
SDL_UpdateWindowSurface = _ctypes["SDL_UpdateWindowSurface"]
SDL_UpdateWindowSurfaceRects = _ctypes["SDL_UpdateWindowSurfaceRects"]
SDL_SetWindowGrab = _ctypes["SDL_SetWindowGrab"]
SDL_SetWindowKeyboardGrab = _ctypes["SDL_SetWindowKeyboardGrab"]
SDL_SetWindowMouseGrab = _ctypes["SDL_SetWindowMouseGrab"]
SDL_GetWindowGrab = _ctypes["SDL_GetWindowGrab"]
SDL_GetWindowKeyboardGrab = _ctypes["SDL_GetWindowKeyboardGrab"]
SDL_GetWindowMouseGrab = _ctypes["SDL_GetWindowMouseGrab"]
SDL_GetGrabbedWindow = _ctypes["SDL_GetGrabbedWindow"]
SDL_SetWindowMouseRect = _ctypes["SDL_SetWindowMouseRect"]
SDL_GetWindowMouseRect = _ctypes["SDL_GetWindowMouseRect"]
SDL_SetWindowBrightness = _ctypes["SDL_SetWindowBrightness"]
SDL_GetWindowBrightness = _ctypes["SDL_GetWindowBrightness"]
SDL_SetWindowGammaRamp = _ctypes["SDL_SetWindowGammaRamp"]
SDL_GetWindowGammaRamp = _ctypes["SDL_GetWindowGammaRamp"]
SDL_FlashWindow = _ctypes["SDL_FlashWindow"]
SDL_DestroyWindow = _ctypes["SDL_DestroyWindow"]
SDL_IsScreenSaverEnabled = _ctypes["SDL_IsScreenSaverEnabled"]
SDL_EnableScreenSaver = _ctypes["SDL_EnableScreenSaver"]
SDL_DisableScreenSaver = _ctypes["SDL_DisableScreenSaver"]
SDL_SetWindowHitTest = _ctypes["SDL_SetWindowHitTest"]
SDL_GetDisplayDPI = _ctypes["SDL_GetDisplayDPI"]
SDL_GetDisplayUsableBounds = _ctypes["SDL_GetDisplayUsableBounds"]
SDL_GetWindowBordersSize = _ctypes["SDL_GetWindowBordersSize"]
SDL_GetWindowOpacity = _ctypes["SDL_GetWindowOpacity"]
SDL_SetWindowOpacity = _ctypes["SDL_SetWindowOpacity"]
SDL_SetWindowInputFocus = _ctypes["SDL_SetWindowInputFocus"]
SDL_SetWindowModalFor = _ctypes["SDL_SetWindowModalFor"]
SDL_SetWindowResizable = _ctypes["SDL_SetWindowResizable"]
SDL_SetWindowAlwaysOnTop = _ctypes["SDL_SetWindowAlwaysOnTop"]

SDL_GL_LoadLibrary = _ctypes["SDL_GL_LoadLibrary"]
SDL_GL_GetProcAddress = _ctypes["SDL_GL_GetProcAddress"]
SDL_GL_UnloadLibrary = _ctypes["SDL_GL_UnloadLibrary"]
SDL_GL_ExtensionSupported = _ctypes["SDL_GL_ExtensionSupported"]
SDL_GL_SetAttribute = _ctypes["SDL_GL_SetAttribute"]
SDL_GL_GetAttribute = _ctypes["SDL_GL_GetAttribute"]
SDL_GL_CreateContext = _ctypes["SDL_GL_CreateContext"]
SDL_GL_GetCurrentWindow = _ctypes["SDL_GL_GetCurrentWindow"]
SDL_GL_MakeCurrent = _ctypes["SDL_GL_MakeCurrent"]
SDL_GL_GetCurrentContext = _ctypes["SDL_GL_GetCurrentContext"]
SDL_GL_SetSwapInterval = _ctypes["SDL_GL_SetSwapInterval"]
SDL_GL_GetSwapInterval = _ctypes["SDL_GL_GetSwapInterval"]
SDL_GL_SwapWindow = _ctypes["SDL_GL_SwapWindow"]
SDL_GL_DeleteContext = _ctypes["SDL_GL_DeleteContext"]
SDL_GL_GetDrawableSize = _ctypes["SDL_GL_GetDrawableSize"]
SDL_GL_ResetAttributes = _ctypes["SDL_GL_ResetAttributes"]
