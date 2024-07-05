import sys
import pytest
from sdl2.ext import particles


class TestExtParticle(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        p = particles.Particle(0, 0, 0)
        assert isinstance(p, particles.Particle)
        assert p.x == p.y == p.life == 0
        p = particles.Particle(1, 2, 3)
        assert isinstance(p, particles.Particle)
        assert p.x == 1
        assert p.y == 2
        assert p.life == 3

    def test_xy_position(self):
        for x in range(-100, 100):
            for y in range(-100, 100):
                p = particles.Particle(x, y, 1)
                assert p.position == (x, y)
                assert p.x == x
                assert p.y == y
                p.position = x + 1, y + 1
                assert p.position == (x + 1, y + 1)
                assert p.x == x + 1
                assert p.y == y + 1
                p.x = x
                assert p.position == (x, y + 1)
                assert p.x == x
                assert p.y == y + 1
                p.y = y
                assert p.position == (x, y)
                assert p.x == x
                assert p.y == y

    def test_life(self):
        for life in range(-100, 100):
            p = particles.Particle(0, 0, life)
            assert p.life == life


class TestExtParticleEngine(object):
    __tags__ = ["sdl2ext"]

    def test_init(self):
        engine = particles.ParticleEngine()
        assert isinstance(engine, particles.ParticleEngine)
        assert particles.Particle in engine.componenttypes
        assert engine.createfunc is None
        assert engine.deletefunc is None
        assert engine.updatefunc is None

    def test_createfunc(self):
        def func(w, c):
            pass
        engine = particles.ParticleEngine()
        assert engine.createfunc is None
        engine.createfunc = func
        assert engine.createfunc == func

        def setf(x, f):
            x.createfunc = f
        with pytest.raises(TypeError):
            setf(engine, None)
        with pytest.raises(TypeError):
            setf(engine, "Test")
        with pytest.raises(TypeError):
            setf(engine, 1234)

    def test_deletefunc(self):
        def func(w, c):
            pass
        engine = particles.ParticleEngine()
        assert engine.deletefunc is None
        engine.deletefunc = func
        assert engine.deletefunc == func

        def setf(x, f):
            x.deletefunc = f
        with pytest.raises(TypeError):
            setf(engine, None)
        with pytest.raises(TypeError):
            setf(engine, "Test")
        with pytest.raises(TypeError):
            setf(engine, 1234)

    def test_updatefunc(self):
        def func(w, c):
            pass
        engine = particles.ParticleEngine()
        assert engine.updatefunc is None
        engine.updatefunc = func
        assert engine.updatefunc == func

        def setf(x, f):
            x.updatefunc = f
        with pytest.raises(TypeError):
            setf(engine, None)
        with pytest.raises(TypeError):
            setf(engine, "Test")
        with pytest.raises(TypeError):
            setf(engine, 1234)

    def test_process(self):
        def cfunc(w, c):
            assert len(c) == w["runs"]
            for p in c:
                assert p.life <= 0

        def ufunc(w, c):
            assert len(c) == 100 - w["runs"]
            for p in c:
                assert p.life >= 1

        def dfunc(w, c):
            assert len(c) == w["runs"]
            for p in c:
                assert p.life <= 0

        plist = []
        for x in range(2, 102):
            plist.append(particles.Particle(x, x, x - 1))

        engine = particles.ParticleEngine()
        engine.createfunc = cfunc
        engine.updatefunc = ufunc
        engine.deletefunc = dfunc
        world = {"runs": 1}
        engine.process(world, plist)
        world["runs"] = 2
        engine.process(world, plist)
