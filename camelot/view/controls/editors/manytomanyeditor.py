from one2manyeditor import One2ManyEditor, QtGui, QtCore
from customeditor import editingFinished
from abstractmanytooneeditor import AbstractManyToOneEditor

from camelot.view.art import Icon
from camelot.view.model_thread import model_function, post

class ManyToManyEditor( One2ManyEditor, AbstractManyToOneEditor ):

    def setupButtons( self, layout ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        remove_button = QtGui.QToolButton()
        remove_button.setIcon( Icon( 'tango/16x16/actions/list-remove.png' ).getQIcon() )
        remove_button.setAutoRaise( True )
        remove_button.setFixedHeight( self.get_height() )
        self.connect( remove_button,
                     QtCore.SIGNAL( 'clicked()' ),
                     self.removeSelectedRows )
        add_button = QtGui.QToolButton()
        add_button.setIcon( Icon( 'tango/16x16/actions/list-add.png' ).getQIcon() )
        add_button.setAutoRaise( True )
        add_button.setFixedHeight( self.get_height() )
        self.connect( add_button, QtCore.SIGNAL( 'clicked()' ), self.createSelectView )
#    new_button = QtGui.QToolButton()
#    new_button.setIcon(Icon('tango/16x16/actions/document-new.png').getQIcon())
#    new_button.setAutoRaise(True)
#    self.connect(new_button, QtCore.SIGNAL('clicked()'), self.newRow)
        button_layout.addStretch()
        button_layout.addWidget( add_button )
        button_layout.addWidget( remove_button )
#    button_layout.addWidget(new_button)
        layout.addLayout( button_layout )
    
    def selectEntity( self, entity_instance_getter ):
  
        @model_function
        def insert():
            o = entity_instance_getter()
            self.model.insertEntityInstance( 0, o )
      
        post( insert, self.editingFinished )
      
    def editingFinished(self, *args):
        self.emit( editingFinished )
    
    def removeSelectedRows( self ):
        """Remove the selected rows in this tableview, but don't delete them"""
        for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
            self.model.removeRow( row, delete = False )
        self.emit( editingFinished )
