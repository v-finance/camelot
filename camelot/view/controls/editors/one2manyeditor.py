import logging

logger = logging.getLogger( 'camelot.view.controls.editors.onetomanyeditor' )
from customeditor import CustomEditor, QtCore, QtGui, Qt
from wideeditor import WideEditor

from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function, post
from camelot.core.utils import ugettext as _

class One2ManyEditor( CustomEditor, WideEditor ):

    def __init__( self,
                 admin = None,
                 parent = None,
                 create_inline = False,
                 editable = True,
                 **kw ):
        """
    :param admin: the Admin interface for the objects on the one side of the
    relation
    
    :param create_inline: if False, then a new entity will be created within a
    new window, if True, it will be created inline
    
    after creating the editor, setEntityInstance needs to be called to set the
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
        self.connect( self.table.verticalHeader(),
                     QtCore.SIGNAL( 'sectionClicked(int)' ),
                     self.createFormForIndex )
        self.admin = admin
        self.editable = editable
        self.create_inline = create_inline
        layout.addWidget( self.table )
        self.setupButtons( layout )
        self.setLayout( layout )
        self.model = None
    
    def setupButtons( self, layout ):
        button_layout = QtGui.QVBoxLayout()
        button_layout.setSpacing( 0 )
        delete_button = QtGui.QToolButton()
        icon = Icon( 'tango/16x16/places/user-trash.png' ).getQIcon()
        delete_button.setIcon( icon )
        delete_button.setAutoRaise( True )
        delete_button.setToolTip(_('delete'))
        self.connect( delete_button,
                     QtCore.SIGNAL( 'clicked()' ),
                     self.deleteSelectedRows )
        add_button = QtGui.QToolButton()
        icon = Icon( 'tango/16x16/actions/document-new.png' ).getQIcon()
        add_button.setIcon( icon )
        add_button.setAutoRaise( True )
        add_button.setToolTip(_('new'))
        self.connect( add_button, QtCore.SIGNAL( 'clicked()' ), self.newRow )
        copy_button = QtGui.QToolButton()
        icon = Icon( 'tango/16x16/actions/edit-copy.png' ).getQIcon()
        copy_button.setIcon( icon )
        copy_button.setAutoRaise( True )
        copy_button.setToolTip(_('copy'))
        self.connect( copy_button, QtCore.SIGNAL( 'clicked()' ), self.copy_selected_rows )        
        export_button = QtGui.QToolButton()
        export_button.setIcon( Icon( 'tango/16x16/mimetypes/x-office-spreadsheet.png' ).getQIcon() )
        export_button.setAutoRaise( True )
        export_button.setToolTip(_('export as spreadsheet'))
        self.connect( export_button,
                     QtCore.SIGNAL( 'clicked()' ),
                     self.exportToExcel )
        button_layout.addStretch()
        if self.editable:
            button_layout.addWidget( add_button )
            button_layout.addWidget( copy_button )
            button_layout.addWidget( delete_button )
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
        if model:
            self.model = model
            self.table.setModel( model )
      
            def create_fill_model_cache( model ):
              
                def fill_model_cache():
                    model._extend_cache( 0, 10 )
          
                return fill_model_cache
        
            post( create_fill_model_cache( model ), self.update_delegates )
      
    @gui_function
    def activate_editor( self, row ):
        index = self.model.index( row, 0 )
        self.table.scrollToBottom()
        self.table.setCurrentIndex( index )
        self.table.edit( index )
            
    def newRow( self ):
        from camelot.view.workspace import get_workspace
        workspace = get_workspace()
    
        if self.create_inline:
    
            @model_function
            def create():
                o = self.admin.entity()
                row = self.model.insertEntityInstance( 0, o )
                self.admin.set_defaults( o )
                return row
        
            post( create, self.activate_editor )
      
        else:
            prependentity = lambda o: self.model.insertEntityInstance( 0, o )
            removeentity = lambda o: self.model.removeEntityInstance( o )
            #
            # We cannot use the workspace as a parent, in case of working with 
            # the NoDesktopWorkspaces
            #
            form = self.admin.create_new_view( parent = None,
                                               oncreate = prependentity,
                                               onexpunge = removeentity )
            workspace.addSubWindow( form )
            form.show()
            
    def copy_selected_rows( self ):
        """Copy the selected rows in this tableview"""
        logger.debug( 'delete selected rows called' )
        for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
            self.model.copy_row( row )        
      
    def deleteSelectedRows( self ):
        """Delete the selected rows in this tableview"""
        logger.debug( 'delete selected rows called' )
        for row in set( map( lambda x: x.row(), self.table.selectedIndexes() ) ):
            self.model.removeRow( row )
      
    def createFormForIndex( self, index ):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.view.workspace import get_workspace
        model = CollectionProxy( self.admin,
                                self.model.collection_getter,
                                self.admin.get_fields,
                                max_number_of_rows = 1,
                                edits = None )
        form = self.admin.create_form_view( u'', model, index, get_workspace() )
        get_workspace().addSubWindow( form )
        form.show()
