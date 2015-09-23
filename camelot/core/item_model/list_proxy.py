import logging
from sys import maxsize

from .proxy import AbstractModelProxy

LOGGER = logging.getLogger(__name__)

class TwoWayDict(dict):

    def __setitem__(self, key, value):
        # Remove any previous connections with these values
        assert (key not in self)
        assert (value not in self)
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

class SortingRowMapper( dict ):
    """Class mapping rows of a collection 1:1 without sorting
    and filtering, unless a mapping has been defined explicitly"""

    def __getitem__(self, row):
        try:
            return super(SortingRowMapper, self).__getitem__(row)
        except KeyError:
            return row


class ListModelProxy(AbstractModelProxy, dict):
    """
    A concrete model proxy for displaying objects in python `list`s
    """

    def __init__(self, objects):
        """
        :param objects: a list of objects
        """
        self._objects = objects
        self._indexed_objects = TwoWayDict()
        self._sort_and_filter = SortingRowMapper()

    def __len__(self):
        return len(self._objects)

    def append(self, obj):
        if obj not in self._objects:
            self._objects.append(obj)

    def remove(self, obj):
        if obj in self._objects:
            self._objects.remove(obj)

    def index(self, obj):
        try:
            return self._indexed_objects[obj]
        except KeyError:
            i = self._objects.index(obj)
            self._indexed_objects[i] = obj
            return i

    def sort(self, key=None, reverse=False):
        self._indexed_objects = TwoWayDict()
        self._sort_and_filter = SortingRowMapper()

        if key is None:
            return

        def get_key(obj):
            value = None
            try:
                value = getattr(obj, key)
            except Exception as e:
                LOGGER.error('could not get attribute %s from object'%key,
                             exc_info=e)
            # handle the case of one of the values being None
            return (value is not None, value)

        indexed_keys = [(get_key(obj),i) for i,obj in enumerate(self._objects)]
        indexed_keys.sort(reverse=reverse)
        for j,(_key,i) in enumerate(indexed_keys):
            self._sort_and_filter[j] = i

    def __getitem__(self, sl, yield_per=None):
        # for now, dont get the actual length, as this might be too slow
        size = maxsize
        if not (0<=sl.start<=size):
            raise IndexError('start of slice not in range', sl.start, 0, size)
        if not (0<=sl.stop<=size):
            raise IndexError('stop of slice not in range', sl.stop, 0, size)
        limit = min(size-sl.start, sl.stop-sl.start)
        for i in xrange(sl.start, sl.stop):
            try:
                obj = self._indexed_objects[i]
            except KeyError:
                self._extend_indexed_objects(i, limit)
                try:
                    obj = self._indexed_objects[i]
                except KeyError:
                    # there is no data available to extend the cache any
                    # more
                    break
            yield obj

    def _extend_indexed_objects(self, offset, limit):
        """
        Extend the indexed objects.
        """
        if limit > 0:
            skipped_rows = 0
            try:
                for i in range(offset, min(offset + limit + 1,len(self._objects))):
                    object_found = False
                    while not object_found:
                        unsorted_row = self._sort_and_filter[i]
                        obj = self._objects[unsorted_row+skipped_rows]
                        # check if the object is not present with another index
                        if self._indexed_objects.get(obj) not in (None, i):
                            skipped_rows = skipped_rows + 1
                        else:
                            self._indexed_objects[i] = obj
                            object_found = True
            except IndexError:
                # stop when the end of the collection is reached, no matter
                # what the request was
                pass
