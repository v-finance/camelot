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

from ...core.qt import QtCore, QtWidgets

from camelot.admin.action import ActionStep
from camelot.core.utils import ugettext_lazy as _
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.controls.editors import RichTextEditor
from camelot.view.utils import resize_widget_to_screen

class EditTextDocument( ActionStep ):
    """
    Display a rich text editor to edit a text document.
    
    :param document: a :class:`QtGui.QTextDocument` object.
    
    When this action step is constructed, the thread affinity of
    the document is changed to be the gui thread.  when the editing
    of the document is finished, the affinity is returned to the
    current thread.  There is no :guilabel:`Cancel` button on the
    dialog because the document is changed when the user is editing
    it, and this cannot be undone.
    
    This action step can be customised using these attributes :    
        
    .. attribute:: window_title
    
        the window title of the dialog shown
        
    .. attribute:: title
    
        the title of the dialog shown
        
    .. attribute:: subtitle
    
        the subtitle of the dialog shown
        
    .. image:: /_static/actionsteps/text_document.png
        
    """
    
    def __init__( self, document ):
        self.document = document
        self.thread = QtCore.QThread.currentThread()
        self.document.moveToThread( QtWidgets.QApplication.instance().thread() )
        self.window_title = _('Edit text')
        self.title = _('Edit text')
        self.subtitle = _('Press OK when finished')
        
    def render( self ):
        """create the text edit dialog. this method is used to unit test
        the action step."""
        dialog = StandaloneWizardPage( self.window_title )
        dialog.set_default_buttons( reject = None )
        dialog.set_banner_title( self.title )
        dialog.set_banner_subtitle( self.subtitle )
        main_widget = dialog.main_widget()
        layout = QtWidgets.QHBoxLayout()
        editor = RichTextEditor()
        editor.set_document( self.document )
        editor.set_toolbar_hidden( False )
        layout.addWidget( editor )
        main_widget.setLayout( layout )
        resize_widget_to_screen( dialog )
        return dialog
     
    def gui_run( self, gui_context ):
        try:
            dialog = self.render()
            with hide_progress_dialog( gui_context ):
                dialog.exec_()
        finally:
            self.document.moveToThread( self.thread )


