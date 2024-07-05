"""
A simple particle engine implementation.
"""
from .compat import *
from .ebs import System

__all__ = ["Particle", "ParticleEngine"]


class Particle(object):
    """A simple particle component type.

    The Particle component only contains information about a x- and
    y-coordinate and its current life time. The life time will be
    decreased by 1, everytime the particle is processed by the
    ParticleEngine.
    """
    def __init__(self, x, y, life):
        """Creates a new Particle with a x-/y-position and life time."""
        super(Particle, self).__init__()
        self.x = x
        self.y = y
        self.life = life

    @property
    def position(self):
        """The position of the Particle as tuple."""
        return self.x, self.y

    @position.setter
    def position(self, value):
        """The position of the Particle as tuple."""
        self.x = value[0]
        self.y = value[1]


class ParticleEngine(System):
    """A simple particle processing system.

    The ParticleEngine takes care of creating, updating and deleting
    particles via callback functions. It only decreases the life of the
    particles by itself and marks them as dead, once the particle's life
    attribute has reached 0 or below.
    """
    def __init__(self):
        """Creates a new ParticleEngine."""
        super(ParticleEngine, self).__init__()
        self.componenttypes = (Particle,)
        self._createfunc = None
        self._deletefunc = None
        self._updatefunc = None

    def process(self, world, components):
        """Processes all particle components, decreasing their life by 1.

        Once the life of all particle components has been decreased
        properly and the particles considered dead (life <= 0) are
        identified, the creation, update and deletion callbacks are
        invoked.

        The creation callback takes the passed world as first and the
        list of dead particles as second argument.

            def particle_createfunc(world, list_of_dead_ones):
                ...

        Afterwards the still living particles are passed to the update
        callback, which also take the passed world as first and the
        living particles as set as second argument.

            def particle_updatefunc(world, set_of_living_ones):
                ...

        Finally, the dead particles need to be deleted in some way or
        another, which is done by the deletion callback, taking the
        passed world as first and the list of dead particles as second
        argument.

            def particle_deletefunc(world, list_of_dead_ones):
                ...
        """
        deadones = []
        dappend = deadones.append
        for p in components:
            p.life -= 1
            if p.life <= 0:
                dappend(p)
        self.createfunc(world, deadones)
        self.updatefunc(world, set(components) - set(deadones))
        self.deletefunc(world, deadones)

    @property
    def createfunc(self):
        """The function to be used for creating new particles."""
        return self._createfunc

    @createfunc.setter
    def createfunc(self, value):
        """The function to be used for creating new particles."""
        if not callable(value):
            raise TypeError("createfunc must be callable")
        self._createfunc = value

    @property
    def deletefunc(self):
        """The function to be used for deleting dead particles."""
        return self._deletefunc

    @deletefunc.setter
    def deletefunc(self, value):
        """The function to be used for deletíng dead particles."""
        if not callable(value):
            raise TypeError("deletefunc must be callable")
        self._deletefunc = value

    @property
    def updatefunc(self):
        """The function to be used for updating particles."""
        return self._updatefunc

    @updatefunc.setter
    def updatefunc(self, value):
        """The function to be used for updating particles."""
        if not callable(value):
            raise TypeError("updatefunc must be callable")
        self._updatefunc = value
