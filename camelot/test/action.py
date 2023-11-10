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

"""Helper classes to create unit tests for Actions."""

class MockModelContext( object ):
    """Model Context to be used in unit tests
    
    :param session: the session attributed to this model context, if `None` is
        given, the session of the object is used.
    """
    
    def __init__( self, session=None ):
        self._model = []
        self.obj = None
        self.selection = []
        self.admin = None
        self.mode_name = None
        self.collection_count = 1
        self.current_row = 0
        self.current_column = None
        self.current_field_name = None
        self.field_attributes = {}
        self._session = session
        
    def get_object( self, row=None ):
        return self.obj
        
    def get_selection( self, yield_per = None ):
        if self.obj is not None:
            return [self.obj]
        return self.selection

    def get_collection( self, yield_per = None ):
        return self.get_selection(yield_per=yield_per)

    @property
    def selection_count(self):
        return len(self.get_selection())

    @property
    def session( self ):
        if self._session is None and self.admin is not None:
            return self.admin.get_session(self.obj)
        return self._session
