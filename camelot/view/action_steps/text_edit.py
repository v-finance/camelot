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
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.controls.editors import RichTextEditor
from camelot.view.utils import resize_widget_to_screen

class EditTextDocument( ActionStep ):
    """
    Display a rich text editor to edit a text document.
    
    :param document: a :class:`QtGui.QTextDocument` object.
    
    this action step can be customised using these attributes :    
        
    .. attribute:: window_title
    
        the window title of the dialog shown
        
    """
    
    def __init__( self, document ):
        self.document = document
        self.thread = QtCore.QThread.currentThread()
        self.document.moveToThread( QtGui.QApplication.instance().thread() )
        self.window_title = None
        
    def render( self ):
        """create the text edit dialog. this method is used to unit test
        the action step."""
        dialog = StandaloneWizardPage( self.window_title )
        dialog.set_default_buttons()
        main_widget = dialog.main_widget()
        layout = QtGui.QHBoxLayout()
        editor = RichTextEditor()
        editor.set_document( self.document )
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
