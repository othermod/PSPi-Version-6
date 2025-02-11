import sys
import pytest

try:
    import multiprocessing
    _HASMP = True
except ImportError:
    _HASMP = False
from sdl2.ext import events


def mp_do_nothing(sender, *args):
    # Does nothing
    pass


class TestExtEventHandler(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        with pytest.raises(TypeError):
            events.EventHandler()
        assert isinstance(events.EventHandler(None), events.EventHandler)
        assert isinstance(events.EventHandler(132), events.EventHandler)
        assert isinstance(events.EventHandler("Test"), events.EventHandler)

        ev = events.EventHandler(None)
        assert ev.sender == None
        ev = events.EventHandler("Test")
        assert ev.sender == "Test"
        assert len(ev) == 0
        assert len(ev.callbacks) == 0

    def test_add__iadd__(self):
        ev = events.EventHandler(None)

        def doadd(ev, cb):
            ev += cb

        def callback():
            pass

        with pytest.raises(TypeError):
            doadd(ev, None)
        with pytest.raises(TypeError):
            doadd(ev, "Test")
        with pytest.raises(TypeError):
            doadd(ev, 1234)

        assert len(ev) == 0
        ev += callback
        assert len(ev) == 1
        for x in range(4):
            ev += callback
        assert len(ev) == 5

        with pytest.raises(TypeError):
            ev.add(None)
        with pytest.raises(TypeError):
            ev.add("Test")
        with pytest.raises(TypeError):
            ev.add(1234)

        assert len(ev) == 5
        ev.add(callback)
        assert len(ev) == 6
        for x in range(4):
            ev.add(callback)
        assert len(ev) == 10

    def test_remove__isub__(self):
        ev = events.EventHandler(None)

        def doremove(ev, cb):
            ev -= cb

        def callback():
            pass

        for x in range(10):
            ev += callback
        assert len(ev) == 10

        with pytest.raises(TypeError):
            ev.remove()
        for invval in ("Test", None, 1234):
            with pytest.raises(ValueError):
                ev.remove(invval)
            with pytest.raises(ValueError):
                doremove(ev, invval)
        assert len(ev) == 10
        ev.remove(callback)
        assert len(ev) == 9
        ev -= callback
        assert len(ev) == 8
        for x in range(3):
            ev.remove(callback)
            ev -= callback
        assert len(ev) == 2

    def test__call__(self):
        ev = events.EventHandler("Test")
        testsum = []

        def callback(sender, sumval):
            assert sender == "Test"
            sumval.append(1)

        for x in range(10):
            ev += callback
        assert len(ev) == 10
        results = ev(testsum)
        assert len(testsum) == 10
        for v in testsum:
            assert v == 1
        assert len(results) == 10
        for v in results:
            assert v is None


@pytest.mark.skipif(not _HASMP, reason="multiprocessing is not supported")
class TestExtMPEventHandler(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        with pytest.raises(TypeError):
            events.MPEventHandler()
        assert isinstance(events.MPEventHandler(None), events.MPEventHandler)
        assert isinstance(events.MPEventHandler(132), events.MPEventHandler)
        assert isinstance(events.MPEventHandler("Test"), events.MPEventHandler)

        ev = events.MPEventHandler(None)
        assert ev.sender == None
        ev = events.MPEventHandler("Test")
        assert ev.sender == "Test"
        assert len(ev) == 0
        assert len(ev.callbacks) == 0

    def test_add__iadd__(self):
        ev = events.MPEventHandler(None)

        def doadd(ev, cb):
            ev += cb

        def callback():
            pass

        with pytest.raises(TypeError):
            doadd(ev, None)
        with pytest.raises(TypeError):
            doadd(ev, "Test")
        with pytest.raises(TypeError):
            doadd(ev, 1234)

        assert len(ev) == 0
        ev += callback
        assert len(ev) == 1
        for x in range(4):
            ev += callback
        assert len(ev) == 5

        with pytest.raises(TypeError):
            ev.add(None)
        with pytest.raises(TypeError):
            ev.add("Test")
        with pytest.raises(TypeError):
            ev.add(1234)

        assert len(ev) == 5
        ev.add(callback)
        assert len(ev) == 6
        for x in range(4):
            ev.add(callback)
        assert len(ev) == 10

    def test_remove__isub__(self):
        ev = events.MPEventHandler(None)

        def doremove(ev, cb):
            ev -= cb

        def callback():
            pass

        for x in range(10):
            ev += callback
        assert len(ev) == 10

        with pytest.raises(TypeError):
            ev.remove()
        for invval in ("Test", None, 1234):
            with pytest.raises(ValueError):
                ev.remove(invval)
            with pytest.raises(ValueError):
                doremove(ev, invval)
        assert len(ev) == 10
        ev.remove(callback)
        assert len(ev) == 9
        ev -= callback
        assert len(ev) == 8
        for x in range(3):
            ev.remove(callback)
            ev -= callback
        assert len(ev) == 2

    @pytest.mark.skipif(not _HASMP, reason="multiprocessing is not supported")
    @pytest.mark.skipif(sys.platform == "win32",
        reason="relative import will create a fork bomb")
    def test__call__(self):
        ev = events.MPEventHandler("Test")

        for x in range(10):
            ev += mp_do_nothing
        assert len(ev) == 10
        results = ev().get(timeout=1)
        assert len(results) == 10
        for v in results:
            assert v is None

        results = ev("Test", 1234, "MoreArgs").get(timeout=1)
        assert len(results) == 10
        for v in results:
            assert v is None
