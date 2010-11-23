#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from wideeditor import WideEditor
from customeditor import CustomEditor

from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function, post
from camelot.core.utils import ugettext as _
from camelot.view import register

class One2ManyEditor(CustomEditor, WideEditor):

    new_icon = Icon('tango/16x16/actions/document-new.png')
    
    def __init__( self,
                 admin = None,
                 parent = None,
                 create_inline = False,
                 vertical_header_clickable = True,
                 **kw ):
        """
    :param admin: the Admin interface for the objects on the one side of the
    relation

    :param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline

    :param vertical_header_clickable: True if the vertical header is clickable by the user, False if not.

    after creating the editor, set_value needs to be called to set the
    actual data to the editor
    """

        CustomEditor.__init__( self, parent )
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        #
        # Setup table
        #
        from camelot.view.controls.tableview import TableWidget
        # parent set by layout manager
        self.table = TableWidget()
        rowHeight = QtGui.QFontMetrics( self.font() ).height() + 5
        self.table.verticalHeader().setDefaultSectionSize( rowHeight )
        layout.setSizeConstraint( QtGui.QLayout.SetNoConstraint )
        self.setSizePolicy( QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding )
        self.setMinimumHeight( rowHeight*5 )
        if vertical_header_clickable:
            self.table.verticalHeader().sectionClicked.connect(
                self.createFormForIndex
            )
        self.admin = admin
        self.create_inline = create_inline
        self.add_button = None
        self.copy_button = None
        self.delete_button = None
        layout.addWidget( self.table )
        self.setupButtons( layout )
        self.setLayout( layout )
        self.model = None
        self._new_message = None

    def set_field_attributes(self, editable=True, new_message=None, **kwargs):
        self.add_button.setEnabled(editable)
        self.copy_button.setEnabled(editable)
        self.delete_button.setEnabled(editable)
        self._new_message = new_message

    def setupButtons( self, layout ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        self.delete_button = QtGui.QToolButton()
        icon = Icon( 'tango/16x16/places/user-trash.png' ).getQIcon()
        self.delete_button.setIcon( icon )
        self.delete_button.setAutoRaise( True )
        self.delete_button.setToolTip(_('Delete'))
        self.delete_button.clicked.connect(self.deleteSelectedRows)
        self.add_button = QtGui.QToolButton()
        icon = self.new_icon.getQIcon()
        self.add_button.setIcon( icon )
        self.add_button.setAutoRaise( True )
        self.add_button.setToolTip(_('New'))
        self.add_button.clicked.connect(self.newRow)
        self.copy_button = QtGui.QToolButton()
        icon = Icon( 'tango/16x16/actions/edit-copy.png' ).getQIcon()
        self.copy_button.setIcon( icon )
        self.copy_button.setAutoRaise( True )
        self.copy_button.setToolTip(_('Copy'))
        self.copy_button.clicked.connect(self.copy_selected_rows)
        export_button = QtGui.QToolButton()
        export_button.setIcon( Icon( 'tango/16x16/mimetypes/x-office-spreadsheet.png' ).getQIcon() )
        export_button.setAutoRaise( True )
        export_button.setToolTip(_('Export as spreadsheet'))
        export_button.clicked.connect(self.exportToExcel)
        button_layout.addStretch()
        button_layout.addWidget( self.add_button )
        button_layout.addWidget( self.copy_button )
        button_layout.addWidget( self.delete_button )
        button_layout.addWidget( export_button )
        layout.addLayout( button_layout )

    def exportToExcel( self ):
        from camelot.view.export.excel import open_data_with_excel

        def export():
            title = self.admin.get_verbose_name_plural()
            columns = self.admin.get_columns()
            if self.model:
                data = list( self.model.getData() )
                open_data_with_excel( title, columns, data )

        post( export )

    def getModel( self ):
        return self.model

    def update_delegates( self, *args ):
        if self.model:
            delegate = self.model.getItemDelegate()
            if delegate:
                self.table.setItemDelegate( delegate )
                for i in range( self.model.columnCount() ):
                    txtwidth = self.model.headerData( i, Qt.Horizontal, Qt.SizeHintRole ).toSize().width()
                    colwidth = self.table.columnWidth( i )
                    self.table.setColumnWidth( i, max( txtwidth, colwidth ) )

    def set_value( self, model ):
        model = CustomEditor.set_value( self, model )
        if model and model != self.model:
            self.model = model
            self.table.setModel( model )
            register.register( self.model, self.table )
            post( model._extend_cache, self.update_delegates )

    @gui_function
    def activate_editor( self, row ):
        index = self.model.index( row, 0 )
        self.table.scrollToBottom()
        self.table.setCurrentIndex( index )
        self.table.edit( index )

    def newRow( self ):
        from camelot.view.workspace import show_top_level
        if self._new_message:
            QtGui.QMessageBox.information(self, _('New'), self._new_message)
            return
        
        if self.create_inline:

            @model_function
            def create():
                o = self.admin.entity()
                row = self.model.insertEntityInstance( 0, o )
                return row

            post( create, self.activate_editor )

        else:
            prependentity = lambda o: self.model.insertEntityInstance( 0, o )
            removeentity = lambda o: self.model.removeEntityInstance( o )
            form = self.admin.create_new_view( parent = None,
                                               oncreate = prependentity,
                                               onexpunge = removeentity )
            show_top_level( form, self )

    def copy_selected_rows( self ):
        """Copy the selected rows in this tableview"""
        LOGGER.debug( 'delete selected rows called' )
        for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
            self.model.copy_row( row )

    def deleteSelectedRows( self ):
        """Delete the selected rows in this tableview"""
        LOGGER.debug( 'delete selected rows called' )
        self.model.remove_rows( set( map( lambda x: x.row(), self.table.selectedIndexes() ) ) )

    def createFormForIndex( self, index ):
        from camelot.view.workspace import show_top_level
        from camelot.view.proxy.collection_proxy import CollectionProxy
        model = CollectionProxy( self.admin,
                                 self.model.collection_getter,
                                 self.admin.get_fields,
                                 max_number_of_rows = 1,
                                 edits = None )
        form = self.admin.create_form_view( u'', model, self.model.map_to_source(index) )
        show_top_level( form, self )


