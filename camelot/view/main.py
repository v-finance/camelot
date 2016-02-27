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

"""Main function, to be called to start the GUI interface"""

import functools
import sys

from camelot.art import resources # Required for tooltip visualization
resources.__name__ # Dodge PyFlakes' attack

from ..core.qt import QtCore, QtWidgets
from ..admin.action.application import Application
from ..admin.action.application_action import ApplicationActionGuiContext

def main(application_admin):
    """shortcut main function, call this function to start the GUI interface 
    with minimal hassle and without the need to construct a main action object.  
    
    If you need to customize the initialization process, use the 
    :func:`main_action` function an supply the custom action object.

    :param application_admin: a 
        :class:`camelot.admin.application_admin.ApplicationAdmin` object
        that specifies the look of the GUI interface
    """
    app = Application(application_admin)
    main_action(app)
    
def main_action(action):
    """
    Construct a :class:`QtWidgets.QApplication`, start the event loop and run a
    :class:`camelot.admin.action.base.Action` object.
    
    Use this function for complete customization of a Camelot application.  The
    typical use case is to call this function with a subclass of
    :class:`camelot.admin.action.application.Application`.  But it can be
    used with any action object.
    """
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([a for a in sys.argv if a])
    gui_context = ApplicationActionGuiContext()
    QtCore.QTimer.singleShot(0, functools.partial(action.gui_run, 
                                                   gui_context))
    result = app.exec_()
    sys.exit( result )

