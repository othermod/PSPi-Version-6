import sys
import pytest
from ctypes import c_char_p, c_void_p, cast
import sdl2
from sdl2 import SDL_Init, SDL_Quit, SDL_QuitSubSystem, SDL_INIT_EVERYTHING

# NOTE: These tests are very incomplete and in need of a rewrite


# Test initializing event structs (is this actually useful?)

def test_SDL_AudioDeviceEvent():
    event = sdl2.SDL_AudioDeviceEvent()
    assert isinstance(event, sdl2.SDL_AudioDeviceEvent)

def test_SDL_DisplayEvent():
    event = sdl2.SDL_DisplayEvent()
    assert isinstance(event, sdl2.SDL_DisplayEvent)

def test_SDL_WindowEvent():
    event = sdl2.SDL_WindowEvent()
    assert isinstance(event, sdl2.SDL_WindowEvent)

def test_SDL_KeyboardEvent():
    event = sdl2.SDL_KeyboardEvent()
    assert isinstance(event, sdl2.SDL_KeyboardEvent)

def test_SDL_TextEditingEvent():
    event = sdl2.SDL_TextEditingEvent()
    assert isinstance(event, sdl2.SDL_TextEditingEvent)

def test_SDL_TextInputEvent():
    event = sdl2.SDL_TextInputEvent()
    assert isinstance(event, sdl2.SDL_TextInputEvent)

def test_SDL_MouseMotionEvent():
    event = sdl2.SDL_MouseMotionEvent()
    assert isinstance(event, sdl2.SDL_MouseMotionEvent)

def test_SDL_MouseButtonEvent():
    event = sdl2.SDL_MouseButtonEvent()
    assert isinstance(event, sdl2.SDL_MouseButtonEvent)

def test_SDL_MouseWheelEvent():
    event = sdl2.SDL_MouseWheelEvent()
    assert isinstance(event, sdl2.SDL_MouseWheelEvent)

def test_SDL_JoyAxisEvent():
    event = sdl2.SDL_JoyAxisEvent()
    assert isinstance(event, sdl2.SDL_JoyAxisEvent)

def test_SDL_JoyBallEvent():
    event = sdl2.SDL_JoyBallEvent()
    assert isinstance(event, sdl2.SDL_JoyBallEvent)

def test_SDL_JoyHatEvent():
    event = sdl2.SDL_JoyHatEvent()
    assert isinstance(event, sdl2.SDL_JoyHatEvent)

def test_SDL_JoyButtonEvent():
    event = sdl2.SDL_JoyButtonEvent()
    assert isinstance(event, sdl2.SDL_JoyButtonEvent)

def test_SDL_JoyDeviceEvent():
    event = sdl2.SDL_JoyDeviceEvent()
    assert isinstance(event, sdl2.SDL_JoyDeviceEvent)

def test_SDL_ControllerAxisEvent():
    event = sdl2.SDL_ControllerAxisEvent()
    assert isinstance(event, sdl2.SDL_ControllerAxisEvent)

def test_SDL_ControllerButtonEvent():
    event = sdl2.SDL_ControllerButtonEvent()
    assert isinstance(event, sdl2.SDL_ControllerButtonEvent)

def test_SDL_ControllerDeviceEvent():
    event = sdl2.SDL_ControllerDeviceEvent()
    assert isinstance(event, sdl2.SDL_ControllerDeviceEvent)

def test_SDL_ControllerTouchpadEvent():
    event = sdl2.SDL_ControllerTouchpadEvent()
    assert isinstance(event, sdl2.SDL_ControllerTouchpadEvent)

def test_SDL_ControllerSensorEvent():
    event = sdl2.SDL_ControllerSensorEvent()
    assert isinstance(event, sdl2.SDL_ControllerSensorEvent)

def test_SDL_TouchFingerEvent():
    event = sdl2.SDL_TouchFingerEvent()
    assert isinstance(event, sdl2.SDL_TouchFingerEvent)

def test_SDL_MultiGestureEvent():
    event = sdl2.SDL_MultiGestureEvent()
    assert isinstance(event, sdl2.SDL_MultiGestureEvent)

def test_SDL_DollarGestureEvent():
    event = sdl2.SDL_DollarGestureEvent()
    assert isinstance(event, sdl2.SDL_DollarGestureEvent)

def test_SDL_DropEvent():
    event = sdl2.SDL_DropEvent()
    assert isinstance(event, sdl2.SDL_DropEvent)

def test_SDL_SensorEvent():
    event = sdl2.SDL_SensorEvent()
    assert isinstance(event, sdl2.SDL_SensorEvent)

def test_SDL_QuitEvent():
    event = sdl2.SDL_QuitEvent()
    assert isinstance(event, sdl2.SDL_QuitEvent)

def test_SDL_UserEvent():
    event = sdl2.SDL_UserEvent()
    assert isinstance(event, sdl2.SDL_UserEvent)

def test_SDL_SysWMEvent():
    event = sdl2.SDL_SysWMEvent()
    assert isinstance(event, sdl2.SDL_SysWMEvent)

def test_SDL_Event():
    event = sdl2.SDL_Event()
    assert isinstance(event, sdl2.SDL_Event)


class TestSDLEvents(object):
    __tags__ = ["sdl"]

    @classmethod
    def setup_class(cls):
        SDL_Init(SDL_INIT_EVERYTHING)

    @classmethod
    def teardown_class(cls):
        SDL_QuitSubSystem(SDL_INIT_EVERYTHING)
        SDL_Quit()

    def test_SDL_AddDelEventWatch(self):
        eventwatch = []

        def watch(data, event):
            eventwatch.append((event.contents, data,))
            return 0
        efilter = sdl2.SDL_EventFilter(watch)
        udata = c_char_p(b"Something random")
        sdl2.SDL_AddEventWatch(efilter, cast(udata, c_void_p))
        ev = sdl2.SDL_Event()
        ev.type = sdl2.SDL_USEREVENT
        ev.user = sdl2.SDL_UserEvent()
        sdl2.SDL_PushEvent(ev)
        assert len(eventwatch) == 1
        # TODO: x
        # self.assertEqual(eventwatch[0][1], udata)

        sdl2.SDL_DelEventWatch(efilter, udata)
        ev = sdl2.SDL_Event()
        sdl2.SDL_PushEvent(ev)
        assert len(eventwatch) == 1
        # TODO: x
        # self.assertEqual(eventwatch[0][1], udata)

    @pytest.mark.skip("not implemented")
    def test_SDL_EventState(self):
        pass
        # state = sdl2.SDL_EventState(sdl2.SDL_USEREVENT, sdl2.SDL_QUERY)
        # self.assertEqual(state, sdl2.SDL_ENABLE)
        # state = sdl2.SDL_EventState(sdl2.SDL_USEREVENT,sdl2.SDL_IGNORE)
        # self.assertEqual(state, sdl2.SDL_ENABLE)
        # state = sdl2.SDL_EventState(sdl2.SDL_USEREVENT, sdl2.SDL_QUERY)
        # self.assertEqual(state, sdl2.SDL_IGNORE)
        # state = sdl2.SDL_EventState(sdl2.SDL_USEREVENT,sdl2.SDL_ENABLE)
        # self.assertEqual(state, sdl2.SDL_IGNORE)
        # state = sdl2.SDL_EventState(sdl2.SDL_USEREVENT, sdl2.SDL_QUERY)
        # self.assertEqual(state, sdl2.SDL_ENABLE)

        # self.assertRaises(TypeError, sdl2.SDL_EventState, None, None)

        # ev = sdl2.SDL_Event()
        # ev.type = sdl2.SDL_USEREVENT
        # ev.user = sdl2.SDL_UserEvent()
        # sdl2.SDL_PushEvent(ev)

    @pytest.mark.skip("not implemented")
    def test_SDL_GetEventState(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_FilterEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_FlushEvent(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_FlushEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_GetSetEventFilter(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_HasEvent(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_HasEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_PeepEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_PollEvent(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_PumpEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_PushEvent(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_RegisterEvents(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_WaitEvent(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_WaitEventTimeout(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_SDL_QuitRequested(self):
        pass
