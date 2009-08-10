import logging

logger = logging.getLogger('camelot.view.controls.editors.onetomanyeditor')
from customeditor import *

from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function

class One2ManyEditor(CustomEditor):
  
  def __init__(self,
               admin=None,
               parent=None,
               create_inline=False,
               editable=True,
               **kw):
    """
:param admin: the Admin interface for the objects on the one side of the
relation

:param create_inline: if False, then a new entity will be created within a
new window, if True, it will be created inline

after creating the editor, setEntityInstance needs to be called to set the
actual data to the editor
"""

    CustomEditor.__init__(self, parent)
    layout = QtGui.QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    #
    # Setup table
    #
    from camelot.view.controls.tableview import TableWidget
    # parent set by layout manager
    self.table = TableWidget()
    layout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
    layout.addWidget(self.table) 
    self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                       QtGui.QSizePolicy.Expanding)
    self.connect(self.table.verticalHeader(),
                 QtCore.SIGNAL('sectionClicked(int)'),
                 self.createFormForIndex)
    self.admin = admin
    self.editable = editable
    self.create_inline = create_inline
    self.setupButtons(layout)
    self.setLayout(layout)
    self.model = None    

  def setupButtons(self, layout):
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    delete_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/places/user-trash.png').getQIcon()
    delete_button.setIcon(icon)
    delete_button.setAutoRaise(True)
    self.connect(delete_button,
                 QtCore.SIGNAL('clicked()'),
                 self.deleteSelectedRows)
    add_button = QtGui.QToolButton()
    icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
    add_button.setIcon(icon)
    add_button.setAutoRaise(True)
    self.connect(add_button, QtCore.SIGNAL('clicked()'), self.newRow)
    export_button = QtGui.QToolButton()
    export_button.setIcon(Icon('tango/16x16/mimetypes/x-office-spreadsheet.png').getQIcon())
    export_button.setAutoRaise(True)
    self.connect(export_button,
                 QtCore.SIGNAL('clicked()'),
                 self.exportToExcel)
    button_layout.addStretch()
    if self.editable:
      button_layout.addWidget(add_button)
      button_layout.addWidget(delete_button)
    button_layout.addWidget(export_button)
    layout.addLayout(button_layout)

  def exportToExcel(self):
    from camelot.view.export.excel import open_data_with_excel

    def export():
      title = self.admin.get_verbose_name_plural()
      columns = self.admin.getColumns()
      if self.model:
        data = list(self.model.getData())
        open_data_with_excel(title, columns, data)

    self.admin.mt.post(export)

  def getModel(self):
    return self.model

  def set_value(self, model):
    model = CustomEditor.set_value(self, model)
    if model:
      self.model = model
      self.table.setModel(model)

      def create_fill_model_cache(model):
        def fill_model_cache():
          model._extend_cache(0, 10)
          
        return fill_model_cache
      
      def create_delegate_updater(model):
        def update_delegates(*args):
          self.table.setItemDelegate(model.getItemDelegate())
          for i in range(self.model.columnCount()):
            txtwidth = self.model.headerData(i, Qt.Horizontal, Qt.SizeHintRole).toSize().width()
            colwidth = self.table.columnWidth(i)
            self.table.setColumnWidth(i, max(txtwidth, colwidth))
            
        return update_delegates

      self.admin.mt.post(create_fill_model_cache(model),
                         create_delegate_updater(model))
    
  def newRow(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()

    if self.create_inline:
      
      @model_function
      def create():
        o = self.admin.entity()
        row = self.model.insertEntityInstance(0,o)
        self.admin.setDefaults(o)
        return row
      
      @gui_function
      def activate_editor(row):
        index = self.model.index(row, 0)
        self.table.scrollToBottom()
        self.table.setCurrentIndex(index)
        self.table.edit(index)
        
      self.admin.mt.post(create, activate_editor)
        
    else:
      prependentity = lambda o: self.model.insertEntityInstance(0, o)
      removeentity = lambda o: self.model.removeEntityInstance(o)
      #
      # We cannot use the workspace as a parent, in case of working with 
      # the NoDesktopWorkspaces
      #
      form = self.admin.create_new_view(parent = None,
                                        oncreate=prependentity,
                                        onexpunge=removeentity)
      workspace.addSubWindow(form)
      form.show()
    
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row)

  def createFormForIndex(self, index):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace
    model = CollectionProxy(self.admin,
                            self.model.collection_getter,
                            self.admin.getFields,
                            max_number_of_rows=1,
                            edits=None)
    form = self.admin.create_form_view(u'', model, index, get_workspace())
    get_workspace().addSubWindow(form)
    form.show()
