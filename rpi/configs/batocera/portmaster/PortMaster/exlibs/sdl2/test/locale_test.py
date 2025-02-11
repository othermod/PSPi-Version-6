import pytest
import sdl2


@pytest.mark.skipif(sdl2.dll.version < 2014, reason="not available")
def test_SDL_GetPreferredLocales():
    locales = sdl2.SDL_GetPreferredLocales()
    assert type(locales) == list
    if len(locales):
        assert all([type(i) == sdl2.SDL_Locale for i in locales])
        assert len(locales[0].language)
