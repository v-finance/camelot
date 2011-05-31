#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui

from one2manyeditor import One2ManyEditor
from abstractmanytooneeditor import AbstractManyToOneEditor

from camelot.view.art import Icon
from camelot.view.model_thread import model_function, post
from camelot.core.utils import ugettext as _

class ManyToManyEditor( One2ManyEditor, AbstractManyToOneEditor ):

    remove_icon = Icon( 'tango/16x16/actions/list-remove.png' )
    add_icon = Icon( 'tango/16x16/actions/list-add.png' )
    
    def setupButtons( self, layout, _table ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        
        self.remove_button = QtGui.QToolButton()
        self.remove_button.setIcon( self.remove_icon.getQIcon() )
        self.remove_button.setAutoRaise( True )
        self.remove_button.setToolTip(_('Remove'))
        self.remove_button.setFixedHeight( self.get_height() )
        self.remove_button.clicked.connect(self.removeSelectedRows)

        self.add_button = QtGui.QToolButton()
        self.add_button.setIcon( self.add_icon.getQIcon() )
        self.add_button.setAutoRaise( True )
        self.add_button.setToolTip(_('Add'))
        self.add_button.setFixedHeight( self.get_height() )
        self.add_button.clicked.connect(self.createSelectView)
        
        """
        self.delete_button = QtGui.QToolButton()
        self.delete_button.setIcon( self.delete_icon.getQIcon() )
        self.delete_button.setAutoRaise( True )
        self.delete_button.setToolTip(_('Delete'))
        table = self.findChild(QtGui.QWidget, 'table')
        if table:
            self.delete_button.clicked.connect( table.delete_selected_rows )
        """
        self.new_button = QtGui.QToolButton()
        self.new_button.setIcon( self.new_icon.getQIcon() )
        self.new_button.setAutoRaise( True )
        self.new_button.setToolTip(_('New'))
        self.new_button.clicked.connect(self.newRow)
        """
        self.copy_button = QtGui.QToolButton()
        self.copy_button.setIcon( self.copy_icon.getQIcon() )
        self.copy_button.setAutoRaise( True )
        self.copy_button.setToolTip(_('Copy'))
        if table:
            self.copy_button.clicked.connect( table.copy_selected_rows )
        """
        export_button = QtGui.QToolButton()
        export_button.setIcon( self.spreadsheet_icon.getQIcon() )
        export_button.setAutoRaise( True )
        export_button.setToolTip(_('Export as spreadsheet'))
        export_button.clicked.connect(self.exportToExcel)
        
        button_layout.addStretch()
        button_layout.addWidget( self.add_button )
        button_layout.addWidget( self.remove_button )
        button_layout.addSpacing( 8 )
        button_layout.addWidget( self.new_button )
        #button_layout.addWidget( self.copy_button )
        #button_layout.addWidget( self.delete_button )
        button_layout.addWidget( export_button )
        layout.addLayout( button_layout )

    def set_field_attributes(self, editable=True, **kwargs):
        self.add_button.setEnabled(editable)
        self.remove_button.setEnabled(editable)

    def selectEntity( self, entity_instance_getter ):

        @model_function
        def insert():
            o = entity_instance_getter()
            self.model.append_object( o )

        post( insert, self.emit_editing_finished )

    def emit_editing_finished(self, *args):
        self.editingFinished.emit()

    def removeSelectedRows( self ):
        """Remove the selected rows in this tableview, but don't delete them"""
        table = self.findChild(QtGui.QWidget, 'table')
        if table:
            self.model.remove_rows( set( map( lambda x: x.row(), table.selectedIndexes() ) ), delete=False)
            self.editingFinished.emit()


