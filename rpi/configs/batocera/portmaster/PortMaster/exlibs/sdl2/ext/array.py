import ctypes

__all__ = ["CTypesView", "to_ctypes", "to_list", "to_tuple", "create_array",
           "MemoryView"]


# Hack around an import error using relative import paths in Python 2.7
_ARRAY = __import__("array")


def to_tuple(dataseq):
    """Converts a ``ctypes`` array to a tuple."""
    return tuple(dataseq)


def to_list(dataseq):
    """Converts a ``ctypes`` array to a list."""
    return list(dataseq)


def to_ctypes(dataseq, dtype, mcount=0):
    """Converts an arbitrary sequence to a ``ctypes`` array of a given type.

    Args:
        dataseq: A sequence to convert to a ``ctypes`` array.
        dtype (class): The ``ctypes`` data type to use for the array (e.g.
            ``ctypes.c_uint8``).
        mcount (int, optional): The number of elements in ``dataseq``. If
            not specified, this will be inferred automatically.

    Returns:
        tuple: A tuple in the form ``(valset, count)``, where ``valset`` is
        the converted ``ctypes`` array and ``count`` is the number of
        elements in the array.

    Raises:
        TypeError: if any elements in the passed sequence do not
            match the specified type.

    """
    if mcount > 0:
        count = mcount
    else:
        count = len(dataseq)
    if isinstance(dataseq, CTypesView):
        itemsize = ctypes.sizeof(dtype)
        if itemsize == 1:
            dataseq = dataseq.to_bytes()
        elif itemsize == 2:
            dataseq = dataseq.to_uint16()
        elif itemsize == 4:
            dataseq = dataseq.to_uint32()
        elif itemsize == 8:
            dataseq = dataseq.to_uint64()
        else:
            raise TypeError("unsupported data type for the passed CTypesView")
    valset = (count * dtype)(*dataseq)
    return valset, count


def create_array(obj, itemsize):
    """Creates an :obj:`array.array` copy of a given object.

    Args:
        obj: The object from which the array will be created.
        itemsize: The size (in bytes) of each item in the given object.

    Returns:
        :obj:`array.array`: The array created from the object.

    """
    if itemsize == 1:
        return _ARRAY.array("B", obj)
    elif itemsize == 2:
        return _ARRAY.array("H", obj)
    elif itemsize == 4:
        return _ARRAY.array("I", obj)
    elif itemsize == 8:
        return _ARRAY.array("d", obj)
    else:
        raise TypeError("unsupported data type")


class CTypesView(object):
    """A proxy for accessing byte-wise ``ctypes`` data types.

    This class provides read-write access for arbitrary ``ctypes`` objects
    that are iterable. In case the object does not provide a :func:`buffer`
    interface for direct access, a ``CTypesView`` can copy the object's contents
    into an internal buffer from which data can be retrieved.

    Depending on the item type stored in the iterable object, you might
    need to manually specify the object's item size (in bytes). Additionally,
    you may need to manually specify the number of items in the iterable if
    it does not properly return its length using the ``len`` function.

    For certain types, such as the bytearray, the original object must not be
    reassigned after being encapsuled and used in ctypes bindings if the
    contents are not copied.

    Args:
        obj: An arbitrary iterable ``ctypes`` object to access.
        itemsize (int, optional): The size (in bytes) of each item of the
            iterable object. Defaults to ``1``.
        docopy (bool, optional): If True, the view will be created for a copy
            of the object and will not modify the original ``ctypes`` instance.
            Defalts to False (original object will be modified).
        objsize (int, optional): The number of items in the iterable object.
            If not specified, the number of items will try to be inferred
            automatically. Defaults to ``None`` (automatic inferrence).

    """
    def __init__(self, obj, itemsize=1, docopy=False, objsize=None):
        self._obj = obj
        self._isshared = True
        self._view = None
        self._itemsize = itemsize
        self._create_view(itemsize, bool(docopy), objsize)

    def _create_view(self, itemsize, docopy, objsize):
        """Creates the view on the specified object."""
        self._isshared = not docopy
        bsize = 0
        if objsize is None:
            bsize = len(self._obj) * itemsize
        else:
            bsize = objsize * itemsize

        if docopy:
            self._obj = create_array(self._obj, itemsize)
        try:
            self._view = (ctypes.c_ubyte * bsize).from_buffer(self._obj)
        except AttributeError:
            # pypy ctypes arrays do not feature a from_buffer() method.
            self._isshared = False
            # in case we requested a copy earlier, we do not need to recreate
            # the array, since we have it already. In any other case, create
            # a byte array.
            if not docopy:
                # Try to determine the itemsize again for array
                # instances, just in case the user assumed it to work.
                if isinstance(self._obj, _ARRAY.array):
                    itemsize = self._obj.itemsize
                    bsize = len(self._obj) * itemsize
                self._obj = create_array(self._obj, itemsize)
            self._view = (ctypes.c_ubyte * bsize)(*bytearray(self._obj))

    def __repr__(self):
        dtype = type(self._obj).__name__
        bsize = self.bytesize
        return "CTypesView(type=%s, bytesize=%d, shared=%s)" % (dtype, bsize,
                                                                self.is_shared)

    def __len__(self):
        """Returns the length of the underlying object in bytes."""
        return self.bytesize

    def to_bytes(self):
        """Casts the object to an array of bytes.
        
        If the view was created with ``docopy = False`` (the default), the
        returned object provides direct read-write access to the object data.
        Otherwise, the returned object will only modify a copy of the data.

        Returns:
            :obj:`ctypes._Pointer`: A pointer to a :class:`ctypes.c_uint8`
            array.

        """
        castval = ctypes.POINTER(ctypes.c_uint8 * self.bytesize)
        return ctypes.cast(self.view, castval).contents

    def to_uint16(self):
        """Casts the object to an array of 16-bit unsigned ints.
        
        If the view was created with ``docopy = False`` (the default), the
        returned object provides direct read-write access to the object data.
        Otherwise, the returned object will only modify a copy of the data.

        Returns:
            :obj:`ctypes._Pointer`: A pointer to a :class:`ctypes.c_uint16`
            array.

        """
        castval = ctypes.POINTER(ctypes.c_uint16 * (self.bytesize // 2))
        return ctypes.cast(self.view, castval).contents

    def to_uint32(self):
        """Casts the object to an array of 32-bit unsigned ints.
        
        If the view was created with ``docopy = False`` (the default), the
        returned object provides direct read-write access to the object data.
        Otherwise, the returned object will only modify a copy of the data.

        Returns:
            :obj:`ctypes._Pointer`: A pointer to a :class:`ctypes.c_uint32`
            array.

        """
        castval = ctypes.POINTER(ctypes.c_uint32 * (self.bytesize // 4))
        return ctypes.cast(self.view, castval).contents

    def to_uint64(self):
        """Casts the object to an array of 64-bit unsigned ints.
        
        If the view was created with ``docopy = False`` (the default), the
        returned object provides direct read-write access to the object data.
        Otherwise, the returned object will only modify a copy of the data.

        Returns:
            :obj:`ctypes._Pointer`: A pointer to a :class:`ctypes.c_uint64`
            array.

        """
        castval = ctypes.POINTER(ctypes.c_uint64 * (self.bytesize // 8))
        return ctypes.cast(self.view, castval).contents

    @property
    def bytesize(self):
        """int: The size (in bytes) of the underlying object."""
        return ctypes.sizeof(self.view)

    @property
    def view(self):
        """Provides a read/write-aware ``ctypes`` view of the encapsuled
        object.
        
        """
        return self._view

    @property
    def is_shared(self):
        """bool: Whether any modifications to the view will also modify the
        underlying object.

        """
        return self._isshared

    @property
    def object(self):
        """The underlying object."""
        return self._obj


class MemoryView(object):
    """A class that provides read-write access to indexable ``ctypes`` objects.

    .. note::
       ``MemoryView`` makes heavy use of recursion for multi-dimensional
       access, making it slow for many use-cases. For better performance, the
       ``numpy`` library can be used for fast access to many array-like data
       types, but it may support fewer types of arbitrary objects than the
       ``MemoryView`` class.

    Args:
        source: An arbitrary indexable ``ctypes`` object to access.
        itemsize (int): The size (in bytes) of each item of the indexable
            object.
        strides (tuple): The length of each dimension in the object (e.g.
            ``(4, 3)`` for a 4 x 3 2D array).
        getfunc (function, optional): Deprecated, do not use.
        setfunc (function, optional): Deprecated, do not use.
        srcsize (int, optional): The size (in bytes) of the input object.
            If ``len(source)`` returns the size of the object in bytes this will
            be inferred automatically, otherwise it must be manually specified.

    """
    def __init__(self, source, itemsize, strides, getfunc=None, setfunc=None,
                 srcsize=None):
        self._source = source
        self._itemsize = itemsize
        self._strides = strides
        self._srcsize = srcsize or len(source)
        self._offset = 0

        self._getfunc = getfunc or self._getbytes
        self._setfunc = setfunc or self._setbytes

        tsum = 1
        for v in strides:
            tsum *= v
        if tsum > self._srcsize:
            raise ValueError("strides exceed the accesible source size")
        #if itemsize > strides[-1]:
        #    raise ValueError("itemsize exceeds the accessible stride length")

    def _getbytes(self, start, end):
        """Gets the bytes within the range of start:end."""
        return self._source[start:end]

    def _setbytes(self, start, end, value):
        """Gets the bytes within the range of start:end to the passed
        value.
        """
        self._source[start:end] = value

    def _getindex(self, index):
        # Perform typechecking and preprocessing of view indices
        if type(index) is slice:
            raise IndexError("MemoryView slicing is not currently supported.")
        elif type(index) is not int:
            e = "Array indices must be integers (got '{0}')."
            raise TypeError(e.format(str(index)))
        else:
            final_idx = index
            if index < 0:
                final_idx = len(self) + index  # Handle negative indexing
            if index >= len(self):
                e = "Index {0} is out of bounds for a view of length {1}."
                raise IndexError(e.format(index, len(self)))
        return final_idx

    def __len__(self):
        """The length of the MemoryView over the current dimension
        (amount of items for the current dimension).
        """
        return self.strides[0]

    def __repr__(self):
        retval = "["
        slen = self.strides[0]
        for dim in range(slen - 1):
            retval += "%s, " % self[dim]
        retval += str(self[slen - 1])
        retval += "]"
        return retval

    def __getitem__(self, index):
        """Returns the item at the specified index."""
        index = self._getindex(index)
        if self.ndim == 1:
            offset = self._offset + index * self.itemsize
            return self._getfunc(offset, offset + self.itemsize)
        else:
            advance = self.itemsize
            for b in self.strides[1:]:
                advance *= b
            offset = self._offset + advance * index
            view = MemoryView(
                self._source, self.itemsize, self.strides[1:],
                self._getfunc, self._setfunc, self._srcsize
            )
            view._offset = offset
            return view

    def __setitem__(self, index, value):
        """Sets the item at index to the specified value."""
        index = self._getindex(index)
        offset = self._offset + index * self.itemsize
        if self.ndim == 1:
            self._setfunc(offset, offset + self.itemsize, value)
        else:
            advance = self.itemsize
            for b in self.strides[1:]:
                advance *= b
            offset = self._offset + advance * index
            view = MemoryView(
                self._source, self.itemsize, self.strides[1:],
                self._getfunc, self._setfunc, self._srcsize
            )
            view._offset = offset
            if len(value) != len(view):
                raise ValueError("value does not match the view strides")
            for x in range(len(view)):
                view[x] = value[x]

    @property
    def size(self):
        """int: The size (in bytes) of the underlying source object."""
        return self._srcsize

    @property
    def strides(self):
        """tuple: The length of each dimension the MemoryView."""
        return self._strides

    @property
    def itemsize(self):
        """int: The size (in bytes) of a single item in the object."""
        return self._itemsize

    @property
    def ndim(self):
        """int: The number of dimensions of the MemoryView."""
        return len(self.strides)

    @property
    def source(self):
        """The underlying data source."""
        return self._source
