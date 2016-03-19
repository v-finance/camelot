#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

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

    def copy(self):
        """
        :return: a new `AbstractModelProxy` with consistent indexes as long
            as no new operation is applied on one of the proxies.
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


