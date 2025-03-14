import pytest
from sdl2.ext import algorithms as alg


def test_cohensutherland():
    # Test a simple diagonal intersection
    ret = alg.cohensutherland(1, 2, 2, 1, 0, 0, 4, 4)
    assert ret == (1, 1, 2, 2)

    # Test handling of swapped top/bottom values
    ret = alg.cohensutherland(1, 1, 2, 2, 0, 0, 4, 4)
    assert ret == (1, 1, 2, 2)

    # Test partial intersection
    ret = alg.cohensutherland(1, 1, 2, 2, 1.5, 0, 1.5, 1.5)
    assert ret == (1.5, 1, 1.5, 1.5)

    # Test non-intersecting line
    ret = alg.cohensutherland(1, 2, 2, 1, 0, 0, 0, 4)
    assert ret == (None, None, None, None)


def test_liangbarsky():
    # Test a simple diagonal intersection
    ret = alg.liangbarsky(1, 2, 2, 1, 0, 0, 4, 4)
    assert ret == (1, 1, 2, 2)

    # Test handling of swapped top/bottom values
    ret = alg.liangbarsky(1, 1, 2, 2, 0, 0, 4, 4)
    assert ret == (1, 1, 2, 2)

    # Test partial intersection
    ret = alg.liangbarsky(1, 1, 2, 2, 1.5, 0, 1.5, 1.5)
    assert ret == (1.5, 1, 1.5, 1.5)

    # Test non-intersecting line
    ret = alg.liangbarsky(1, 2, 2, 1, 0, 0, 0, 4)
    assert ret == (None, None, None, None)


def test_clipline():
    # Test a simple diagonal intersection w/ default method
    ret = alg.clipline(1, 2, 2, 1, 0, 0, 4, 4)
    assert ret == (1, 1, 2, 2)

    # Test a simple diagonal intersection w/ Liang-Barsky
    ret = alg.clipline(1, 2, 2, 1, 0, 0, 4, 4, method='liangbarsky')
    assert ret == (1, 1, 2, 2)

    # Test a simple diagonal intersection w/ Cohen-Sutherland
    ret = alg.clipline(1, 2, 2, 1, 0, 0, 4, 4, method='cohensutherland')
    assert ret == (1, 1, 2, 2)

    # Test exception with unknown clipping method
    with pytest.raises(ValueError):
        alg.clipline(1, 2, 2, 1, 0, 0, 4, 4, method='cohenlebowski')


def test_point_on_line():
    line = [(1, 1), (3, 3)]
    assert alg.point_on_line(line[0], line[1], (2, 2))
    assert alg.point_on_line(line[0], line[1], (3, 3))
    assert alg.point_on_line(line[1], line[0], (2, 2))
    assert not alg.point_on_line(line[0], line[1], (3, 4))
