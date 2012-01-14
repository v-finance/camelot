#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Functions and widget to represent exceptions to the user"""


from PyQt4 import QtGui

from camelot.core.utils import ugettext as _
from camelot.core.exception import UserException

def register_exception(logger, text, exception):
    """Log an exception and return a serialized form of the exception with 
    exception information in a  user readable format, to be used when displaying 
    an exception message box.
    
    that serialized form can be fed to the model_thread_exception_message_box 
    function.
    
    :return: a tuple with exception information
    """
    if isinstance( exception, UserException ):
        # this exception is not supposed to generate any logging
        # or inform the developer about something
        return (exception.title, 
                exception.text, 
                exception.icon, 
                exception.resolution, 
                exception.detail)

    logger.error( text, exc_info = exception )
    title = _('Exception')
    text  = _('An unexpected event occurred')
    icon  = None
    # chop the size of the text to prevent error dialogs larger than the screen
    resolution = unicode(exception)[:1000]
    import traceback, cStringIO
    sio = cStringIO.StringIO()
    traceback.print_exc(file=sio)
    detail = sio.getvalue()
    sio.close()
    return (title, text, icon, resolution, detail)

class ExceptionDialog(QtGui.QMessageBox):
    """Dialog to display an exception to the user

    .. image:: /_static/controls/user_exception.png 
    """

    def __init__( self, exception_info ):
        """Dialog to display a serialized exception, as returned
        by :func:`register_exception`

        :param exception_info: a tuple containing exception information
        """

        (title, text, icon, resolution, detail) = exception_info
        super( ExceptionDialog, self ).__init__(QtGui.QMessageBox.Warning,
                                                unicode(title), unicode(text))
        self.setInformativeText(unicode(resolution or ''))
        self.setDetailedText(unicode(detail or ''))
    
def model_thread_exception_message_box(exception_info):
    """Display an exception that occurred in the model thread in a message box,
    use this function as the exception argument in the model thread's post function
    to represent the exception to the user
    
    :param exception_info: a tuple containing exception information
    """
    dialog = ExceptionDialog( exception_info )
    dialog.exec_()



