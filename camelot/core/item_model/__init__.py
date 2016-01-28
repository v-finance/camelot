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
This module contains the helper classes and constants for building a
`QAbstractItemModel` by the view.  The classes in this module are no subclasses
of `QObject`, but pure Python helper classes.
"""

from ..qt import Qt

from .list_proxy import ListModelProxy
from .proxy import AbstractModelProxy
from .query_proxy import QueryModelProxy

#
# Custom Roles
#
FieldAttributesRole = Qt.UserRole
ObjectRole = Qt.UserRole + 1
PreviewRole = Qt.UserRole + 2
VerboseIdentifierRole = Qt.UserRole + 3
ValidRole = Qt.UserRole + 4
ValidMessageRole = Qt.UserRole + 5

class ProxyDict(dict):
    """Subclass of dictionary to fool the Qt Variant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass

__all__ = [
    AbstractModelProxy.__name__,
    ListModelProxy.__name__,
    ProxyDict.__name__,
    QueryModelProxy.__name__,
]

