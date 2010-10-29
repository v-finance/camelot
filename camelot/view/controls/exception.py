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

from camelot.core.utils import ugettext as _

def register_exception(logger, text, exception):
    """Log an exception and return a tuple of strings with exception information in a 
    user readable format, to be used when displaying an exception message box
    :return: (exception_name, exception_traceback) """
    logger.error( text, exc_info = exception )
    import traceback, cStringIO
    sio = cStringIO.StringIO()
    traceback.print_exc(file=sio)
    traceback_print = sio.getvalue()
    sio.close()
    return ( unicode(exception), traceback_print)
    
def model_thread_exception_message_box(exception_info, title=None, text=None):
    """Display an exception that occurred in the model thread in a message box,
  use this function as the exception argument in the model thread's post function
  to represent the exception to the user
    
  :param exception_info: a tuple containing the exception that was thrown and the
  traceback
  """
    from PyQt4 import QtGui
    title = title or _('Exception')
    text  = text  or _('An unexpected event occurred')
    exc, traceback = exception_info
    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                               unicode(title), unicode(text))
    # chop the size of the text to prevent error dialogs larger than the screen
    msgBox.setInformativeText(unicode(exc)[:1000])
    msgBox.setDetailedText(traceback)
    msgBox.exec_()
