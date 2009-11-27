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

"""Functions and widget to represent exceptions to the user"""

def model_thread_exception_message_box(exception_info):
    """Display an exception that occurred in the model thread in a message box,
  use this function as the exception argument in the model thread's post function
  to represent the exception to the user
    
  :param exception_info: a tuple containing the exception that was thrown and the
  model thread in which the exception was thrown  
  """
    from PyQt4 import QtGui
    exc, traceback = exception_info
    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                               'Exception', 'An unexpected event occurred')
    msgBox.setInformativeText(unicode(exc))
    msgBox.setDetailedText(traceback)
    msgBox.exec_()
