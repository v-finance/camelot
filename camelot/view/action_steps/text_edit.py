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

from PyQt4 import QtCore, QtGui

from camelot.admin.action import ActionStep
from camelot.core.utils import ugettext_lazy as _
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
        self.document.moveToThread( QtGui.QApplication.instance().thread() )
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
        layout = QtGui.QHBoxLayout()
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
            dialog.exec_()
        finally:
            self.document.moveToThread( self.thread )
