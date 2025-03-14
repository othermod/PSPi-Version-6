import sys
import pytest
from sdl2 import SDL_Window, SDL_ClearError
from sdl2 import ext as sdl2ext
from sdl2 import messagebox as mb


def test_MessageBoxTheme(with_sdl):
    # Test using RGB color tuples
    theme = sdl2ext.MessageBoxTheme(text=(255, 255, 255))
    text_col = theme._get_theme().colors[1]
    assert text_col.r == 255 and text_col.g == 255

    # Test using Color objects
    BLACK = sdl2ext.Color(0, 0, 0)
    theme = sdl2ext.MessageBoxTheme(btn=BLACK)
    btn_col = theme._get_theme().colors[3]
    assert btn_col.r == 0 and btn_col.b == 0

    # Test exceptions on bad input
    with pytest.raises(TypeError):
        sdl2ext.MessageBoxTheme(bg=(255, 255))
    with pytest.raises(ValueError):
        sdl2ext.MessageBoxTheme(bg=(256, 255, 255))

def test_MessageBox(with_sdl):
    # Test initialization of the class
    box = sdl2ext.MessageBox(
        "Test", "Did it work?", ["Yes", "No"], default="Yes", msgtype="info"
    )
    sdl_box = box._get_msgbox()
    assert sdl_box.flags & mb.SDL_MESSAGEBOX_INFORMATION
    assert sdl_box.title.decode('utf-8') == "Test"
    assert sdl_box.message.decode('utf-8') == "Did it work?"
    assert sdl_box.numbuttons == 2
    b1 = sdl_box.buttons.contents  # Only gets first button for some reason
    assert b1.text.decode('utf-8') == "Yes"
    assert b1.flags & mb.SDL_MESSAGEBOX_BUTTON_RETURNKEY_DEFAULT

    # Test internal generation w/ an associated window
    win = sdl2ext.Window(b"Test", (640, 480))
    sdl_box = box._get_msgbox(win)
    assert isinstance(sdl_box.window.contents, SDL_Window)
    win.close()

    # Test initialization with theme
    mbtheme = sdl2ext.MessageBoxTheme(text=(255, 0, 0))
    box2 = sdl2ext.MessageBox(
        "Test", "Did it work?", ["Yes", "No"], theme=mbtheme
    )
    sdl_box2 = box2._get_msgbox()
    text_col = sdl_box2.colorScheme.contents.colors[1]
    assert text_col.r == 255 and text_col.g == 0

    # Test exceptions on bad input
    with pytest.raises(TypeError):
        sdl2ext.MessageBox("Title", "Some text", "A button")
    with pytest.raises(ValueError):
        sdl2ext.MessageBox("Title", "Some text", [])
    with pytest.raises(ValueError):
        box._get_window_pointer("not a window")

@pytest.mark.skip("not implemented, requires GUI interaction")
def test_show_messagebox(self):
    # Could implement a test using mock, but not sure how useful that'd be
    pass

@pytest.mark.skip("not implemented, requires GUI interaction")
def test_show_alert(self):
    pass
