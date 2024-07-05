from .. import error

__all__ = ["SDLError", "raise_sdl_err"]


class SDLError(Exception):
    """A custom exception class for SDL2-specific errors.
    
    Args:
        msg (str, optional): The error message for the exception. If not
            provided, the current SDL error (if any) will be retrieved using
            `:func:~sdl2.SDL_GetError`.
    """

    def __init__(self, msg=None):
        super(SDLError, self).__init__()
        self.msg = msg
        if not msg:
            self.msg = error.SDL_GetError()
            error.SDL_ClearError()

    def __str__(self):
        return repr(self.msg)


def raise_sdl_err(desc=None):
    """Raises an exception for an internal SDL error.
    
    The format of the exception message depends on whether a description is
    provided and whether `:func:~sdl2.SDL_GetError` returns an error string.
    If a description is given, it will be appended after the default text
    ``Error encountered``. If SDL has set an error string, it will be appended
    to the end of the message following a colon (clearing the error in the
    process).
    
    For example, if ``SDL_GetError() == b"unsupported pixel format"`` and the
    function is called as ``raise_sdl_err("creating the surface")``, the
    resulting exception message will be "Error encountered creating the surface:
    unsupported pixel format".

    Args:
        desc (str. optional): A description of what SDL was trying to do when
            the error occurred. Will be placed after the text "Error encountered"
            in the exception message if provided.

    Raises:
        :exc:`~SDLError`: An exception explaining the most recent SDL error.

    """
    errmsg = error.SDL_GetError().decode('utf-8')
    error.SDL_ClearError()
    e = "Error encountered"
    if desc:
        e += " " + desc
    if len(errmsg):
        e += ": {0}".format(errmsg)
    raise SDLError(e)
