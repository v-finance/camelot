#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest

_detail_format = u'Update Progress {0._value:03d}/{0._maximum:03d} {0._text} {0._detail}'

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
:param blocking: wait until the user presses `OK`, for example to review the
    details.
"""
    
    def __init__( self,
                  value=0, 
                  maximum=0, 
                  text=None, 
                  detail=None, 
                  clear_details=False,
                  blocking=False ):
        super(UpdateProgress, self).__init__()
        self._value = value
        self._maximum = maximum
        self._text = text
        self._detail = detail
        self._clear_details = clear_details
        self.blocking = blocking
        
    def __unicode__( self ):
        return _detail_format.format( self )
    
    def gui_run( self, gui_context ):
        """This method will update the progress dialog, if such dialog exists
        within the GuiContext
        
        :param gui_context: a :class:`camelot.admin.action.GuiContext` instance
        """
        progress_dialog = gui_context.progress_dialog
        if progress_dialog:
            progress_dialog.setMaximum( self._maximum )
            progress_dialog.setValue( self._value )
            progress_dialog.set_cancel_hidden(not self.cancelable)
            if self._text != None:
                progress_dialog.setLabelText( unicode(self._text) )
            if self._clear_details == True:
                progress_dialog.clear_details()
            if self._detail != None:
                progress_dialog.add_detail( self._detail )
            if self.blocking:
                progress_dialog.set_ok_hidden( False )
                progress_dialog.exec_()
                progress_dialog.set_ok_hidden( True )
            if progress_dialog.wasCanceled():
                progress_dialog.reset()
                raise CancelRequest()
