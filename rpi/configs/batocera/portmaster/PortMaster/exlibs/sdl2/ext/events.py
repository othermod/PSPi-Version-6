"""General purpose event handling routines"""
from .compat import *

__all__ = ["EventHandler", "MPEventHandler"]

_HASMP = True
try:
    from multiprocessing import Pool
except ImportError:
    _HASMP = False


class EventHandler(object):
    """A simple event handling class, which manages callbacks to be
    executed.
    """
    def __init__(self, sender):
        self.callbacks = []
        self.sender = sender

    def __call__(self, *args):
        """Executes all callbacks.

        Executes all connected callbacks in the order of addition,
        passing the sender of the EventHandler as first argument and the
        optional args as second, third, ... argument to them.
        """
        return [callback(self.sender, *args) for callback in self.callbacks]

    def __iadd__(self, callback):
        """Adds a callback to the EventHandler."""
        self.add(callback)
        return self

    def __isub__(self, callback):
        """Removes a callback from the EventHandler."""
        self.remove(callback)
        return self

    def __len__(self):
        """Gets the amount of callbacks connected to the EventHandler."""
        return len(self.callbacks)

    def __getitem__(self, index):
        return self.callbacks[index]

    def __setitem__(self, index, value):
        self.callbacks[index] = value

    def __delitem__(self, index):
        del self.callbacks[index]

    def add(self, callback):
        """Adds a callback to the EventHandler."""
        if not callable(callback):
            raise TypeError("callback mus be callable")
        self.callbacks.append(callback)

    def remove(self, callback):
        """Removes a callback from the EventHandler."""
        self.callbacks.remove(callback)


def _mp_callback(args):
    # args = (function, sender, (args))
    fargs = args[2]
    return args[0](args[1], *fargs)


class MPEventHandler(EventHandler):
    """An asynchronous event handling class in which callbacks are
    executed in parallel.

    It is the responsibility of the caller code to ensure that every
    object used maintains a consistent state. The MPEventHandler class
    will not apply any locks, synchronous state changes or anything else
    to the arguments being used. Consider it a "fire-and-forget" event
    handling strategy
    """
    def __init__(self, sender, maxprocs=None):
        if not _HASMP:
            raise UnsupportedError("no multiprocessing support found")
        super(MPEventHandler, self).__init__(sender)
        self.maxprocs = maxprocs

    def __call__(self, *args):
        if self.maxprocs is not None:
            pool = Pool(processes=self.maxprocs)
        else:
            pool = Pool()
        psize = len(self.callbacks)
        pv = zip(self.callbacks, [self.sender] * psize, [args[:]] * psize)
        results = pool.map_async(_mp_callback, pv)
        pool.close()
        pool.join()
        return results
