import os
import sys
import urllib
if sys.version_info[0] < 3:
    import urllib2
else:
    import urllib.request as urllib2
import pytest
from sdl2.ext import resources


def test_open_zipfile():
    fpath = os.path.join(os.path.dirname(__file__), "resources")
    zfile = os.path.join(fpath, "resources.zip")

    # resources.zip is a packed version of resources/, which at
    # least contains
    #
    # resources/rwopstest.txt
    # resources/surfacetest.bmp

    resfile = resources.open_zipfile(zfile, "rwopstest.txt", "resources")
    assert resfile is not None
    resfile = resources.open_zipfile(zfile, "resources/rwopstest.txt")
    assert resfile is not None

    with pytest.raises(KeyError):
        resources.open_zipfile(zfile, "invalid")
    with pytest.raises(KeyError):
        resources.open_zipfile(zfile, None)
    with pytest.raises(KeyError):
        resources.open_zipfile(zfile,
                        "rwopstest.txt", "data")
    with pytest.raises(KeyError):
        resources.open_zipfile(zfile,
                        "rwopstest.txt", 1234)
    with pytest.raises(KeyError):
        resources.open_zipfile(zfile,
                        None, None)

    with pytest.raises(TypeError):
        resources.open_zipfile(None,
                        "rwopstest.txt")
    with pytest.raises(TypeError):
        resources.open_zipfile(None, None)
    with pytest.raises(TypeError):
        resources.open_zipfile(None,
                        "rwopstest.txt", "resources")

def test_open_tarfile():
    fpath = os.path.join(os.path.dirname(__file__), "resources")
    tfile = os.path.join(fpath, "resources.tar.gz")

    # resources.tar.gz is a packed version of resources/, which at
    # least contains
    #
    # resources/rwopstest.txt
    # resources/surfacetest.bmp

    resfile = resources.open_tarfile(tfile, "rwopstest.txt", "resources")
    assert resfile is not None
    resfile = resources.open_tarfile(tfile, "resources/rwopstest.txt")
    assert resfile is not None

    # TODO: refine the error handling in open_tarfile()
    with pytest.raises(KeyError):
        resources.open_tarfile(tfile, "invalid")
    with pytest.raises(AttributeError):
        resources.open_tarfile(tfile, None)
    with pytest.raises(KeyError):
        resources.open_tarfile(tfile,
                        "rwopstest.txt", "data")
    with pytest.raises(KeyError):
        resources.open_tarfile(tfile,
                        "rwopstest.txt", 1234)
    with pytest.raises(AttributeError):
        resources.open_tarfile(tfile,
                        None, None)

    with pytest.raises(ValueError):
        resources.open_tarfile(None,
                        "rwopstest.txt")
    with pytest.raises(ValueError):
        resources.open_tarfile(None, None)
    with pytest.raises(ValueError):
        resources.open_tarfile(None,
                        "rwopstest.txt", "resources")

def test_open_url():
    if sys.version_info[0] < 3:
        p2url = urllib.pathname2url
    else:
        p2url = urllib2.pathname2url

    fpath = os.path.join(os.path.dirname(__file__), "resources")
    fpath = os.path.abspath(fpath)
    tfile = os.path.join(fpath, "rwopstest.txt")
    urlpath = "file:%s" % p2url(tfile)
    resfile = resources.open_url(urlpath)
    assert resfile is not None

    tfile = os.path.join(fpath, "invalid")
    urlpath = "file:%s" % p2url(tfile)
    with pytest.raises(urllib2.URLError):
        resources.open_url(urlpath)


class TestSDL2ExtResources(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        with pytest.raises(ValueError):
            resources.Resources("invalid")

        res = resources.Resources()
        assert isinstance(res, resources.Resources)
        with pytest.raises(KeyError):
            res.get("surfacetest.bmp")

        fpath = os.path.join(os.path.dirname(__file__), "resources")
        res = resources.Resources(fpath)
        assert res.get("rwopstest.txt") is not None
        assert res.get("surfacetest.bmp") is not None

        res2 = resources.Resources(__file__)
        assert res2.get("rwopstest.txt") is not None
        assert res2.get("surfacetest.bmp") is not None

        res3 = resources.Resources(__file__, "resources")
        assert res3.get("rwopstest.txt") is not None
        assert res3.get("surfacetest.bmp") is not None

    def test_add(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")
        sfile = os.path.join(fpath, "surfacetest.bmp")
        zfile = os.path.join(fpath, "resources.zip")

        res = resources.Resources()
        res.add(sfile)
        with pytest.raises(KeyError):
            res.get("rwopstest.txt")
        assert res.get("surfacetest.bmp") is not None

        res.add(zfile)
        assert res.get("rwopstest.txt") is not None
        assert res.get("surfacetest.bmp") is not None

        with pytest.raises(TypeError):
            res.add(None)
        with pytest.raises(ValueError):
            res.add("invalid_name.txt")

    def test_add_file(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")
        sfile = os.path.join(fpath, "surfacetest.bmp")
        zfile = os.path.join(fpath, "resources.zip")

        res = resources.Resources()
        res.add_file(sfile)
        res.add_file(zfile)

        with pytest.raises(KeyError):
            res.get("rwopstest.txt")
        assert res.get("surfacetest.bmp") is not None
        assert res.get("resources.zip") is not None

        with pytest.raises(TypeError):
            res.add_file(None)
        with pytest.raises(ValueError):
            res.add_file("invalid_name.txt")

    def test_add_archive(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")
        zfile = os.path.join(fpath, "resources.zip")
        tfile = os.path.join(fpath, "resources.tar.gz")

        res = resources.Resources()
        res.add_archive(zfile)

        assert res.get("surfacetest.bmp") is not None
        assert res.get("rwopstest.txt") is not None
        with pytest.raises(KeyError):
            res.get("resources.zip")

        with pytest.raises(TypeError):
            res.add_archive(None)
        with pytest.raises(ValueError):
            res.add_archive("invalid_name.txt")

        res = resources.Resources()
        res.add_archive(tfile, typehint="targz")
        assert res.get("surfacetest.bmp") is not None
        assert res.get("rwopstest.txt") is not None
        with pytest.raises(KeyError):
            res.get("resources.tar.gz")

    def test_get(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")

        for path in (fpath, None):
            res = resources.Resources(path)

            with pytest.raises(KeyError):
                res.get("invalid_file.txt")
            with pytest.raises(KeyError):
                res.get(None)
            with pytest.raises(KeyError):
                res.get(123456)
            if path is None:
                with pytest.raises(KeyError):
                    res.get("surfacetest.bmp")
                with pytest.raises(KeyError):
                    res.get("rwopstest.txt")
            else:
                assert res.get("surfacetest.bmp") is not None
                assert res.get("rwopstest.txt") is not None

    def test_get_filelike(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")
        zfile = os.path.join(fpath, "resources.zip")
        pfile = os.path.join(fpath, "rwopstest.txt")

        res = resources.Resources()
        res.add(zfile)

        v1 = res.get_filelike("rwopstest.txt")
        v2 = res.get_filelike("surfacetest.bmp")
        assert type(v1) == type(v2)

        res.add(pfile)

        v1 = res.get_filelike("rwopstest.txt")
        v2 = res.get_filelike("surfacetest.bmp")
        assert type(v1) != type(v2)

        with pytest.raises(KeyError):
            res.get_filelike(None)
        with pytest.raises(KeyError):
            res.get_filelike("invalid")
        with pytest.raises(KeyError):
            res.get_filelike(1234)

    def test_get_path(self):
        fpath = os.path.join(os.path.dirname(__file__), "resources")
        zfile = os.path.join(fpath, "resources.zip")
        pfile = os.path.join(fpath, "rwopstest.txt")

        res = resources.Resources()
        res.add(zfile)
        res.add(pfile)

        zpath = res.get_path("surfacetest.bmp")
        assert zpath.find("surfacetest.bmp@") != -1
        assert zpath != zfile
        ppath = res.get_path("rwopstest.txt")
        assert ppath.find("rwopstest.txt") != -1

        with pytest.raises(KeyError):
            res.get_path(None)
        with pytest.raises(KeyError):
            res.get_path("invalid")
        with pytest.raises(KeyError):
            res.get_path(1234)

    def test_scan(self):
        fpath = os.path.join(os.path.dirname(__file__))
        res = resources.Resources()
        res.scan(fpath)
        assert res.get("rwopstest.txt") is not None
        assert res.get("surfacetest.bmp") is not None

        with pytest.raises(ValueError):
            res.scan("invalid")
        with pytest.raises(ValueError):
            res.scan(fpath, "invalid")
        with pytest.raises(Exception):
            res.scan(12345)

        res = resources.Resources()
        res.scan(fpath, "resources")
        assert res.get("rwopstest.txt") is not None
        assert res.get("surfacetest.bmp") is not None
