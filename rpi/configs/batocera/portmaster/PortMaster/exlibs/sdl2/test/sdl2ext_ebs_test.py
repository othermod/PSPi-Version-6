import sys
import pytest
from sdl2.ext.ebs import Entity, System, Applicator, World


# Define some classes for testing the module

class Position(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class Movement(object):
    def __init__(self, vx=0, vy=0):
        self.vx = vx
        self.vy = vy

class PositionEntity(Entity):
    def __init__(self, world, x=0, y=0):
        self.position = Position(x, y)

class MovingEntity(Entity):
    def __init__(self, world, x=0, y=0, vx=0, vy=0):
        self.position = Position(x, y)
        self.movement = Movement(vx, vy)

class PosEntity(Entity):
    def __init__(self, world, x=0, y=0):
        self.pos = Position(x, y)

class PositionSystem(System):
    def __init__(self):
        super(PositionSystem, self).__init__()
        self.componenttypes = (Position,)

    def process(self, world, components):
        for c in components:
            c.x += 1
            c.y += 1

class MovementApplicator(Applicator):
    def __init__(self):
        super(MovementApplicator, self).__init__()
        self.componenttypes = (Position, Movement)

    def process(self, world, componentsets):
        for p, m in componentsets:
            p.x += m.vx
            p.y += m.vy


# Test the classes of the module

class TestExtEntity(object):
    __tags__ = ["ebs", "sdl2ext"]

    def test_init(self):
        world = World()
        world.add_system(PositionSystem())

        e = Entity(world)
        e2 = Entity(world)
        assert isinstance(e, Entity)
        assert isinstance(e2, Entity)
        assert e != e2

        p = PositionEntity(world)
        assert isinstance(p, PositionEntity)
        assert isinstance(p, Entity)

    def test_id(self):
        world = World()
        ent1 = Entity(world)
        ent2 = Entity(world)
        assert ent1.id != ent2.id

    def test_world(self):
        world = World()
        world2 = World()
        ent1 = Entity(world)
        ent2 = Entity(world2)
        assert ent1.world == world
        assert ent1.world != world2
        assert ent2.world == world2
        assert ent2.world != world
        assert ent1.world != ent2.world

    def test_delete(self):
        w = World()
        e1 = Entity(w)
        e2 = Entity(w)

        assert len(w.entities) == 2
        e1.delete()
        assert len(w.entities) == 1
        e2.delete()
        assert len(w.entities) == 0

        # The next two should have no effect
        e1.delete()
        e2.delete()

    def test__inheritance(self):
        world = World()

        pos1 = PositionEntity(world)
        pos2 = PositionEntity(world, 10, 10)
        for p in (pos1, pos2):
            assert isinstance(p, PositionEntity)
            assert isinstance(p, Entity)
            assert isinstance(p.position, Position)

    def test__access(self):
        world = World()
        pos1 = PositionEntity(world)
        pos2 = PosEntity(world)

        pos1.position.x = 10

        # components are _always_ identified by a lower-case class name.
        def sx(p, v):
            p.pos.x = v
        with pytest.raises(AttributeError):
            sx(pos2, 10)


class TestExtWorld(object):
    __tags__ = ["ebs", "sdl2ext"]

    def test_init(self):
        w = World()
        assert isinstance(w, World)

    def test_add_remove_system(self):
        world = World()
        assert isinstance(world, World)

        class SimpleSystem(object):
            def __init__(self):
                self.componenttypes = (Position,)

            def process(self, world, components):
                pass

        for method in (world.add_system, world.remove_system):
            for val in (None, "Test", Position, Entity(world)):
                with pytest.raises(ValueError):
                    method(val)

        psystem = SimpleSystem()
        world.add_system(psystem)
        assert len(world.systems) != 0
        assert psystem in world.systems
        world.remove_system(psystem)
        assert len(world.systems) == 0
        assert psystem not in world.systems

        psystem = PositionSystem()
        world.add_system(psystem)
        assert len(world.systems) != 0
        assert psystem in world.systems

        entity = PositionEntity(world)
        assert isinstance(entity.position, Position)

        world.remove_system(psystem)
        assert len(world.systems) == 0
        assert psystem not in world.systems

        # The data must stay intact in the world, even if the processing
        # system has been removed.
        assert isinstance(entity.position, Position)

    def test_entities(self):
        w = World()
        assert len(w.entities) == 0

        for x in range(100):
            Entity(w)
        assert len(w.entities) == 100

    def test_delete(self):
        w = World()
        e1 = Entity(w)
        e2 = Entity(w)

        assert len(w.entities) == 2
        w.delete(e1)
        assert len(w.entities) == 1
        w.delete(e2)
        assert len(w.entities) == 0

        # The next two should have no effect
        w.delete(e1)
        w.delete(e2)

    def test_delete_entities(self):
        w = World()
        e1 = Entity(w)
        e2 = Entity(w)

        assert len(w.entities) == 2
        w.delete_entities((e1, e2))
        assert len(w.entities) == 0
        # The next should have no effect
        w.delete_entities((e1, e2))

    def test_get_entities(self):
        w = World()
        e1 = PositionEntity(w, 1, 1)
        e2 = PositionEntity(w, 1, 2)
        assert len(w.get_entities(e1.position)) == 1
        e2.position.y = 1
        assert len(w.get_entities(e1.position)) == 2


class TestExtSystem(object):
    __tags__ = ["ebs", "sdl2ext"]

    def test_init(self):
        world = World()
        with pytest.raises(ValueError):
            world.add_system(None)
        with pytest.raises(ValueError):
            world.add_system(1234)
        with pytest.raises(ValueError):
            world.add_system("Test")

        class ErrornousSystem(System):
            def __init__(self):
                super(ErrornousSystem, self).__init__()

        esystem = ErrornousSystem()
        # No component types defined.
        with pytest.raises(ValueError):
            world.add_system(esystem)
        assert len(world.systems) == 0

        psystem = PositionSystem()
        world.add_system(psystem)
        assert psystem in world.systems

    def test_process(self):
        world = World()

        class ErrornousSystem(System):
            def __init__(self):
                super(ErrornousSystem, self).__init__()
                self.componenttypes = (Position,)

        esystem = ErrornousSystem()
        world.add_system(esystem)
        for x in range(10):
            PositionEntity(world)
        assert esystem in world.systems
        with pytest.raises(NotImplementedError):
            world.process()

        world2 = World()
        psystem = PositionSystem()
        world2.add_system(psystem)
        for x in range(10):
            PositionEntity(world2)
        assert psystem in world2.systems
        world2.process()
        for c in world2.components[Position].values():
            assert c.x == 1
            assert c.y == 1
        world2.process()
        for c in world2.components[Position].values():
            assert c.x == 2
            assert c.y == 2


class TestExtApplicator(object):
    __tags__ = ["ebs", "sdl2ext"]

    def test_init(self):
        world = World()

        class ErrornousApplicator(Applicator):
            def __init__(self):
                super(ErrornousApplicator, self).__init__()

        eapplicator = ErrornousApplicator()
        # No component types defined.
        with pytest.raises(ValueError):
            world.add_system(eapplicator)
        assert len(world.systems) == 0

        mapplicator = MovementApplicator()
        world.add_system(mapplicator)
        assert mapplicator in world.systems

    def test_process(self):
        world = World()

        class ErrornousApplicator(Applicator):
            def __init__(self):
                super(ErrornousApplicator, self).__init__()
                self.componenttypes = (Position, Movement)

        eapplicator = ErrornousApplicator()
        world.add_system(eapplicator)
        for x in range(10):
            MovingEntity(world)
        assert eapplicator in world.systems
        with pytest.raises(NotImplementedError):
            world.process()

        world2 = World()
        mapplicator = MovementApplicator()
        world2.add_system(mapplicator)
        for x in range(10):
            MovingEntity(world2, vx=1, vy=1)
        assert mapplicator in world2.systems
        world2.process()
        for c in world2.components[Position].values():
            assert c.x == 1
            assert c.y == 1
        world2.process()
        for c in world2.components[Position].values():
            assert c.x == 2
            assert c.y == 2
