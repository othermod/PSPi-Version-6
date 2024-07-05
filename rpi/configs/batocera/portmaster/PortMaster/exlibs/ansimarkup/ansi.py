from colorama.ansi import AnsiCodes
from colorama import Fore, Back, Style


class AnsiExtendedStyle(AnsiCodes):
    ITALIC    = 3
    UNDERLINE = 4
    BLINK     = 5
    REVERSE   = 7
    STRIKE    = 8
    HIDE      = 9


ExtendedStyle = AnsiExtendedStyle()
