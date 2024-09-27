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

"""Classes to interface with the Memento model, which tracks modification
of changes.

This module contains the `memento_types` variable, which is a list of different
types of changes that can be tracked.  Add elements to this list to add custom
tracking of changes
"""

import collections
import logging

from camelot.core.utils import ugettext

memento_types = [ (1, 'before_update'),
                  (2, 'before_delete'),
                  (3, 'create')
                  ]
                                                        
LOGGER = logging.getLogger( 'camelot.core.memento' )
            
#
# lightweight data structure to present object changes to the memento
# system
#
# :param model: a string with the name of the model
# :param primary_key: a tuple with the primary key of the changed object
# :param previous_attributes: a dict with the names and the values of
#     the attributes of the object before they were changed.
# :param memento_type: a string with the type of memento
#
memento_change = collections.namedtuple( 'memento_change',
                                         [ 'model', 
                                           'primary_key', 
                                           'previous_attributes', 
                                           'memento_type' ] )

class Change( object ):
    
    def __init__( self, memento, row ):
        self.id = row.id
        self.type = row.memento_type
        self.at = row.at
        self.by = row.by
        self.changes = None
        if row.previous_attributes:
            self.changes = u', '.join( ugettext('%s was %s')%(k,str(v)) for k,v in row.previous_attributes.items() )
        self.memento_type = row.memento_type
