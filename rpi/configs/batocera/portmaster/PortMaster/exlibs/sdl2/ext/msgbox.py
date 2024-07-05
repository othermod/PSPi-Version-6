from ctypes import byref, c_int
from .color import Color
from .compat import isiterable, utf8
from .err import raise_sdl_err
from .window import Window
from .. import dll, SDL_PumpEvents, SDL_Window
from .. import messagebox as mb

__all__ = [
    "MessageBoxTheme", "MessageBox", "show_messagebox", "show_alert"
]

class MessageBoxTheme(object):
    """Initializes a color scheme for use with :obj:`MessageBox` objects.

    This is used to define the background, text, and various button colors
    to use when presenting dialog boxes to users. All colors must be defined
    as either :obj:`sdl2.ext.Color` objects or 8-bit ``(r, g, b)`` tuples.

    .. note::
       SDL2 only supports MessageBox themes on a few platforms, including
       Linux/BSD (if using X11) and Haiku. MessageBox themes will have no effect
       on Windows, macOS, or Linux if using Wayland.

    Args:
        bg (:obj:`~sdl2.ext.Color`, tuple, optional): The color to use for the
            background of the dialog box. Defaults to ``(56, 54, 53)``.
        text (:obj:`~sdl2.ext.Color`, tuple, optional): The color to use for the
            text of the dialog box. Defaults to ``(209, 207, 205)``.
        btn (:obj:`~sdl2.ext.Color`, tuple, optional): The color to use for the
            backgrounds of buttons. Defaults to ``(140, 135, 129)``.
        btn_border (:obj:`~sdl2.ext.Color`, tuple, optional): The color to use
            for the borders of buttons. Defaults to ``(105, 102, 99)``.
        btn_selected (:obj:`~sdl2.ext.Color`, tuple, optional): The color to use
            for selected buttons. Defaults to ``(205, 202, 53)``.

    """
    def __init__(
        self, bg=None, text=None, btn=None, btn_border=None, btn_selected=None
    ):
        # NOTE: Default colors taken from SDL_x11messagebox.c
        self._theme = [
            (56, 54, 53),     # Background color
            (209, 207, 205),  # Text color
            (140, 135, 129),  # Button border color
            (105, 102, 99),   # Button background color
            (205, 202, 53)    # Selected button color
        ]
        # Update default theme colors based on provided values
        elements = [bg, text, btn_border, btn, btn_selected]
        for i in range(len(elements)):
            if elements[i] is not None:
                self._theme[i] = self._validate_color(elements[i])

    def _validate_color(self, col):
        if not isinstance(col, Color):
            if not isiterable(col) or len(col) != 3:
                e = "MessageBox colors must be specified as (r, g, b) tuples."
                raise TypeError(e)
            for val in col:
                if int(val) != float(val):
                    e = "All RGB values must be integers between 0 and 255."
                    raise ValueError(e)
            col = Color(col[0], col[1], col[2])
        return (col.r, col.g, col.b)

    def _get_theme(self):
        sdl_colors = []
        for col in self._theme:
            sdl_colors.append(mb.SDL_MessageBoxColor(*col))
        col_array = (mb.SDL_MessageBoxColor * 5)(*sdl_colors)
        return mb.SDL_MessageBoxColorScheme(col_array)


class MessageBox(object):
    """Creates a prototype for a dialog box that can be presented to the user.

    The `MessageBox` class is for designing a dialog box in the style of the
    system's window manager, containing a title, a message to present, and
    one or more response buttons.

    Args:
        title (str): The title to use for the dialog box. All UTF-8 characters
            are supported.
        msg (str): The main body of text to display in the dialog box. All UTF-8
            characters are supported.
        buttons (list): A list of strings, containing the labels of the buttons
            to place at the bottom of the dialog box (e.g. ``["No", "Yes"]``).
            Buttons will be placed in left-to-right order.
        default (str, optional): The label of the button to highlight as the
            default option (e.g. ``"Yes"``). Must match one of the labels in
            ``buttons``. This option will be accepted if the Return/Enter key
            is pressed on the keyboard.
        msgtype (str, optional): The type of dialog box to create, if supported
            by the system. On most window managers, this changes the icon used
            in the dialog box. Must be one of 'error', 'warning', or 'info', or
            None (the default).
        theme (:obj:`MessageBoxTheme`, optional): The color scheme to use for
            the dialog box, if supported by the window manager. Defaults to the
            system default theme.

    """
    def __init__(self, title, msg, buttons, default=None, msgtype=None, theme=None):
        self._title = utf8(title).encode('utf-8')
        self._text = utf8(msg).encode('utf-8')
        self._validate_buttons(buttons)
        self._buttons = buttons
        self._sdlbuttons = self._init_buttons(buttons, default)
        self._type = self._set_msgtype(msgtype) if msgtype else 0
        self._theme = theme._get_theme() if theme else None

    def _set_msgtype(self, msgtype):
        _flagmap = {
            'error': mb.SDL_MESSAGEBOX_ERROR,
            'warning': mb.SDL_MESSAGEBOX_WARNING,
            'info': mb.SDL_MESSAGEBOX_INFORMATION,
        }
        if msgtype.lower() not in _flagmap.keys():
            raise ValueError(
                "MessageBox type must be 'error', 'warning', 'info', or None."
            )
        return _flagmap[msgtype]

    def _validate_buttons(self, buttons):
        if not isiterable(buttons):
            raise TypeError("Buttons must be provided as a list.")
        elif len(buttons) == 0:
            raise ValueError("MessageBox must have at least one button.")

    def _init_buttons(self, buttons, default):
        default_flag = mb.SDL_MESSAGEBOX_BUTTON_RETURNKEY_DEFAULT
        buttonset = []
        for i in range(len(buttons)):
            b = mb.SDL_MessageBoxButtonData(
                flags = (default_flag if buttons[i] == default else 0),
                buttonid = i,
                text = utf8(buttons[i]).encode('utf-8'),
            )
            buttonset.append(b)
        return (mb.SDL_MessageBoxButtonData * len(buttons))(*buttonset)

    def _get_window_pointer(self, win):
        if isinstance(win, Window):
            win = win.window
        if isinstance(win, SDL_Window):
            win = dll.get_pointer(win)
        if hasattr(win, "contents") and isinstance(win.contents, SDL_Window):
            return win
        else:
            e = "'window' must be a Window or SDL_Window object (got {0})"
            raise ValueError(e.format(str(type(win))))

    def _get_msgbox(self, window=None):
        if window:
            window = self._get_window_pointer(window)
        return mb.SDL_MessageBoxData(
            flags = self._type | mb.SDL_MESSAGEBOX_BUTTONS_RIGHT_TO_LEFT,
            window = window,
            title = self._title,
            message = self._text,
            numbuttons = len(self._buttons),
            buttons = self._sdlbuttons,
            colorScheme = dll.get_pointer(self._theme) if self._theme else None,
        )
        

def show_messagebox(msgbox, window=None):
    """Displays a dialog box to the user and waits for a response.

    By default message boxes are presented independently of any window, but
    they can optionally be attached explicitly to a specific SDL window. This
    prevents that window from regaining focus until a response to the dialog
    box is made.

    Args:
        msgbox (:obj:`~sdl2.ext.MessageBox`): The dialog box to display
            on-screen.
        window (:obj:`~sdl2.SDL_Window`, :obj:`~sdl2.ext.Window`, optional): The
            window to associate with the dialog box. Defaults to None.

    Returns:
        str: The label of the button selected by the user.

    """
    resp = c_int(-1)
    ret = mb.SDL_ShowMessageBox(
        msgbox._get_msgbox(window),
        byref(resp)
    )
    SDL_PumpEvents()
    if ret == 0:
        return msgbox._buttons[resp.value]
    else:
        raise_sdl_err("displaying the message box")


def show_alert(title, msg, msgtype=None, window=None):
    """Displays a simple alert to the user and waits for a response.

    This function is a simplified version of :func:`show_messagebox` for cases
    where only one response button ("OK") is needed and a custom color scheme
    is not necessary.

    By default message boxes are presented independently of any window, but
    they can optionally be attached explicitly to a specific SDL window. This
    prevents that window from regaining focus until a response to the dialog
    box is made.

    Args:
        msgbox (:obj:`~sdl2.ext.MessageBox`): The dialog box to display
            on-screen.
        window (:obj:`~sdl2.SDL_Window`, :obj:`~sdl2.ext.Window`, optional): The
            window to associate with the dialog box. Defaults to ``None``.

    """
    box = MessageBox(title, msg, ["OK"], msgtype=msgtype)
    if window:
        window = box._get_window_pointer(window)
    ret = mb.SDL_ShowSimpleMessageBox(
        box._type,
        box._title,
        box._text,
        window
    )
    SDL_PumpEvents()
    if ret < 0:
        raise_sdl_err("displaying the message box")
