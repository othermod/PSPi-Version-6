import sys
import copy
import pytest
import random
from ctypes import byref, c_int, c_float
import sdl2
from sdl2.stdinc import SDL_FALSE, SDL_TRUE
from sdl2 import rect

to_ctypes = lambda seq, dtype: (dtype * len(seq))(*seq)


class TestSDLPoint(object):
    __tags__ = ["sdl"]

    def test_init(self):
        pt = sdl2.SDL_Point()
        assert (pt.x, pt.y) == (0, 0)
        for i in range(0, 100):
            x = random.randint(-1000, 1000)
            y = random.randint(-1000, 1000)
            pt = sdl2.SDL_Point(x, y)
            assert (pt.x, pt.y) == (x, y)

    def test_xy(self):
        pt = sdl2.SDL_Point()
        for i in range(0, 50):
            x = random.randint(-1000, 1000)
            y = random.randint(-1000, 1000)
            pt.x = x
            pt.y = y
            assert (pt.x, pt.y) == (x, y)
        with pytest.raises(TypeError):
            pt.x = 10.4
        with pytest.raises(TypeError):
            pt.y = 10.4
        with pytest.raises(TypeError):
            pt.x = "point"
        with pytest.raises(TypeError):
            pt.y = "point"
        with pytest.raises(TypeError):
            pt.x = None
        with pytest.raises(TypeError):
            pt.y = None

    def test___repr__(self):
        pt = sdl2.SDL_Point(10, 12)
        pt2 = eval("sdl2.%s" % repr(pt))
        assert pt == pt2
        assert (pt.x, pt.y) == (pt2.x, pt2.y)

    def test___copy__(self):
        pt = sdl2.SDL_Point()
        pt2 = copy.copy(pt)
        assert pt == pt2
        assert (pt.x, pt.y) == (pt2.x, pt2.y)
        pt2.x = 7
        pt2.y = 9
        pt3 = copy.copy(pt2)
        assert pt != pt2
        assert pt3 == pt2

    def test___eq__(self):
        assert sdl2.SDL_Point() == sdl2.SDL_Point()
        coords = [(0, 0), (10, 0), (0, 10), (12, 10), (7, 10)]
        for x1, y1 in coords:
            for x2, y2 in coords:
                equal = sdl2.SDL_FPoint(x1, y1) == sdl2.SDL_FPoint(x2, y2)
                assert equal if (x1 == x2 and y1 == y2) else not equal

    def test___ne__(self):
        assert not sdl2.SDL_Point() != sdl2.SDL_Point()
        coords = [(0, 0), (10, 0), (0, 10), (12, 10), (7, 10)]
        for x1, y1 in coords:
            for x2, y2 in coords:
                notequal = sdl2.SDL_Point(x1, y1) != sdl2.SDL_Point(x2, y2)
                assert notequal if (x1 != x2 or y1 != y2) else not notequal

    def test___getitem__(self):
        p = sdl2.SDL_Point(5, 10)
        x, y = p
        assert x == 5
        assert y == 10
        with pytest.raises(IndexError):
            a = p[2]



@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
class TestSDLFPoint(object):
    __tags__ = ["sdl"]

    def test_init(self):
        pt = sdl2.SDL_FPoint()
        assert (pt.x, pt.y) == (0, 0)
        for i in range(0, 100):
            x = random.uniform(-1000, 1000)
            y = random.uniform(-1000, 1000)
            pt = sdl2.SDL_FPoint(x, y)
            assert (pt.x, pt.y) == pytest.approx((x, y))

    def test_xy(self):
        pt = sdl2.SDL_FPoint()
        for i in range(0, 50):
            x = random.uniform(-1000, 1000)
            y = random.uniform(-1000, 1000)
            pt.x = x
            pt.y = y
            assert (pt.x, pt.y) == pytest.approx((x, y))
        with pytest.raises(TypeError):
            pt.x = "point"
        with pytest.raises(TypeError):
            pt.y = "point"
        with pytest.raises(TypeError):
            pt.x = None
        with pytest.raises(TypeError):
            pt.y = None

    def test___repr__(self):
        pt = sdl2.SDL_FPoint(3.24, 12.8)
        pt2 = eval("sdl2.%s" % repr(pt))
        assert pt == pt2
        assert (pt.x, pt.y) == (pt2.x, pt2.y)

    def test___copy__(self):
        pt = sdl2.SDL_FPoint()
        pt2 = copy.copy(pt)
        assert pt == pt2
        assert (pt.x, pt.y) == (pt2.x, pt2.y)
        pt2.x = 7
        pt2.y = 9
        pt3 = copy.copy(pt2)
        assert pt != pt2
        assert pt3 == pt2

    def test___eq__(self):
        assert sdl2.SDL_FPoint() == sdl2.SDL_FPoint()
        coords = [(0, 0.5), (10, 0.5), (0, 10.5), (12, 10.5), (7, 10.5)]
        for x1, y1 in coords:
            for x2, y2 in coords:
                equal = sdl2.SDL_FPoint(x1, y1) == sdl2.SDL_FPoint(x2, y2)
                assert equal if (x1 == x2 and y1 == y2) else not equal

    def test___ne__(self):
        assert not sdl2.SDL_FPoint() != sdl2.SDL_FPoint()
        coords = [(0, 0.5), (10, 0.5), (0, 10.5), (12, 10.5), (7, 10.5)]
        for x1, y1 in coords:
            for x2, y2 in coords:
                notequal = sdl2.SDL_FPoint(x1, y1) != sdl2.SDL_FPoint(x2, y2)
                assert notequal if (x1 != x2 or y1 != y2) else not notequal

    def test___getitem__(self):
        p = sdl2.SDL_FPoint(5.5, 10)
        x, y = p
        assert x == 5.5
        assert y == 10
        with pytest.raises(IndexError):
            a = p[2]


class TestSDLRect(object):
    __tags__ = ["sdl"]

    def test_init(self):
        rt = sdl2.SDL_Rect()
        assert (rt.x, rt.y, rt.w, rt.h) == (0, 0, 0, 0)
        for i in range(0, 50):
            x = random.randint(-1000, 1000)
            y = random.randint(-1000, 1000)
            w = random.randint(-1000, 1000)
            h = random.randint(-1000, 1000)
            rt = sdl2.SDL_Rect(x, y, w, h)
            assert (rt.x, rt.y, rt.w, rt.h) == (x, y, w, h)

    def test_xywh(self):
        rt = sdl2.SDL_Rect()
        for i in range(0, 50):
            x = random.randint(-1000, 1000)
            y = random.randint(-1000, 1000)
            w = random.randint(-1000, 1000)
            h = random.randint(-1000, 1000)
            rt.x = x
            rt.y = y
            rt.w = w
            rt.h = h
            assert (rt.x, rt.y, rt.w, rt.h) == (x, y, w, h)

        bad_inputs = [10.4, "point", None]
        for val in bad_inputs:  
            with pytest.raises(TypeError):
                rt.x = val
            with pytest.raises(TypeError):
                rt.y = val
            with pytest.raises(TypeError):
                rt.w = val
            with pytest.raises(TypeError):
                rt.h = val

    def test___repr__(self):
        rt = sdl2.SDL_Rect(1, 2, 3, 4)
        rt2 = eval("sdl2.%s" % repr(rt))
        assert (rt.x, rt.y, rt.w, rt.h) == (rt2.x, rt2.y, rt2.w, rt2.h)
        assert rt == rt2

    def test___copy__(self):
        rt = sdl2.SDL_Rect()
        rt2 = copy.copy(rt)
        assert rt == rt2
        assert (rt.x, rt.y, rt.w, rt.h) == (rt2.x, rt2.y, rt2.w, rt2.h)
        rt2.x = 5
        rt2.y = 33
        rt2.w = 17
        rt2.w = 212
        rt3 = copy.copy(rt2)
        assert rt != rt2
        assert rt3 == rt2

    def test___eq__(self):
        sdlr = sdl2.SDL_Rect
        assert sdlr() == sdlr()
        rects = [
            (0, 0, 0, 0), (0, 0, 0, 1), (10, 0, 1, 1), (0, 10, 1, 1),
            (1, 2, 3, 4)
        ]
        for x1, y1, w1, h1 in rects:
            for x2, y2, w2, h2 in rects:
                same = x1 == x2 and y1 == y2 and w1 == w2 and h1 == h2
                equal = sdlr(x1, y1, w1, h1) == sdlr(x2, y2, w2, h2)
                assert equal if same else not equal

    def test___ne__(self):
        sdlr = sdl2.SDL_Rect
        assert sdlr() == sdlr()
        rects = [
            (0, 0, 0, 0), (0, 0, 0, 1), (10, 0, 1, 1), (0, 10, 1, 1),
            (1, 2, 3, 4)
        ]
        for x1, y1, w1, h1 in rects:
            for x2, y2, w2, h2 in rects:
                same = x1 == x2 and y1 == y2 and w1 == w2 and h1 == h2
                notequal = sdlr(x1, y1, w1, h1) != sdlr(x2, y2, w2, h2)
                assert notequal if same == False else not notequal

    def test___getitem__(self):
        r = sdl2.SDL_Rect(5, 10, 20, 40)
        x, y, w, h = r
        assert x == 5
        assert y == 10
        assert w == 20
        assert h == 40
        with pytest.raises(IndexError):
            a = r[4]


@pytest.mark.skipif(sdl2.dll.version < 2010, reason="not available")
class TestSDLFRect(object):
    __tags__ = ["sdl"]

    def test_init(self):
        rt = sdl2.SDL_FRect()
        assert (rt.x, rt.y, rt.w, rt.h) == (0, 0, 0, 0)
        for i in range(0, 50):
            x = random.uniform(-1000, 1000)
            y = random.uniform(-1000, 1000)
            w = random.uniform(-1000, 1000)
            h = random.uniform(-1000, 1000)
            rt = sdl2.SDL_FRect(x, y, w, h)
            assert (rt.x, rt.y, rt.w, rt.h) == pytest.approx((x, y, w, h))

    def test_xywh(self):
        rt = sdl2.SDL_FRect()
        for i in range(0, 50):
            x = random.uniform(-1000, 1000)
            y = random.uniform(-1000, 1000)
            w = random.uniform(-1000, 1000)
            h = random.uniform(-1000, 1000)
            rt.x = x
            rt.y = y
            rt.w = w
            rt.h = h
            assert (rt.x, rt.y, rt.w, rt.h) == pytest.approx((x, y, w, h))

        bad_inputs = ["point", None]
        for val in bad_inputs:  
            with pytest.raises(TypeError):
                rt.x = val
            with pytest.raises(TypeError):
                rt.y = val
            with pytest.raises(TypeError):
                rt.w = val
            with pytest.raises(TypeError):
                rt.h = val

    def test___repr__(self):
        rt = sdl2.SDL_FRect(1.5, 2.2, 3.8, 4.9)
        rt2 = eval("sdl2.%s" % repr(rt))
        assert (rt.x, rt.y, rt.w, rt.h) == (rt2.x, rt2.y, rt2.w, rt2.h)
        assert rt == rt2

    def test___copy__(self):
        rt = sdl2.SDL_FRect()
        rt2 = copy.copy(rt)
        assert rt == rt2
        assert (rt.x, rt.y, rt.w, rt.h) == (rt2.x, rt2.y, rt2.w, rt2.h)
        rt2.x = 5.5
        rt2.y = 33
        rt2.w = 17.2
        rt2.w = 212
        rt3 = copy.copy(rt2)
        assert rt != rt2
        assert rt3 == rt2

    def test___eq__(self):
        sdlr = sdl2.SDL_FRect
        assert sdlr() == sdlr()
        rects = [
            (0, 0.5, 1, 1), (10, 0.5, 99.9, 1.9), (0, 0.5, 99.9, 96),
            (-2.4, 0.5, 1, 1), (0, 0, 99.9, 1.9)
        ]
        for x1, y1, w1, h1 in rects:
            for x2, y2, w2, h2 in rects:
                same = x1 == x2 and y1 == y2 and w1 == w2 and h1 == h2
                equal = sdlr(x1, y1, w1, h1) == sdlr(x2, y2, w2, h2)
                assert equal if same else not equal

    def test___ne__(self):
        sdlr = sdl2.SDL_FRect
        assert sdlr() == sdlr()
        rects = [
            (0, 0.5, 1, 1), (10, 0.5, 99.9, 1.9), (0, 0.5, 99.9, 96),
            (-2.4, 0.5, 1, 1), (0, 0, 99.9, 1.9)
        ]
        for x1, y1, w1, h1 in rects:
            for x2, y2, w2, h2 in rects:
                same = x1 == x2 and y1 == y2 and w1 == w2 and h1 == h2
                notequal = sdlr(x1, y1, w1, h1) != sdlr(x2, y2, w2, h2)
                assert notequal if same == False else not notequal

    def test___getitem__(self):
        r = sdl2.SDL_FRect(5.5, 10, 20, 40)
        x, y, w, h = r
        assert x == 5.5
        assert y == 10
        assert w == 20
        assert h == 40
        with pytest.raises(IndexError):
            a = r[4]


def test_SDL_RectEmpty():
    for i in range(0, 50):
        w = random.randint(-100, 100)
        h = random.randint(-100, 100)
        r = sdl2.SDL_Rect(0, 0, w, h)
        empty = sdl2.SDL_RectEmpty(r)
        assert empty if not (w > 0 and h > 0) else not empty
    with pytest.raises(AttributeError):
        sdl2.SDL_RectEmpty("Test")

def test_SDL_RectEquals():
    r1 = sdl2.SDL_Rect(0, 0, 1, 1)
    r2 = sdl2.SDL_Rect(0, 0, 1, 1)
    assert sdl2.SDL_RectEquals(r1, r2)
    r2 = sdl2.SDL_Rect(-1, 2, 1, 1)
    assert not sdl2.SDL_RectEquals(r1, r2)
    r2 = sdl2.SDL_Rect(0, 0, 1, 2)
    assert not sdl2.SDL_RectEquals(r1, r2)
    # Test exceptions
    with pytest.raises(AttributeError):
        sdl2.SDL_RectEquals("Test", r2)
    with pytest.raises(AttributeError):
        sdl2.SDL_RectEquals(r1, None)

def test_SDL_UnionRect():
    tests = [
        [(0, 0, 10, 10), (20, 20, 10, 10), (0, 0, 30, 30)],
        [(0, 0, 0, 0), (20, 20, 10, 10), (20, 20, 10, 10)],
        [(-200, -4, 450, 33), (20, 20, 10, 10), (-200, -4, 450, 34)],
        [(0, 0, 15, 16), (20, 20, 0, 0), (0, 0, 15, 16)]
    ]
    out = sdl2.SDL_Rect()
    for rect1, rect2, expected in tests:
        r1 = sdl2.SDL_Rect(*rect1)
        r2 = sdl2.SDL_Rect(*rect2)
        sdl2.SDL_UnionRect(r1, r2, byref(out))
        assert (out.x, out.y, out.w, out.h) == expected
    # Test exceptions
    with pytest.raises((AttributeError, TypeError)):
        sdl2.SDL_UnionRect(None, None)
    with pytest.raises((AttributeError, TypeError)):
        sdl2.SDL_UnionRect("Test", r2)
    with pytest.raises((AttributeError, TypeError)):
        sdl2.SDL_UnionRect(r1, None)
    with pytest.raises((AttributeError, TypeError)):
        sdl2.SDL_UnionRect(r1, "Test")

def test_SDL_IntersectRectAndLine():
    tests = [
        [(0, 0, 0, 0), (-5, -5, 5, 5), SDL_FALSE, None],
        [(0, 0, 2, 2), (-1, -1, 3, 3), SDL_TRUE, (0, 0, 1, 1)],
        [(-4, -4, 14, 14), (8, 22, 8, 33), SDL_FALSE, None]
    ]
    for rect1, line, expected_ret, expected_coords in tests:
        r = sdl2.SDL_Rect(*rect1)
        x1, y1, x2, y2 = line
        x1, y1, x2, y2 = c_int(x1), c_int(y1), c_int(x2), c_int(y2)
        ret = sdl2.SDL_IntersectRectAndLine(
            r, byref(x1), byref(y1), byref(x2), byref(y2))
        assert ret == expected_ret
        if ret == SDL_TRUE:
            assert (x1.value, y1.value, x2.value, y2.value) == expected_coords

def test_SDL_EnclosePoints():
    tests = [
        [sdl2.SDL_Rect(0, 0, 10, 10), SDL_TRUE, (0, 0, 6, 8)],
        [sdl2.SDL_Rect(-10, -10, 3, 3), SDL_FALSE, (0, 0, 0, 0)],
        [None, SDL_TRUE, (0, 0, 6, 8)],
    ]
    pt1, pt2 = [sdl2.SDL_Point(0, 0), sdl2.SDL_Point(5, 7)]
    points = to_ctypes([pt1, pt2], sdl2.SDL_Point)
    res = sdl2.SDL_Rect()
    for clip, expected_ret, expected_rect in tests:
        clip_p = byref(clip) if isinstance(clip, sdl2.SDL_Rect) else None
        ret = sdl2.SDL_EnclosePoints(points, 2, clip_p, byref(res))
        assert ret == expected_ret
        r = sdl2.SDL_Rect(*expected_rect)
        assert res == r if ret == SDL_TRUE else res != r
    # Test with no points
    ret = sdl2.SDL_EnclosePoints(None, 0, None, byref(res))
    assert not ret
    assert res != sdl2.SDL_Rect()
    # Test expceptions
    with pytest.raises(TypeError):
        sdl2.SDL_EnclosePoints(None, None)
    with pytest.raises(TypeError):
        sdl2.SDL_EnclosePoints("Test", None)
    with pytest.raises(TypeError):
        sdl2.SDL_EnclosePoints((1, 2, 3), None)
    with pytest.raises(TypeError):
        sdl2.SDL_EnclosePoints((None,), None)

def test_SDL_HasIntersection():
    tests = [
        [(0, 0, 0, 0), (0, 0, 0, 0), SDL_FALSE],
        [(0, 0, -200, 200), (0, 0, -200, 200), SDL_FALSE],
        [(0, 0, 10, 10), (-5, 5, 10, 2), SDL_TRUE],
        [(0, 0, 10, 10), (-5, -5, 10, 2), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 2, 10), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 5, 5), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 6, 6), SDL_TRUE]
    ]
    for rect1, rect2, expected in tests:
        r1 = sdl2.SDL_Rect(*rect1)
        r2 = sdl2.SDL_Rect(*rect2)
        assert sdl2.SDL_HasIntersection(r1, r2) == expected

def test_SDL_IntersectRect():
    tests = [
        [(0, 0, 0, 0), (0, 0, 0, 0), SDL_FALSE, None],
        [(0, 0, -200, 200), (0, 0, -200, 200), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, 5, 10, 2), SDL_TRUE, (0, 5, 5, 2)],
        [(0, 0, 10, 10), (-5, -5, 10, 2), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 2, 10), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 5, 5), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 6, 6), SDL_TRUE, (0, 0, 1, 1)]
    ]
    res = sdl2.SDL_Rect()
    for rect1, rect2, expected_ret, expected_rect in tests:
        r1 = sdl2.SDL_Rect(*rect1)
        r2 = sdl2.SDL_Rect(*rect2)
        ret = sdl2.SDL_IntersectRect(r1, r2, byref(res))
        assert ret == expected_ret
        if ret == SDL_TRUE:
            res == sdl2.SDL_Rect(*expected_rect)

def test_SDL_PointInRect():
    r = sdl2.SDL_Rect(0, 0, 10, 10)
    inside = [(0, 0), (4, 2)]
    outside = [(10, 10), (10, 3), (3, 10), (-1, -3)]
    for x, y in inside:
        p = sdl2.SDL_Point(x, y)
        assert sdl2.SDL_PointInRect(p, r)
    for x, y in outside:
        p = sdl2.SDL_Point(x, y)
        assert not sdl2.SDL_PointInRect(p, r)

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_HasIntersectionF():
    tests = [
        [(0, 0, 0, 0), (0, 0, 0, 0), SDL_FALSE],
        [(0, 0, -200, 200), (0, 0, -200, 200), SDL_FALSE],
        [(0, 0, 10, 10), (-5, 5, 10, 2), SDL_TRUE],
        [(0, 0, 10, 10), (-5, -5, 10, 2), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 2, 10), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 5, 5), SDL_FALSE],
        [(0, 0, 10, 10), (-5, -5, 5.1, 5.1), SDL_TRUE],
        [(0, 0, 10, 10), (-4.99, -4.99, 5, 5), SDL_TRUE],
    ]
    for rect1, rect2, expected in tests:
        r1 = sdl2.SDL_FRect(*rect1)
        r2 = sdl2.SDL_FRect(*rect2)
        assert sdl2.SDL_HasIntersectionF(r1, r2) == expected

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_IntersectFRect():
    tests = [
        [(0, 0, 0, 0), (0, 0, 0, 0), SDL_FALSE, None],
        [(0, 0, -200, 200), (0, 0, -200, 200), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, 5, 9.9, 2), SDL_TRUE, (0, 5, 4.9, 2)],
        [(0, 0, 10, 10), (-5, -5, 10, 2), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 2, 10), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 5, 5), SDL_FALSE, None],
        [(0, 0, 10, 10), (-5, -5, 5.5, 6), SDL_TRUE, (0, 0, 0.5, 1)]
    ]
    res = sdl2.SDL_FRect()
    for rect1, rect2, expected_ret, expected_rect in tests:
        r1 = sdl2.SDL_FRect(*rect1)
        r2 = sdl2.SDL_FRect(*rect2)
        ret = sdl2.SDL_IntersectFRect(r1, r2, byref(res))
        assert ret == expected_ret
        if ret == SDL_TRUE:
            res == sdl2.SDL_FRect(*expected_rect)

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_UnionFRect():
    tests = [
        [(0, 0, 10, 10), (19.9, 20, 10, 10), (0, 0, 29.9, 30)],
        [(0, 0, 0, 0), (20, 20.1, 10.1, 10), (20, 20.1, 10.1, 10)],
        [(-200, -4.5, 450, 33), (20, 20, 10, 10), (-200, -4.5, 450, 34.5)],
        [(0, 0, 15, 16.5), (20, 20, 0, 0), (0, 0, 15, 16.5)]
    ]
    out = sdl2.SDL_FRect()
    for rect1, rect2, expected in tests:
        r1 = sdl2.SDL_FRect(*rect1)
        r2 = sdl2.SDL_FRect(*rect2)
        sdl2.SDL_UnionFRect(r1, r2, byref(out))
        res = (out.x, out.y, out.w, out.h)
        assert tuple([round(n, 6) for n in res]) == expected

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_EncloseFPoints():
    tests = [
        [sdl2.SDL_FRect(0, 0, 10, 10), SDL_TRUE, (0.5, 0.1, 6, 8)],
        [sdl2.SDL_FRect(1.2, 1, 10, 10), SDL_TRUE, (1.5, 1.1, 5, 7)],
        [sdl2.SDL_FRect(-10, -10, 3, 3), SDL_FALSE, (0, 0, 0, 0)],
        [None, SDL_TRUE, (0.5, 0.1, 6, 8)],
    ]
    pt1, pt2 = [sdl2.SDL_FPoint(0.5, 0.1), sdl2.SDL_FPoint(5.5, 7.1)]
    pt3 = sdl2.SDL_FPoint(1.5, 1.1)
    points = to_ctypes([pt1, pt2, pt3], sdl2.SDL_FPoint)
    res = sdl2.SDL_FRect()
    for clip, expected_ret, expected_rect in tests:
        clip_p = byref(clip) if isinstance(clip, sdl2.SDL_FRect) else None
        ret = sdl2.SDL_EncloseFPoints(points, 3, clip_p, byref(res))
        assert ret == expected_ret
        r = sdl2.SDL_FRect(*expected_rect)
        assert res == r if ret == SDL_TRUE else res != r
    # Test with no points
    ret = sdl2.SDL_EncloseFPoints(None, 0, None, byref(res))
    assert not ret
    assert res != sdl2.SDL_FRect()

@pytest.mark.skipif(sdl2.dll.version < 2022, reason="not available")
def test_SDL_IntersectFRectAndLine():
    tests = [
        [(0, 0, 0, 0), (-4.8, -4.8, 5.2, 5.2), SDL_FALSE, None],
        [(0, 0, 2, 2), (-1, -1, 3.5, 3.5), SDL_TRUE, (0, 0, 1, 1)],
        [(-4, -4, 14, 14), (8, 22, 8, 33), SDL_FALSE, None]
    ]
    for rect1, line, expected_ret, expected_coords in tests:
        r = sdl2.SDL_FRect(*rect1)
        x1, y1, x2, y2 = line
        x1, y1, x2, y2 = c_float(x1), c_float(y1), c_float(x2), c_float(y2)
        ret = sdl2.SDL_IntersectFRectAndLine(
            r, byref(x1), byref(y1), byref(x2), byref(y2))
        assert ret == expected_ret
        if ret == SDL_TRUE:
            assert (x1.value, y1.value, x2.value, y2.value) == expected_coords

def test_SDL_PointInFRect():
    r = sdl2.SDL_FRect(0, 0, 8.6, 9.2)
    inside = [(0, 0), (4, 2)]
    outside = [(8.6, 9.2), (8.6, 3), (3, 9.2), (-1, -3)]
    for x, y in inside:
        p = sdl2.SDL_FPoint(x, y)
        assert sdl2.SDL_PointInFRect(p, r)
    for x, y in outside:
        p = sdl2.SDL_FPoint(x, y)
        assert not sdl2.SDL_PointInFRect(p, r)

def test_SDL_FRectEmpty():
    for i in range(0, 20):
        w = random.uniform(-100, 100)
        h = random.uniform(-100, 100)
        r = sdl2.SDL_FRect(0, 0, w, h)
        empty = sdl2.SDL_FRectEmpty(r)
        assert empty if not (w > 0 and h > 0) else not empty

def test_SDL_FRectEqualsEpsilon():
    r1 = sdl2.SDL_FRect(0, 0, 1.5, 1.2)
    r2 = sdl2.SDL_FRect(0, 0, 1.6, 1.1)
    assert sdl2.SDL_FRectEqualsEpsilon(r1, r2, 0.11)
    assert not sdl2.SDL_FRectEqualsEpsilon(r1, r2, 0.05)
    r2 = sdl2.SDL_FRect(0.01, 0.01, 1.5, 1.2)
    assert sdl2.SDL_FRectEqualsEpsilon(r1, r2, 0.011)
    assert not sdl2.SDL_FRectEqualsEpsilon(r1, r2, 0.001)

def test_SDL_FRectEquals():
    r1 = sdl2.SDL_FRect(0, 0, 1.5, 1.2)
    r2 = sdl2.SDL_FRect(0, 0, 0.1 * 15, 0.1 * 12)
    assert sdl2.SDL_FRectEquals(r1, r2)
    r2 = sdl2.SDL_FRect(-1, 2, 1.5, 1.2)
    assert not sdl2.SDL_FRectEquals(r1, r2)
    r2 = sdl2.SDL_FRect(0, 0, 1.5, 1.3)
    assert not sdl2.SDL_FRectEquals(r1, r2)
