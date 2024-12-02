from math import floor
from .compat import *

__all__ = ["Color", "is_rgb_color", "is_rgba_color", "argb_to_color", "ARGB",
           "rgba_to_color", "RGBA", "string_to_color", "convert_to_color",
           "COLOR"]


def _clip(val, _min, _max):
    return max(min(val, _max), _min)


class Color(object):
    """A class for working with and converting RGBA colors.
    
    This class represents the 4 RGBA color channels (red, green, blue, and
    alpha transparency) as integers from 0 to 255. It also provides methods
    for converting colors to alternative color spaces (e.g. HSV or CMY).

    ``Color`` objects support basic arithmetic operations (``+, -, *, /, %``),
    which operate on a per-channel basis. For example, the operation ::

       color = color1 + color2

    is the same as ::

       color = Color()
       color.r = min(color1.r + color2.r, 255)
       color.g = min(color1.g + color2.g, 255)

    All arithmetic operations guarantee that the channel values stay within
    the allowed range of [0, 255].

    Args:
        r (int, optional): An integer between 0 and 255 indicating the red
            level of the color. Defaults to 255.
        g (int, optional): An integer between 0 and 255 indicating the green
            level of the color. Defaults to 255.
        b (int, optional): An integer between 0 and 255 indicating the blue
            level of the color. Defaults to 255.
        a (int, optional): An integer between 0 and 255 indicating the alpha
            trasparency level of the color, with 0 being fully transparent and
            255 being fully opaque. Defaults to 255.

    """
    # NOTE: should this use floats internally for better precision?
    def __init__(self, r=255, g=255, b=255, a=255):
        for val in (r, g, b, a):
            self._verify_rgba_value(val)
        self._r = float(int(r))
        self._g = float(int(g))
        self._b = float(int(b))
        self._a = float(int(a))

    def _verify_rgba_value(self, val):
        """Verifies that the input is a valid uint8 RGBA value."""
        e = "All RGBA color values must be integers between 0 and 255 (got {0})"
        try:
            float(val)
        except (ValueError, TypeError):
            raise TypeError(e.format(val))
        if val < 0 or val > 255:
            raise ValueError(e.format(val))

    def __repr__(self):
        cols = [self.r, self.g, self.b, self.a]
        return "Color(r={0}, g={1}, b={2}, a={3})".format(*cols)

    def __copy__(self):
        return Color(self.r, self.g, self.b, self.a)

    def __eq__(self, color):
        return self.r == color.r and self.g == color.g and \
            self.b == color.b and self.a == color.a

    def __ne__(self, color):
        return self.r != color.r or self.g != color.g or \
            self.b != color.b or self.a != color.a

    def __int__(self):
        return (self.r << 24 | self.g << 16 | self.b << 8 | self.a)

    def __long__(self):
        return (self.r << 24 | self.g << 16 | self.b << 8 | self.a)

    def __float__(self):
        return (self.r << 24 | self.g << 16 | self.b << 8 | self.a) * 1.0

    def __index__(self):
        return (self.r << 24 | self.g << 16 | self.b << 8 | self.a)

    def __oct__(self):
        val = (self.r << 24 | self.g << 16 | self.b << 8 | self.a)
        return oct(val)

    def __hex__(self):
        val = (self.r << 24 | self.g << 16 | self.b << 8 | self.a)
        return hex(val)

    def __invert__(self):
        vals = (255 - self.r, 255 - self.g, 255 - self.b, 255 - self.a)
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __mod__(self, color):
        vals = (self.r % color.r, self.g % color.g, self.b % color.b,
                self.a % color.a)
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __div__(self, color):
        vals = [0, 0, 0, 0]
        if color._r != 0:
            vals[0] = (self._r / color._r)
        if color._g != 0:
            vals[1] = (self._g / color._g)
        if color._b != 0:
            vals[2] = (self._b / color._b)
        if color._a != 0:
            vals[3] = (self._a / color._a)
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __truediv__(self, color):
        vals = [0, 0, 0, 0]
        if color._r != 0:
            vals[0] = (self._r / color._r)
        if color._g != 0:
            vals[1] = (self._g / color._g)
        if color._b != 0:
            vals[2] = (self._b / color._b)
        if color._a != 0:
            vals[3] = (self._a / color._a)
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __mul__(self, color):
        vals = (
            min(self._r * color._r, 255),
            min(self._g * color._g, 255),
            min(self._b * color._b, 255),
            min(self._a * color._a, 255)
        )
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __sub__(self, color):
        vals = (max(self.r - color.r, 0), max(self.g - color.g, 0),
                max(self.b - color.b, 0), max(self.a - color.a, 0))
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __add__(self, color):
        vals = (min(self.r + color.r, 255), min(self.g + color.g, 255),
                min(self.b + color.b, 255), min(self.a + color.a, 255))
        return Color(vals[0], vals[1], vals[2], vals[3])

    def __len__(self):
        return 4

    def __getitem__(self, index):
        return (self.r, self.g, self.b, self.a)[index]

    def __setitem__(self, index, val):
        tmp = [self.r, self.g, self.b, self.a]
        tmp[index] = val
        self.r = tmp[0]
        self.g = tmp[1]
        self.b = tmp[2]
        self.a = tmp[3]

    @property
    def r(self):
        """"int: The 8-bit RGBA red level for the color."""
        return int(round(self._r))

    @r.setter
    def r(self, val):
        self._verify_rgba_value(val)
        self._r = float(val)

    @property
    def g(self):
        """"int: The 8-bit RGBA green level for the color."""
        return int(round(self._g))

    @g.setter
    def g(self, val):
        self._verify_rgba_value(val)
        self._g = float(val)

    @property
    def b(self):
        """"int: The 8-bit RGBA blue level for the color."""
        return int(round(self._b))

    @b.setter
    def b(self, val):
        self._verify_rgba_value(val)
        self._b = float(val)

    @property
    def a(self):
        """"int: The 8-bit RGBA alpha transparency level for the color."""
        return int(round(self._a))

    @a.setter
    def a(self, val):
        self._verify_rgba_value(val)
        self._a = float(val)

    @property
    def hsva(self):
        """tuple: A representation of the color in HSV(A) color space.
        
        The HSVA color space represents colors in terms of hue, saturation,
        value (brightness), and alpha (transparency). Hue is represented as a
        value on color wheel between 0 and 360, whereas saturation, brightness,
        and alpha are all represented as values from 0 to 100.

        Note that due to rounding errors, this may not return the exact HSVA
        values for the given color.
        
        """
        rn = self._r / 255.0
        gn = self._g / 255.0
        bn = self._b / 255.0
        an = self._a / 255.0

        maxv = max(rn, gn, bn)
        minv = min(rn, gn, bn)
        diff = maxv - minv

        h = 0
        s = 0
        v = maxv * 100.0
        a = an * 100.0

        if maxv == minv:
            return(h, s, v, a)
        s = 100.0 * (maxv - minv) / maxv

        if maxv == rn:
            h = (60 * (gn - bn) / diff) % 360.0
        elif maxv == gn:
            h = (60 * (bn - rn) / diff) + 120.0
        else:
            h = (60 * (rn - gn) / diff) + 240.0
        if h < 0:
            h += 360.0

        return (h, s, v, a)

    @hsva.setter
    def hsva(self, value):
        h, s, v, a = value
        for x in (h, s, v, a):
            if type(x) not in(int, long, float):
                raise TypeError("HSVA values must be of type float")
        if not (0 <= s <= 100) or not (0 <= v <= 100) or \
                not (0 <= a <= 100) or not (0 <= h <= 360):
            raise ValueError("invalid HSVA value")

        hi = int(floor(h / 60.0))
        if hi > 5:
            raise OverflowError("invalid HSVA value")

        self.a = int((a / 100.0) * 255)
        s /= 100.0
        v /= 100.0
        f = (h / 60.0) - hi
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        rgb_map = [
            (v, t, p), # if hi == 0
            (q, v, p), # if hi == 1
            (p, v, t), # if hi == 2
            (p, q, v), # if hi == 3
            (t, p, v), # if hi == 4
            (v, p, q)  # if hi == 5
        ]
        vals = [_clip(n * 255.0, 0.0, 255.0) for n in rgb_map[hi]]
        self.r, self.g, self.b = vals

    @property
    def hsla(self):
        """tuple: A representation of the color in HSL(A) color space.
        
        The HSLA color space represents colors in terms of hue, saturation,
        lightness, and alpha (transparency). Hue is represented as a
        value on color wheel between 0 and 360, whereas saturation, lightness,
        and alpha are all represented as values from 0 to 100.

        Note that due to rounding errors, this may not return the exact HSLA
        values for the given color.
        
        """
        rn = self._r / 255.0
        gn = self._g / 255.0
        bn = self._b / 255.0
        an = self._a / 255.0

        maxv = max(rn, gn, bn)
        minv = min(rn, gn, bn)
        diff = maxv - minv

        h = 0
        s = 0
        l = 50.0 * (maxv + minv)
        a = an * 100.0

        if maxv == minv:
            return (h, s, l, a)

        if l <= 50.0:
            s = diff / (maxv + minv) * 100.0
        else:
            s = diff / (2.0 - maxv - minv) * 100.0

        if maxv == rn:
            h = (60 * (gn - bn) / diff) % 360.0
        elif maxv == gn:
            h = (60 * (bn - rn) / diff) + 120.0
        else:
            h = (60 * (rn - gn) / diff) + 240.0
        if h < 0:
            h += 360.0

        return (h, s, l, a)

    @hsla.setter
    def hsla(self, value):
        h, s, l, a = value
        for x in (h, s, l, a):
            if type(x) not in (int, long, float):
                raise TypeError("HSLA values must be of type float")
        if not (0 <= s <= 100) or not (0 <= l <= 100) or \
                not (0 <= a <= 100) or not (0 <= h <= 360):
            raise ValueError("invalid HSLA value")

        self.a = int((a / 100.0) * 255)
        s /= 100.0
        l /= 100.0
        if s == 0:
            self.r = l * 255.0
            self.g = l * 255.0
            self.b = l * 255.0
            return

        q = 0
        if l < 0.5:
            q = l * (1 + s)
        else:
            q = l + s - (l * s)
        p = 2 * l - q

        ht = h / 360.0
        vals = []
        for h in [ht + (1.0 / 3.0), ht, ht - (1.0 / 3.0)]:
            if h < 0:
                h += 1
            elif h > 1:
                h -= 1
            if h < (1.0 / 6.0):
                val = (p + ((q - p) * 6 * h))
            elif h < 0.5:
                val = q
            elif h < (2.0 / 3.0):
                val = (p + ((q - p) * 6 * (2.0 / 3.0 - h)))
            else:
                val = p
            vals.append(_clip(val * 255.0, 0.0, 255.0))

        self.r, self.g, self.b = vals

    @property
    def i1i2i3(self):
        """tuple: A representation of the color in I1I2I3 color space.
        
        The I1I2I3 color space represents colors in terms of a color-independent
        intensity level (I1) and two chromatic channels (I2 and I3), with the
        aim of minimizing correlations between its channels for natural images.
        Intensity (I1) is represented as a float between 0.0 and 1.0, whereas
        the color channels (I2 and I3) are represented as floats between
        -0.5 and 0.5, inclusive.

        Note that due to rounding errors, this may not return the exact I1I2I3
        values for the given color.
        
        """
        rn = self._r / 255.0
        gn = self._g / 255.0
        bn = self._b / 255.0

        i1 = _clip((rn + gn + bn) / 3.0, 0.0, 1.0)
        i2 = _clip((rn - bn) / 2.0, -0.5, 0.5)
        i3 = _clip((2 * gn - rn - bn) / 4.0, -0.5, 0.5)

        return (i1, i2, i3)

    @i1i2i3.setter
    def i1i2i3(self, value):
        i1, i2, i3 = value
        for x in (i1, i2, i3):
            if type(x) not in (int, long, float):
                raise TypeError("I1I2I3 values must be of type float")
        if not (0 <= i1 <= 1) or not (-0.5 <= i2 <= 0.5) or \
                not (-0.5 <= i3 <= 0.5):
            raise ValueError("invalid I1I2I3 value")

        ab = i1 - i2 - 2 * i3 / 3.0
        ar = 2 * i2 + ab
        ag = 3 * i1 - ar - ab

        self.r = _clip(ar * 255, 0.0, 255.0)
        self.g = _clip(ag * 255, 0.0, 255.0)
        self.b = _clip(ab * 255, 0.0, 255.0)

    @property
    def cmy(self):
        """tuple: A representation of the color in CMY color space.

        The CMY color space is the inverse of the RGB color space, and
        represents colors in subtractive amounts of Cyan, Magenta, and Yellow.
        All three values are represented as floats between 0.0 and 1.0.

        """
        return (1.0 - self._r / 255.0,
                1.0 - self._g / 255.0,
                1.0 - self._b / 255.0)

    @cmy.setter
    def cmy(self, value):
        c, m, y = value
        if (c < 0 or c > 1) or (m < 0 or m > 1) or (y < 0 or y > 1):
            raise ValueError("invalid CMY value")
        self._r = (1.0 - c) * 255
        self._g = (1.0 - m) * 255
        self._b = (1.0 - y) * 255

    def normalize(self):
        """Returns the RGBA values as floats between 0 and 1.

        Returns:
            tuple: The (r, g, b, a) values of the color as normalized floats.

        """
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a / 255.0)


def is_rgb_color(v):
    """Checks whether a value be converted to an RGB color.

    Args:
        v: The value to try and interpret as an RGB color.
    
    Returns:
        bool: True if the value can be interpreted as an RGB color, otherwise
        False.

    """
    if hasattr(v, "r") and hasattr(v, "g") and hasattr(v, "b"):
        v = [v.r, v.g, v.b]
    if not isiterable(v) or len(v) < 3:
        return False
    try:
        return all([0 <= int(x) <= 255 for x in v[:3]])
    except (TypeError, ValueError):
        return False


# NOTE: Add support for trying to parse strs and ints using below functions?
def is_rgba_color(v):
    """Checks whether a value be converted to an RGBA color.

    Args:
        v: The value to try and interpret as an RGBA color.
    
    Returns:
        bool: True if the value can be interpreted as an RGBA color, otherwise
        False.

    """
    rgb = is_rgb_color(v)
    if not rgb:
        return False

    try:
        if hasattr(v, "a") and 0 <= int(v.a) <= 255:
            return True
        if len(v) >= 4 and 0 <= int(v[3]) <= 255:
            return True
        return False
    except (TypeError, ValueError):
        return False


# TODO: Add type-checking/exceptions?
def argb_to_color(v):
    """Converts a 32-bit ARGB integer value to a :obj:`sdl2.ext.Color`.

    Args:
        v (int): An integer representing a color in ARGB format.

    Returns:
        :obj:`sdl2.ext.Color`: An object representing the given color.

    """
    v = long(v)

    a = ((v & 0xFF000000) >> 24)
    r = ((v & 0x00FF0000) >> 16)
    g = ((v & 0x0000FF00) >> 8)
    b = ((v & 0x000000FF))
    return Color(r, g, b, a)


ARGB = argb_to_color


def rgba_to_color(v):
    """Converts a 32-bit RGBA integer value to a :obj:`sdl2.ext.Color`.

    Args:
        v (int): An integer representing a color in RGBA format.

    Returns:
        :obj:`sdl2.ext.Color`: An object representing the given color.

    """
    v = long(v)

    r = ((v & 0xFF000000) >> 24)
    g = ((v & 0x00FF0000) >> 16)
    b = ((v & 0x0000FF00) >> 8)
    a = ((v & 0x000000FF))
    return Color(r, g, b, a)


RGBA = rgba_to_color


def string_to_color(s):
    """Converts a hex color string to a Color value.

    Hex colors can be specified in any of the following formats:

    * #RGB
    * #RGBA
    * #RRGGBB
    * #RRGGBBAA
    * 0xRGB
    * 0xRGBA
    * 0xRRGGBB
    * 0xRRGGBBAA

    Args:
        s (str): A valid hex color in string format.

    Returns:
        :obj:`sdl2.ext.Color`: An object representing the given color.

    """
    if type(s) is not str:
        raise TypeError("s must be a string")

    if not(s.startswith("#") or s.startswith("0x")):
        raise ValueError("value is not Color-compatible")

    if s.startswith("#"):
        s = s[1:]
    else:
        s = s[2:]

    r, g, b, a = 255, 255, 255, 255
    if len(s) in (3, 4):
        # A triple/quadruple in the form #ead == #eeaadd
        r = int(s[0], 16) << 4 | int(s[0], 16)
        g = int(s[1], 16) << 4 | int(s[1], 16)
        b = int(s[2], 16) << 4 | int(s[2], 16)
        if len(s) == 4:
            a = int(s[3], 16) << 4 | int(s[3], 16)
    elif len(s) in (6, 8):
        r = int(s[0], 16) << 4 | int(s[1], 16)
        g = int(s[2], 16) << 4 | int(s[3], 16)
        b = int(s[4], 16) << 4 | int(s[5], 16)
        if len(s) == 8:
            a = int(s[6], 16) << 4 | int(s[7], 16)
    else:
        raise ValueError("value is not Color-compatible")
    return Color(r, g, b, a)


def convert_to_color(v):
    """Tries to convert an arbitrary object to a :obj:`sdl2.ext.Color`.

    If an integer is provided, it is assumed to be in ARGB layout.

    Args:
        v: An arbitrary object type representing a color.

    Returns:
        :obj:`sdl2.ext.Color`: An object representing the given color.

    Raises:
        ValueError: If the value could not be converted successfully.

    """
    if isinstance(v, Color):
        return v

    if type(v) is str:
        return string_to_color(v)
    if type(v) in (int, long):
        return argb_to_color(v)

    r, g, b, a = 0, 0, 0, 0
    if hasattr(v, "r") and hasattr(v, "g") and hasattr(v, "b"):
        if 0 <= int(v.r) <= 255 and 0 <= int(v.g) <= 255 and \
                0 <= v.b <= 255:
            r = int(v.r)
            g = int(v.g)
            b = int(v.b)
            if hasattr(v, "a") and 0 <= int(v.a) <= 255:
                a = int(v.a)
        else:
            raise ValueError("value is not Color-compatible")
        return Color(r, g, b, a)

    try:
        length = len(v)
    except:
        raise ValueError("value is not Color-compatible")
    if length < 3:
        raise ValueError("value is not Color-compatible")
    if 0 <= int(v[0]) <= 255 and 0 <= int(v[1]) <= 255 and \
            0 <= int(v[2]) <= 255:
        r = int(v[0])
        g = int(v[1])
        b = int(v[2])
        if length >= 4 and 0 <= int(v[3]) <= 255:
            a = int(v[3])
        return Color(r, g, b, a)

    raise ValueError("value is not Color-compatible")


COLOR = convert_to_color
