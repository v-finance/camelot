#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Functions and classes to use a progress dialog in combination with
a model thread"""

from camelot.core.utils import ugettext as _
from camelot.view.art import Icon

from PyQt4 import QtGui, QtCore

class ProgressDialog(QtGui.QProgressDialog):
    """A Progress Dialog to be used in combination with a post to the model thread::
    
    to display a progress dialog until my_function has finished :
    
    d = ProgressDialog()
    post(my_function, p.finished, p.exception)
    d.exec_()
    
    """

    def __init__(self, name, icon=Icon('tango/32x32/actions/appointment-new.png')):
        QtGui.QProgressDialog.__init__( self, QtCore.QString(), QtCore.QString(), 0, 0 )
        label = QtGui.QLabel(unicode(name))
        #label.setPixmap(icon.getQPixmap())
        self.setLabel(label)
        self.setWindowTitle( _('Please wait') )

    def finished(self, success):
        self.close()
        
    def exception(self, exception_info):
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box(exception_info)
        self.finished(False)
