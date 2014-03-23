#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""
Container classes for basic Python collections, such as `list` and `dict`.  These
allow the passing of those collections through the variant mechanism without
taking a copy.
"""

class CollectionContainer(object):
    """
    Wrapper around a Python collection, any modification on the container should
    be applied on the collection.

    :param collection: a Python collection such as a `list` or a `dict` that
        needs to be passed from the model to the gui without copying the original
        data structure.
    """
    
    def __init__(self, collection):
        self._collection = collection
    
    def __getattr__(self, attr):
        return getattr(self._collection, attr)
    
    def __len__(self):
        return len(self._collection)