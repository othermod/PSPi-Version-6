
import os
import sys

import colorama
from ansimarkup import AnsiMarkup, parse as ansiparse


am = AnsiMarkup(tags={
    'warn': ansiparse('<b><y>'),
    'error': ansiparse('<b><r>'),
    'info': ansiparse('<b><e>'),
    'debug': ansiparse('<b><m>'),
    })


__colorama = None
__output_fh = None


def to_str(data):
    if isinstance(data, str):
        return data

    return str(data)


def in_terminal():
    """
    Are we in a terminal?
    """
    return os.isatty(sys.stdout.fileno()) and os.isatty(sys.stdin.fileno())


def do_cprint_output(file_handle):
    global __output_fh

    __output_fh = file_handle


def do_color(mode=None):
    global __colorama

    if mode is None:
        mode = in_terminal()

    if mode is True:
        if __colorama is None or __colorama is False:
            colorama.init(strip=False)
            __colorama = True

    elif mode is False:
        if __colorama is True:
            colorama.init(strip=True)
        __colorama = False


def cprint(*args, **kwargs):
    global __colorama
    global __output_fh
    if __colorama is None:
        do_color()

    if __output_fh is not None:
        color_func = am.strip
        kwargs.setdefault('file', __output_fh)
    elif 'file' in kwargs:
        color_func = am.strip
    elif __colorama:
        color_func = am.parse
    else:
        color_func = am.strip

    print(
        *(
            color_func(to_str(arg))
            for arg in args),
        **kwargs)

def cstrip(arg):
    return am.strip(to_str(arg))

__all__ = (
    'cprint',
    'cstrip',
    'do_color',
    'in_terminal',
    )
