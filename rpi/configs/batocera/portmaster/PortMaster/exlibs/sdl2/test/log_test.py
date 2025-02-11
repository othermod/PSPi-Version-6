import sys
import pytest
import ctypes
import sdl2

class TestSDLLog(object):
    __tags__ = ["sdl"]

    def setup_method(self):
        self.logdata = []
        def logfunc(userdata, category, priority, message):
            if userdata:
                userdata = ctypes.cast(userdata, ctypes.c_char_p).value
            self.logdata.append((userdata, category, priority, message,))

        # bind to the TestCase, so we do not loose the reference.
        self.funcptr = sdl2.SDL_LogOutputFunction(logfunc)
        sdl2.SDL_LogSetOutputFunction(self.funcptr, None)
        sdl2.SDL_LogSetAllPriority(sdl2.SDL_LOG_PRIORITY_VERBOSE)

    def teardown_method(self):
        sdl2.SDL_LogSetOutputFunction(sdl2.SDL_LogOutputFunction(), None)
        del self.funcptr

    def test_SDL_LogMessage(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogMessage(sdl2.SDL_LOG_CATEGORY_APPLICATION,
                           sdl2.SDL_LOG_PRIORITY_VERBOSE, b"test")
        assert self.logdata[0] == (
            None,   sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_VERBOSE, b"test"
        )
        sdl2.SDL_LogMessage(sdl2.SDL_LOG_CATEGORY_CUSTOM,
                           sdl2.SDL_LOG_PRIORITY_CRITICAL, b"test2")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_CUSTOM,
            sdl2.SDL_LOG_PRIORITY_CRITICAL, b"test2"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogMessage, None, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogMessage, 123, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogMessage, 123, 456, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogMessage, 123, 456, "Test")
        #self.assertRaises(TypeError, sdl2.SDL_LogMessage,
        #                  sdl2.SDL_LOG_CATEGORY_CUSTOM, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogMessage,
        #                  sdl2.SDL_LOG_CATEGORY_CUSTOM, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogMessage,
        #                  sdl2.SDL_LOG_CATEGORY_CUSTOM, 123, "Test")

    def test_SDL_Log(self):
        self.logdata = []  # reset the log
        sdl2.SDL_Log(b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_INFO, b"test"
        )
        sdl2.SDL_Log(b"abcdeghijk")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_INFO, b"abcdeghijk"
        )

    def test_SDL_LogCritical(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogCritical(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_CRITICAL, b"test"
        )
        sdl2.SDL_LogCritical(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_CRITICAL, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogCritical, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogCritical, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogCritical, 123, "Test")

    def test_SDL_LogDebug(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogDebug(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_DEBUG, b"test"
        )
        sdl2.SDL_LogDebug(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_DEBUG, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogDebug, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogDebug, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogDebug, 123, "Test")

    def test_SDL_LogError(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogError(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_ERROR, b"test"
        )
        sdl2.SDL_LogError(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_ERROR, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogError, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogError, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogError, 123, "Test")

    def test_SDL_LogInfo(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogInfo(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_INFO, b"test"
        )
        sdl2.SDL_LogInfo(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_INFO, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogInfo, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogInfo, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogInfo, 123, "Test")

    def test_SDL_LogVerbose(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogVerbose(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_VERBOSE, b"test"
        )
        sdl2.SDL_LogVerbose(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_VERBOSE, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogVerbose, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogVerbose, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogVerbose, 123, "Test")

    def test_SDL_LogWarn(self):
        self.logdata = []  # reset the log
        sdl2.SDL_LogWarn(sdl2.SDL_LOG_CATEGORY_APPLICATION, b"test")
        assert self.logdata[0] == (
            None, sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_WARN, b"test"
        )
        sdl2.SDL_LogWarn(sdl2.SDL_LOG_CATEGORY_SYSTEM, b"test")
        assert self.logdata[1] == (
            None, sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_PRIORITY_WARN, b"test"
        )

        #self.assertRaises(TypeError, sdl2.SDL_LogWarn, None, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogWarn, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogWarn, 123, "Test")

    def test_SDL_LogSetAllPriority(self):
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_APPLICATION) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        sdl2.SDL_LogSetAllPriority(sdl2.SDL_LOG_PRIORITY_WARN)
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_APPLICATION) == \
                                      sdl2.SDL_LOG_PRIORITY_WARN
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM) == \
                                      sdl2.SDL_LOG_PRIORITY_WARN
        # self.assertRaises(ValueError, sdl2.SDL_LogSetAllPriority, 123)
        # self.assertRaises(TypeError, sdl2.SDL_LogSetAllPriority, None)
        # self.assertRaises(TypeError, sdl2.SDL_LogSetAllPriority, "test")

        # Reset to the setUp() value, so other tests do not fail
        sdl2.SDL_LogSetAllPriority(sdl2.SDL_LOG_PRIORITY_VERBOSE)

    def test_SDL_LogGetSetPriority(self):
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_APPLICATION) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_CUSTOM) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        sdl2.SDL_LogSetPriority(sdl2.SDL_LOG_CATEGORY_CUSTOM,
                               sdl2.SDL_LOG_PRIORITY_INFO)
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_APPLICATION) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_CUSTOM) == \
                                      sdl2.SDL_LOG_PRIORITY_INFO
        sdl2.SDL_LogSetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM,
                               sdl2.SDL_LOG_PRIORITY_ERROR)
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_APPLICATION) == \
                                      sdl2.SDL_LOG_PRIORITY_VERBOSE
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_SYSTEM) == \
                                      sdl2.SDL_LOG_PRIORITY_ERROR
        assert sdl2.SDL_LogGetPriority(sdl2.SDL_LOG_CATEGORY_CUSTOM) == \
                                      sdl2.SDL_LOG_PRIORITY_INFO
        #self.assertRaises(TypeError, sdl2.SDL_LogSetPriority, None, None)
        #self.assertRaises(TypeError, sdl2.SDL_LogSetPriority, "Test", None)
        #self.assertRaises(ValueError, sdl2.SDL_LogSetPriority, 123, None)
        #self.assertRaises(ValueError, sdl2.SDL_LogSetPriority, 123, "Test")
        #self.assertRaises(TypeError, sdl2.SDL_LogSetPriority,
        #                  sdl2.SDL_LOG_CATEGORY_APPLICATION, None)
        #self.assertRaises(TypeError, sdl2.SDL_LogSetPriority,
        #                  sdl2.SDL_LOG_CATEGORY_APPLICATION, "Test")
        #self.assertRaises(ValueError, sdl2.SDL_LogSetPriority,
        #                  sdl2.SDL_LOG_CATEGORY_APPLICATION, 123)

        #self.assertRaises(TypeError, sdl2.SDL_LogGetPriority, None)
        #self.assertRaises(TypeError, sdl2.SDL_LogGetPriority, "Test")
        #self.assertRaises(ValueError, sdl2.SDL_LogGetPriority, 123)

    def test_SDL_LogResetPriorities(self):
        # set in setUp()
        defpriority = sdl2.SDL_LOG_PRIORITY_VERBOSE
        categories = (
            sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_CATEGORY_ERROR,
            sdl2.SDL_LOG_CATEGORY_SYSTEM,
            sdl2.SDL_LOG_CATEGORY_AUDIO,
            sdl2.SDL_LOG_CATEGORY_VIDEO,
            sdl2.SDL_LOG_CATEGORY_RENDER,
            sdl2.SDL_LOG_CATEGORY_INPUT,
            sdl2.SDL_LOG_CATEGORY_CUSTOM
            )
        for cat in categories:
            priority = sdl2.SDL_LogGetPriority(cat)
            assert priority == defpriority

        sdl2.SDL_LogResetPriorities()
        for cat in categories:
            priority = sdl2.SDL_LogGetPriority(cat)
            assert priority != defpriority

        sdl2.SDL_LogSetAllPriority(sdl2.SDL_LOG_PRIORITY_VERBOSE)

    def test_SDL_LogGetSetOutputFunction(self):
        logentries = []

        def __log(userdata, category, priority, message):
            if userdata:
                userdata = ctypes.cast(userdata, ctypes.c_char_p).value
            logentries.append((userdata, category, priority, message,))

        # setUp should have set our output function already.
        origfunc = sdl2.SDL_LogOutputFunction()
        origdata = ctypes.c_void_p(0)
        sdl2.SDL_LogGetOutputFunction(ctypes.byref(origfunc),
                                     ctypes.byref(origdata))
        assert not origdata
        logcount = len(self.logdata)
        origfunc(None, 0, 0, b"test_log_get_set_output_function")
        assert len(self.logdata) == logcount + 1
        assert self.logdata[logcount][3] == b"test_log_get_set_output_function"

        logptr = sdl2.SDL_LogOutputFunction(__log)
        userdata = ctypes.c_char_p(b"Testobject")
        sdl2.SDL_LogSetOutputFunction(logptr, userdata)
        ptr = sdl2.SDL_LogOutputFunction()
        userdata = ctypes.c_void_p(0)
        sdl2.SDL_LogGetOutputFunction(ctypes.byref(ptr), ctypes.byref(userdata))
        userdata = ctypes.cast(userdata, ctypes.c_char_p)
        assert userdata.value == b"Testobject"
        sdl2.SDL_Log(b"output test")
        assert logentries[0] == (
            b"Testobject", sdl2.SDL_LOG_CATEGORY_APPLICATION,
            sdl2.SDL_LOG_PRIORITY_INFO, b"output test"
        )

        sdl2.SDL_LogSetOutputFunction(origfunc, userdata)
