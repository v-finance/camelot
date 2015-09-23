
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

The proxy guarantees temporary consistency, meaning that as long as no sort, add,
remove or filter operation is applied on the proxy, an object returned at an index
by the proxy will stay at this index, even when the model has changed.
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

        :key: the name of the attribute to sort the objects on, use None to
            disable a previous sort.
        """
        raise NotImplementedError()

    def append(self, obj):
        """
        Add an object to the proxy and the model
        """
        raise NotImplementedError()

    def remove(self, obj):
        """
        Remove an object from the proxy and the model
        """
        raise NotImplementedError()

    def index(self, obj):
        """
        Return the index holding the object in the proxy
        """
        raise NotImplementedError()

    def __getitem__(self, sl, yield_per=None):
        """
        :param sl: a `slice` object representing a set of indices
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the model at the same time

        :return: an iterator over the indexed objects in the proxy

        The requested slice indexes should be positive and smaller than the number
        lenght of the proxy, or an :attr:`IndexError` will be raised.
        
        The index numbers are the numbers after sorting and filtering.

        The number of objects returned by the iterator is not guaranteed to be
        the number of indexes in the slice since the underlying model might have
        been modified without the proxy being aware of it.  So the proxy might fail
        to retrieve those objects from the model and thus yield less objects than
        requested.
        """
        raise NotImplementedError()

