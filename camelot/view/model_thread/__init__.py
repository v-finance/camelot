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

import logging

from ...core.qt import QtCore
from ..requests import AbstractRequest

logger = logging.getLogger('camelot.view.model_thread')

_model_thread_ = []

# this might be set to False, for unittesting purpose
verify_threads = True

class ModelThreadException(Exception):
    pass

def object_thread( self ):
    """Funtion to verify if a call to an object is made in the thread of this
    object, to be used in assert statements.  Example ::
    
        class FooObject( QtCore.QObject ):
        
            def do_something( self ):
                assert object_thread( self )
                print 'safe method call'
    
    :param self: a :class:`QtCore.QObject` instance.
    :return True: if the thread of self is the current thread 
    
    The approach with assert statements is prefered over decorators,
    since decorators hide part of the method signature from the sphinx
    documentation.
    """
    return self.thread() == QtCore.QThread.currentThread()

def gui_thread():
    """function to verify if a call is made in the GUI thread of the application
    """
    app = QtCore.QCoreApplication.instance()
    return object_thread(app)

def has_model_thread():
    return len(_model_thread_) > 0

def get_model_thread():
    return _model_thread_[0]

def post(request):
    """Post a request and a response to the default model thread"""
    assert isinstance(request, AbstractRequest)
    mt = get_model_thread()
    return mt.post(request)



