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

import six

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest

_detail_format = u'Update Progress {0:03d}/{1:03d} {2._text} {2._detail}'

@six.python_2_unicode_compatible
class UpdateProgress( ActionStep ):
    """
Inform the user about the progress the application is making
while executing an action.  This ActionStep is not blocking.  So it can
be used inside transactions and will result in a minimum of delay when
yielded.  Each time an object is yielded, the progress dialog will be
updated.

.. image:: /_static/controls/progress_dialog.png

:param value: the current step
:param maximum: the maximum number of steps that will be executed. set it
    to 0 to display a busy indicator instead of a progres bar
:param text: the text to be displayed inside the progres bar
:param detail: the text to be displayed below the progres bar, this text is
    appended to the text already there
:param clear_details: clear the details text already there before putting 
    the new detail text.
:param title: the text to be displayed in the window's title bar
:param blocking: wait until the user presses `OK`, for example to review the
    details.
:param enlarge: increase the size of the window to two thirds of the screen,
    useful when there are a lot of details displayed.
"""
    
    def __init__( self,
                  value=None, 
                  maximum=None, 
                  text=None, 
                  detail=None, 
                  clear_details=False,
                  title=None,
                  blocking=False,
                  enlarge=False):
        super(UpdateProgress, self).__init__()
        self._value = value
        self._maximum = maximum
        self._text = text
        self._detail = detail
        self._clear_details = clear_details
        self._title = title
        self.blocking = blocking
        self.enlarge = enlarge
        
    def __str__( self ):
        return _detail_format.format(self._value or 0, self._maximum or 0, self)
    
    def gui_run( self, gui_context ):
        """This method will update the progress dialog, if such dialog exists
        within the GuiContext
        
        :param gui_context: a :class:`camelot.admin.action.GuiContext` instance
        """
        progress_dialog = gui_context.progress_dialog
        if progress_dialog:
            if self._maximum is not None:
                progress_dialog.setMaximum( self._maximum )
            if self._value is not None:
                progress_dialog.setValue( self._value )
            progress_dialog.set_cancel_hidden(not self.cancelable)
            if self._text is not None:
                progress_dialog.setLabelText( six.text_type(self._text) )
            if self._clear_details is True:
                progress_dialog.clear_details()
            if self._detail is not None:
                progress_dialog.add_detail( self._detail )
            if self._title is not None:
                progress_dialog.title = self._title
            if self.enlarge:
                progress_dialog.enlarge()
            if self.blocking:
                progress_dialog.set_ok_hidden( False )
                progress_dialog.exec_()
                progress_dialog.set_ok_hidden( True )
            if progress_dialog.wasCanceled():
                progress_dialog.reset()
                raise CancelRequest()

