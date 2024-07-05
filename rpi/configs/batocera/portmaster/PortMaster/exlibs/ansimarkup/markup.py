from __future__ import print_function

import re

from colorama import Style

from .tags import style, background, foreground, all_tags
from .compat import builtins


class AnsiMarkupError(Exception):
    pass

class MismatchedTag(AnsiMarkupError):
    pass

class UnbalancedTag(AnsiMarkupError):
    pass


class AnsiMarkup:
    '''
    Produce colored terminal text with a tag-based markup.
    '''

    def __init__(self, tags=None, always_reset=False, strict=False, tag_sep='<>', ansistring_cls=None):
        '''
        Arguments
        ---------
        tags: dict
           User-supplied tags, which are a mapping of tag names to the strings
           they will be substituted with.
        always_reset: bool
           Whether or not ``parse()`` should always end strings with a reset code.
        strict: bool
           Whether or not ``parse()`` should raise an error for missing closing tags.
        tag_sep: str
           The opening and closing characters of each tag (e.g. ``<>``, ``{}``).
        ansistring_cls: type
           Class to use in ``ansistring()`` method.
        '''
        self.user_tags = tags if tags else {}
        self.always_reset = always_reset
        self.strict = strict
        self.tag_sep = tag_sep
        self.ansistring_cls = ansistring_cls if ansistring_cls else AnsiMarkupString

        self.re_tag = self.compile_tag_regex(tag_sep)

    def parse(self, text):
        '''Return a string with markup tags converted to ansi-escape sequences.'''
        tags, results = [], []

        text = self.re_tag.sub(lambda m: self.sub_tag(m, tags, results), text)

        if self.strict and tags:
            markup = "%s%s%s" % (self.tag_sep[0], tags.pop(0), self.tag_sep[1])
            raise MismatchedTag('opening tag "%s" has no corresponding closing tag' % markup)

        if self.always_reset:
            if not text.endswith(Style.RESET_ALL):
                text += Style.RESET_ALL

        return text

    def ansiprint(self, *args, **kwargs):
        '''Wrapper around builtins.print() that runs parse() on all arguments first.'''
        args = (self.parse(str(i)) for i in args)
        builtins.print(*args, **kwargs)

    def strip(self, text):
        '''Return string with markup tags removed.'''
        tags, results = [], []
        return self.re_tag.sub(lambda m: self.clear_tag(m, tags, results), text)

    def ansistring(self, markup):
        return self.ansistring_cls(self, markup)

    def __call__(self, text):
        return self.parse(text)

    def sub_tag(self, match, tag_list, res_list):
        markup, tag = match.group(0), match.group(1)
        closing = markup[1] == '/'
        res = None

        # Early exit if the closing tag matches the last known opening tag.
        if closing and tag_list and tag_list[-1] == tag:
            tag_list.pop()
            res_list.pop()
            return Style.RESET_ALL + ''.join(res_list)

        # User-defined tags take preference over all other.
        if tag in self.user_tags:
            utag = self.user_tags[tag]
            res = utag() if callable(utag) else utag

        # Substitute on a direct match.
        elif tag in all_tags:
            res = all_tags[tag]

        # An alternative syntax for setting the color (e.g. <fg red>, <bg red>).
        elif tag.startswith('fg ') or tag.startswith('bg '):
            st, color = tag[:2], tag[3:]
            code = '38' if st == 'fg' else '48'

            if st == 'fg' and color in foreground:
                res = foreground[color]
            elif st == 'bg' and color.islower() and color.upper() in background:
                res = background[color.upper()]
            elif color.isdigit() and int(color) <= 255:
                res = '\033[%s;5;%sm' % (code, color)
            elif re.match(r'#(?:[a-fA-F0-9]{3}){1,2}$', color):
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color *= 2
                res = '\033[%s;2;%s;%s;%sm' % ((code,) + hex_to_rgb(hex_color))
            elif color.count(',') == 2:
                colors = tuple(color.split(','))
                if all(x.isdigit() and int(x) <= 255 for x in colors):
                    res = '\033[%s;2;%s;%s;%sm' % ((code,) + colors)

        # Shorthand formats (e.g. <red,blue>, <bold,red,blue>).
        elif ',' in tag:
            el_count = tag.count(',')

            if el_count == 1:
                fg, bg = tag.split(',')
                if fg in foreground and bg.islower() and bg.upper() in background:
                    res = foreground[fg] + background[bg.upper()]

            elif el_count == 2:
                st, fg, bg = tag.split(',')
                if st in style and (fg != '' or bg != ''):
                    if fg == '' or fg in foreground:
                        if bg == '' or (bg.islower() and bg.upper() in background):
                            res = style[st] + foreground.get(fg, '') + background.get(bg.upper(), '')

        # If nothing matches, return the full tag (i.e. <unknown>text</...>).
        if res is None:
            return markup

        # If closing tag is known, but did not early exit, something is wrong.
        if closing:
            if tag in tag_list:
                raise UnbalancedTag('closing tag "%s" violates nesting rules.' % markup)
            else:
                raise MismatchedTag('closing tag "%s" has no corresponding opening tag' % markup)

        tag_list.append(tag)
        res_list.append(res)

        return res

    def clear_tag(self, match, tag_list, res_list):
        pre_length = len(tag_list)
        try:
            self.sub_tag(match, tag_list, res_list)

            # If list did not change, the tag is unknown
            if len(tag_list) == pre_length:
                return match.group(0)

            # Otherwise, tag matched so remove it
            else:
                return ''

        # Tag matched but is invalid, remove it anyway
        except (UnbalancedTag, MismatchedTag):
            return ''

    def compile_tag_regex(self, tag_sep):
        # Optimize the default:
        if tag_sep == '<>':
            tag_regex = re.compile(r'</?([^<>]+)>')
            return tag_regex

        if len(tag_sep) != 2:
            raise ValueError('tag_sep needs to have exactly two elements (e.g. "<>")')

        if tag_sep[0] == tag_sep[1]:
            raise ValueError('opening and closing characters cannot be the same')

        tag_regex = r'{0}/?([^{0}{1}]+){1}'.format(tag_sep[0], tag_sep[1])
        return re.compile(tag_regex)


class AnsiMarkupString(str):
    '''
    A string containing the original markup, the formatted string and the
    string with tags stripped off. Example usage::

      >>> t = AnsiMarkup().string('<b>abc</b>')
      >>> repr(t)
      <b>abc</b>

      >>> print(t)
      abc  # in bold

      >>> len(t)
      3

      >>> len(AnsiMarkup().parse('<b>abc</b'))
      11

      >>> t.delta
      8

    '''

    def __new__(cls, am, markup):
        parsed = am.parse(markup)

        new_str = str.__new__(cls, parsed)
        new_str.markup = markup
        new_str.stripped = am.strip(markup)

        # The difference in length between the formatted string and the string
        # with markup tags stripped off.
        new_str.delta = len(parsed) - len(new_str.stripped)

        return new_str

    def __len__(self):
        return len(self.stripped)

    def __repr__(self):
        return self.markup


def hex_to_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    #return tuple(bytes.fromhex(value))
