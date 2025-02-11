"""
A component-based entity system framework.

ebs loosely follows a component oriented pattern to separate object
instances, carried data and processing logic within applications or
games. It uses a entity based approach, in which object instances are
unique identifiers, while their data is managed within components, which
are separately stored. For each individual component type a processing
system will take care of all necessary updates for the World
environment.
"""
import uuid
import inspect

from .compat import *

__all__ = ["Entity", "World", "System", "Applicator"]


class Entity(object):
    """A simple object entity.

    An entity is a specific object living in the application world. It
    does not carry any data or application logic, but merely acts as
    identifier label for data that is maintained in the application
    world itself.

    As such, it is an composition of components, which would not exist
    without the entity identifier. The entity itself is non-existent to
    the application world as long as it does not carry any data that can
    be processed by a system within the application world.
    """
    def __new__(cls, world, *args, **kwargs):
        if not isinstance(world, World):
            raise TypeError("world must be a World")
        entity = object.__new__(cls)
        entity._id = uuid.uuid4()
        entity._world = world
        world.entities.add(entity)
        return entity

    def __repr__(self):
        return "Entity(id=%s)" % self._id

    def __hash__(self):
        return hash(self._id)

    def __getattr__(self, name):
        """Gets the component data related to the Entity."""
        if name in ("_id", "_world"):
            return object.__getattribute__(self, name)
        try:
            ctype = self._world._componenttypes[name]
        except KeyError:
            raise AttributeError("object '%r' has no attribute '%r'" % \
                (self.__class__.__name__, name))
        return self._world.components[ctype][self]

    def __setattr__(self, name, value):
        """Sets the component data related to the Entity."""
        if name in ("_id", "_world"):
            object.__setattr__(self, name, value)
        else:
            # If the value is a compound component (e.g. a Button
            # inheriting from a Sprite), it needs to be added to all
            # supported component type instances.
            mro = inspect.getmro(value.__class__)
            if type in mro:
                stop = mro.index(type)
            else:
                stop = mro.index(object)
            mro = mro[0:stop]
            wctypes = self._world.componenttypes
            for clstype in mro:
                if clstype not in wctypes:
                    self._world.add_componenttype(clstype)
                self._world.components[clstype][self] = value

    def __delattr__(self, name):
        """Deletes the component data related to the Entity."""
        if name in ("_id", "_world"):
            raise AttributeError("'%s' cannot be deleted.", name)
        try:
            ctype = self._world._componenttypes[name]
        except KeyError:
            raise AttributeError("object '%s' has no attribute '%s'" % \
                (self.__class__.__name__, name))
        del self._world.components[ctype][self]

    def delete(self):
        """Removes the Entity from the world it belongs to."""
        self.world.delete(self)

    @property
    def id(self):
        """The id of the Entity."""
        return self._id

    @property
    def world(self):
        """The world the Entity resides in."""
        return self._world


class World(object):
    """A simple application world.

    An application world defines the combination of application data and
    processing logic and how the data will be processed. As such, it is
    a container object in which the application is defined.

    The application world maintains a set of entities and their related
    components as well as a set of systems that process the data of the
    entities. Each processing system within the application world only
    operates on a certain set of components, but not all components of
    an entity at once.

    The order in which data is processed depends on the order of the
    added systems.
    """
    def __init__(self):
        """Creates a new World instance."""
        self.entities = set()
        self._systems = []
        self.components = {}
        self._componenttypes = {}

    def _system_is_valid(self, system):
        """Checks, if the passed object fulfills the requirements for being
        a processing system.
        """
        return hasattr(system, "componenttypes") and \
            isiterable(system.componenttypes) and \
            hasattr(system, "process") and \
            callable(system.process)

    def combined_components(self, comptypes):
        """A generator view on combined sets of component items."""
        comps = self.components
        keysets = [set(comps[ctype]) for ctype in comptypes]
        valsets = [comps[ctype] for ctype in comptypes]
        entities = keysets[0].intersection(*keysets[1:])
        for ekey in entities:
            yield tuple(component[ekey] for component in valsets)

    def add_componenttype(self, classtype):
        """Adds a supported component type to the World."""
        if classtype in self._componenttypes.values():
            return
        self.components[classtype] = {}
        self._componenttypes[classtype.__name__.lower()] = classtype

    def delete(self, entity):
        """Removes an Entity from the World, including all its data."""
        for componentset in self.components.values():
            componentset.pop(entity, None)
        self.entities.discard(entity)

    def delete_entities(self, entities):
        """Removes multiple entities from the World at once."""
        eids = set(entities)
        if ISPYTHON2:
            for compkey, compset in self.components.viewitems():
                keys = set(compset.viewkeys()) - eids
                self.components[compkey] = dict((k, compset[k]) for k in keys)
        else:
            for compkey, compset in self.components.items():
                keys = set(compset.keys()) - eids
                self.components[compkey] = dict((k, compset[k]) for k in keys)
        self.entities -= set(entities)

    def get_components(self, componenttype):
        """Gets all existing components for a sepcific component type.

        If no components could be found for the passed component types, an
        empty list is returned.
        """
        if componenttype in self.components:
            return self.components[componenttype].values()
        return []

    def get_entities(self, component):
        """Gets the entities using the passed component.

        Note: this will not perform an identity check on the component
        but rely on its __eq__ implementation instead.
        """
        compset = self.components.get(component.__class__, None)
        if compset is None:
            return []
        return [e for e in compset if compset[e] == component]

    def add_system(self, system):
        """Adds a processing system to the world.

        The system will be added as last item in the processing order. Every
        object can be added as long as it contains

           * a 'componenttypes' attribute that is iterable and contains the
            class types to be processed
           * a 'process()' method, receiving two arguments, the world and
             components

        If the object contains a 'is_applicator' attribute that evaluates to
        True, the system will operate on combined sets of components.
        """
        if not self._system_is_valid(system):
            raise ValueError("system must have componenttypes and a process method")
        for classtype in system.componenttypes:
            if classtype not in self.components:
                self.add_componenttype(classtype)
        self._systems.append(system)

    def insert_system(self, index, system):
        """Adds a processing system to the world.

        The system will be added at the specific position of the
        processing order.
        """
        if not self._system_is_valid(system):
            raise ValueError("system must have componenttypes and a process method")
        for classtype in system.componenttypes:
            if classtype not in self.components:
                self.add_componenttype(classtype)
        self._systems.insert(index, system)

    def remove_system(self, system):
        """Removes a processing system from the world."""
        self._systems.remove(system)

    def process(self):
        """Processes all components within their corresponding systems."""
        components = self.components
        for system in self._systems:
            s_process = system.process
            if getattr(system, "is_applicator", False):
                comps = self.combined_components(system.componenttypes)
                s_process(self, comps)
            else:
                if ISPYTHON2:
                    for ctype in system.componenttypes:
                        s_process(self, components[ctype].viewvalues())
                else:
                    for ctype in system.componenttypes:
                        s_process(self, components[ctype].values())

    @property
    def systems(self):
        """Gets the systems bound to the world."""
        return tuple(self._systems)

    @property
    def componenttypes(self):
        """Gets the supported component types of the world."""
        return self._componenttypes.values()


class System(object):
    """A processing system for component data.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    def __init__(self):
        self.componenttypes = None

    def process(self, world, components):
        """Processes component items.

        This must be implemented by inheriting classes.
        """
        raise NotImplementedError()


class Applicator(System):
    """A processing system for combined data sets."""
    def __init__(self):
        super(Applicator, self).__init__()
        self.is_applicator = True
