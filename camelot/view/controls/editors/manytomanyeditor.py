from one2manyeditor import One2ManyEditor, QtGui, QtCore
from customeditor import editingFinished
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
        self.connect( self.remove_button,
                     QtCore.SIGNAL( 'clicked()' ),
                     self.removeSelectedRows )
        self.add_button = QtGui.QToolButton()
        self.add_button.setIcon( Icon( 'tango/16x16/actions/list-add.png' ).getQIcon() )
        self.add_button.setAutoRaise( True )
        self.add_button.setFixedHeight( self.get_height() )
        self.connect( self.add_button, QtCore.SIGNAL( 'clicked()' ), self.createSelectView )
#    new_button = QtGui.QToolButton()
#    new_button.setIcon(Icon('tango/16x16/actions/document-new.png').getQIcon())
#    new_button.setAutoRaise(True)
#    self.connect(new_button, QtCore.SIGNAL('clicked()'), self.newRow)
        button_layout.addStretch()
        button_layout.addWidget( self.add_button )
        button_layout.addWidget( self.remove_button )
#    button_layout.addWidget(new_button)
        layout.addLayout( button_layout )
    
    def set_field_attributes(self, editable=True, **kwargs):
        self.add_button.setEnabled(editable)
        self.remove_button.setEnabled(editable)
        
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
