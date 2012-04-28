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

import logging

LOGGER = logging.getLogger( 'camelot.view.controls.editors.onetomanyeditor' )

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from wideeditor import WideEditor
from customeditor import CustomEditor

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.view.model_thread import object_thread, post
from camelot.view import register

class One2ManyEditor(CustomEditor, WideEditor):
    """
    :param admin: the Admin interface for the objects on the one side of the
    relation

    :param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline

    after creating the editor, set_value needs to be called to set the
    actual data to the editor
    """
        
    def __init__( self,
                  admin = None,
                  parent = None,
                  create_inline = False,
                  direction = 'onetomany',
                  field_name = 'onetomany',
                  **kw ):
        CustomEditor.__init__( self, parent )
        self.setObjectName( field_name )
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        #
        # Setup table
        #
        from camelot.view.controls.tableview import AdminTableWidget
        # parent set by layout manager
        table = AdminTableWidget(admin, self)
        table.setObjectName('table')
        rowHeight = QtGui.QFontMetrics( self.font() ).height() + 5
        layout.setSizeConstraint( QtGui.QLayout.SetNoConstraint )
        self.setSizePolicy( QtGui.QSizePolicy.Expanding,
                            QtGui.QSizePolicy.Expanding )
        self.setMinimumHeight( rowHeight*5 )
        table.verticalHeader().sectionClicked.connect(
            self.trigger_list_action
        )
        self.admin = admin
        self.direction = direction
        self.create_inline = create_inline
        layout.addWidget( table )
        self.setLayout( layout )
        self.model = None
        self._new_message = None
        self.gui_context = ListActionGuiContext()
        self.gui_context.view = self
        self.gui_context.admin = self.admin
        self.gui_context.item_view = table
        post( self.admin.get_related_toolbar_actions, 
              self.set_right_toolbar_actions,
              args = (Qt.RightToolBarArea, self.direction ) )

    @QtCore.pyqtSlot( object )
    def set_right_toolbar_actions( self, toolbar_actions ):
        if toolbar_actions != None:
            toolbar = QtGui.QToolBar( self )
            toolbar.setOrientation( Qt.Vertical )
            for action in toolbar_actions:
                qaction = action.render( self.gui_context, toolbar )
                qaction.triggered.connect( self.action_triggered )
                toolbar.addAction( qaction )
            self.layout().addWidget( toolbar )
            # set field attributes might have been called before the
            # toolbar was created
            self.update_action_status()

    @QtCore.pyqtSlot( bool )
    def action_triggered( self, _checked = False ):
        action_action = self.sender()
        action_action.action.gui_run( self.gui_context )

    def set_field_attributes( self, **kwargs ):
        self.gui_context.field_attributes = kwargs
        self.update_action_status()
        
    def update_action_status( self ):
        toolbar = self.findChild( QtGui.QToolBar )
        if toolbar:
            model_context = self.gui_context.create_model_context()
            for qaction in toolbar.actions():
                post( qaction.action.get_state,
                      qaction.set_state,
                      args = ( model_context, ) )
                
    @QtCore.pyqtSlot( object )
    def update_delegates( self, *args ):
        table = self.findChild(QtGui.QWidget, 'table')
        if self.model and table:
            delegate = self.model.getItemDelegate()
            if delegate:
                table.setItemDelegate( delegate )
                for i in range( self.model.columnCount() ):
                    txtwidth = self.model.headerData( i, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
                    colwidth = table.columnWidth( i )
                    table.setColumnWidth( i, max( txtwidth, colwidth ) )

    def set_value( self, model ):
        model = CustomEditor.set_value( self, model )
        table = self.findChild(QtGui.QWidget, 'table')
        if table and model and model != self.model:
            self.model = model
            table.setModel( model )
            register.register( self.model, table )
            model_context = self.gui_context.create_model_context()
            for toolbar in self.findChildren( QtGui.QToolBar ):
                for qaction in toolbar.actions():
                    post( qaction.action.get_state,
                          qaction.set_state,
                          args = ( model_context, ) )
            post( model._extend_cache, self.update_delegates )

    def activate_editor( self, number_of_rows ):
        assert object_thread( self )
#        return
# Activating this code can cause segfaults
# see ticket 765 in web issues
#
# The segfault seems no longer there after disabling the
# editor before setting a new model, but the code below
# seems to have no effect.
        table = self.findChild(QtGui.QWidget, 'table')
        if table:
            index = self.model.index( max(0, number_of_rows-1), 0 )
            table.scrollToBottom()
            table.setCurrentIndex( index )
            table.edit( index )

    @QtCore.pyqtSlot( int )
    def trigger_list_action( self, index ):
        table = self.findChild(QtGui.QWidget, 'table')
        # close the editor to prevent certain Qt crashes
        table.close_editor()
        if self.admin.list_action:
            self.admin.list_action.gui_run( self.gui_context )

