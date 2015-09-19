
"""
Getting and setting model data might be expensive and highly dependent on the
actual model.

The model proxy classes provide a uniform interface that can be used by the
`QAbstractItemModel` to get and set model data while defering the cost of
these operations.

Each different type of model that needs to be displayed in Camelot should implement
it's own concrete `ModelProxy`.  Camelot has a built in `ModelProxy` for pure
python lists and for sqlalchemy query objects.

The model proxy classes should be used in the model thread, but they
can be constructed in the gui thread.

This module defines the `AbstractModelProxy` interface class.
Concrete model proxy classes should implement this interface to be usable
by the `QAbstractItemModel`.
"""

class AbstractModelProxy(object):

    def __len__(self):
        """
        :return: the number of objects that can be retrieved from the proxy
        """
        raise NotImplementedError()

    def sort(self, key=None, reverse=False):
        """
        Apply an order on the objects retrieved by the proxy.  This order is not
        applied on the model itself.

        :key: the key to be used to sort the objects, use None to disable a
            previous sort.
        """
        raise NotImplementedError()

    def append(self, obj):
        """
        Add an object to the model
        """
        raise NotImplementedError()

    def remove(self, obj):
        """
        Remove an object from the model
        """
        raise NotImplementedError()

    def index(self, obj):
        """
        Return the row holding the data for this object
        """
        raise NotImplementedError()

    def __getitem__(self, sl):
        """
        :param sl: a `slice` object representing a set of indices
        :return: an iterator over the indexed objects in the model
        """
