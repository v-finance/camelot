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

"""Functions and widget to represent exceptions to the user"""

import collections
from ...core.qt import QtWidgets

import six

from camelot.core.utils import ugettext as _
from camelot.core.exception import UserException

ExceptionInfo = collections.namedtuple( 'exception_info',
                                        ['title', 'text', 'icon', 
                                         'resolution', 'detail'] )

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
        return ExceptionInfo(exception.title, 
                             exception.text, 
                             exception.icon, 
                             exception.resolution, 
                             exception.detail)

    logger.error( text, exc_info = exception )
    title = _('Exception')
    text  = _('An unexpected event occurred')
    icon  = None
    # chop the size of the text to prevent error dialogs larger than the screen
    resolution = six.text_type(exception)[:1000]
    from six.moves import cStringIO
    import traceback
    sio = cStringIO()
    traceback.print_exc(file=sio)
    detail = sio.getvalue()
    sio.close()
    return ExceptionInfo(title, text, icon, resolution, detail)

class ExceptionDialog(QtWidgets.QMessageBox):
    """Dialog to display an exception to the user

    .. image:: /_static/controls/user_exception.png 
    """

    def __init__( self, exception_info ):
        """Dialog to display a serialized exception, as returned
        by :func:`register_exception`

        :param exception_info: a tuple containing exception information
        """

        (title, text, icon, resolution, detail) = exception_info
        super( ExceptionDialog, self ).__init__(QtWidgets.QMessageBox.Warning,
                                                six.text_type(title), 
                                                six.text_type(text))
        self.setInformativeText(six.text_type(resolution or ''))
        self.setDetailedText(six.text_type(detail or ''))
        if icon is not None:
            self.setIconPixmap(icon.getQPixmap())


