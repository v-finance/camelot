#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui
#from PyQt4 import QtCore

from one2manyeditor import One2ManyEditor
from abstractmanytooneeditor import AbstractManyToOneEditor

from camelot.view.art import Icon
from camelot.view.model_thread import model_function, post


class ManyToManyEditor( One2ManyEditor, AbstractManyToOneEditor ):

    def setupButtons( self, layout ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        self.remove_button = QtGui.QToolButton()
        self.remove_button.setIcon( Icon( 'tango/16x16/actions/list-remove.png' ).getQIcon() )
        self.remove_button.setAutoRaise( True )
        self.remove_button.setFixedHeight( self.get_height() )
        self.remove_button.clicked.connect(self.removeSelectedRows)
        self.add_button = QtGui.QToolButton()
        self.add_button.setIcon( Icon( 'tango/16x16/actions/list-add.png' ).getQIcon() )
        self.add_button.setAutoRaise( True )
        self.add_button.setFixedHeight( self.get_height() )
        self.add_button.clicked.connect(self.createSelectView)
        button_layout.addStretch()
        button_layout.addWidget( self.add_button )
        button_layout.addWidget( self.remove_button )
        layout.addLayout( button_layout )

    def set_field_attributes(self, editable=True, **kwargs):
        self.add_button.setEnabled(editable)
        self.remove_button.setEnabled(editable)

    def selectEntity( self, entity_instance_getter ):

        @model_function
        def insert():
            o = entity_instance_getter()
            self.model.insertEntityInstance( 0, o )

        post( insert, self.emit_editing_finished )

    def emit_editing_finished(self, *args):
        self.editingFinished.emit()

    def removeSelectedRows( self ):
        """Remove the selected rows in this tableview, but don't delete them"""
        self.model.remove_rows( set( map( lambda x: x.row(), self.table.selectedIndexes() ) ), delete=False)
        self.editingFinished.emit()
