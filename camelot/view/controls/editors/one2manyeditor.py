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

import logging

LOGGER = logging.getLogger( 'camelot.view.controls.editors.onetomanyeditor' )

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from wideeditor import WideEditor
from customeditor import CustomEditor

from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function, post
from camelot.core.utils import ugettext as _
from camelot.view import register

class One2ManyEditor(CustomEditor, WideEditor):

    new_icon = Icon('tango/16x16/actions/document-new.png')
    delete_icon = Icon( 'tango/16x16/places/user-trash.png' )
    copy_icon = Icon( 'tango/16x16/actions/edit-copy.png' )
    spreadsheet_icon = Icon( 'tango/16x16/mimetypes/x-office-spreadsheet.png' )

    def __init__( self,
                 admin = None,
                 parent = None,
                 create_inline = False,
                 vertical_header_clickable = True,
                 field_name = 'onetomany',
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
        if vertical_header_clickable:
            table.verticalHeader().sectionClicked.connect(
                self.createFormForIndex
            )
        self.admin = admin
        self.create_inline = create_inline
        self.add_button = None
        self.copy_button = None
        self.delete_button = None
        layout.addWidget( table )
        self.setupButtons( layout, table )
        self.setLayout( layout )
        self.model = None
        self._new_message = None

    def set_field_attributes(self, editable=True, new_message=None, **kwargs):
        self.add_button.setEnabled(editable)
        self.copy_button.setEnabled(editable)
        self.delete_button.setEnabled(editable)
        self._new_message = new_message

    def setupButtons( self, layout, table ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        self.delete_button = QtGui.QToolButton()
        self.delete_button.setIcon( self.delete_icon.getQIcon() )
        self.delete_button.setAutoRaise( True )
        self.delete_button.setToolTip(_('Delete'))
        self.delete_button.clicked.connect( table.delete_selected_rows )
        self.add_button = QtGui.QToolButton()
        icon = self.new_icon.getQIcon()
        self.add_button.setIcon( icon )
        self.add_button.setAutoRaise( True )
        self.add_button.setToolTip(_('New'))
        self.add_button.clicked.connect(self.newRow)
        self.copy_button = QtGui.QToolButton()
        self.copy_button.setIcon( self.copy_icon.getQIcon() )
        self.copy_button.setAutoRaise( True )
        self.copy_button.setToolTip(_('Copy'))
        self.copy_button.clicked.connect( table.copy_selected_rows )
        export_button = QtGui.QToolButton()
        export_button.setIcon( self.spreadsheet_icon.getQIcon() )
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
                data = list(self.model.getData())
                for i, row in enumerate(data):
                    for j, column in enumerate(row):
                        if isinstance(column, basestring):
                            row[j] = _(column)
                    data[i] = row
                open_data_with_excel(title, columns, data)

        post( export )

    def getModel( self ):
        return self.model

    @QtCore.pyqtSlot(object)
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
            post( model._extend_cache, self.update_delegates )

    @gui_function
    def activate_editor( self, number_of_rows ):
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

    def newRow( self ):
        from camelot.view.workspace import show_top_level
        if self._new_message:
            QtGui.QMessageBox.information(self, _('New'), self._new_message)
            return

        if self.create_inline:

            @model_function
            def create():
                return self.model.append_object( self.admin.entity() )

            post( create, self.activate_editor )

        else:
            form = self.admin.create_new_view( related_collection_proxy=self.model, parent = None )
            show_top_level( form, self )

    def createFormForIndex( self, index ):
        from camelot.view.workspace import show_top_level
        from camelot.view.proxy.collection_proxy import CollectionProxy
        model = CollectionProxy( self.admin,
                                 self.model.get_collection,
                                 self.admin.get_fields,
                                 max_number_of_rows = 1,
                                 edits = None )
        form = self.admin.create_form_view( u'', model, self.model.map_to_source(index) )
        show_top_level( form, self )

