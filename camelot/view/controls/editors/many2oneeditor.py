
from customeditor import *
from abstractmanytooneeditor import AbstractManyToOneEditor

from camelot.view.art import Icon
from camelot.view.model_thread import gui_function, model_function
from camelot.view.search import create_entity_search_query_decorator

class Many2OneEditor(CustomEditor, AbstractManyToOneEditor):
  """Widget for editing many 2 one relations"""
  
  class CompletionsModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
      QtCore.QAbstractListModel.__init__(self, parent)
      self._completions = []
    
    def setCompletions(self, completions):
      self._completions = completions
      self.emit(QtCore.SIGNAL('layoutChanged()'))
        
    def data(self, index, role):
      if role==Qt.DisplayRole:
        return QtCore.QVariant(self._completions[index.row()][0])
      elif role==Qt.EditRole:
        return QtCore.QVariant(self._completions[index.row()][1])
      return QtCore.QVariant()

    def rowCount(self, index=None):
      return len(self._completions)
    
    def columnCount(self, index=None):
      return 1
      
  def __init__(self, entity_admin=None, parent=None, **kwargs):
    """
:param entity_admin : The Admin interface for the object on the one side of
the relation
"""    

    CustomEditor.__init__(self, parent)
    self.admin = entity_admin
    self.entity_instance_getter = None
    self._entity_representation = ''
    self.entity_set = False
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)

    # Search button
    self.search_button = QtGui.QToolButton()
    self.search_button.setFocusPolicy(Qt.ClickFocus)
    icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
    self.search_button.setIcon(icon)
    self.search_button.setAutoRaise(True)
    self.connect(self.search_button,
                 QtCore.SIGNAL('clicked()'),
                 self.searchButtonClicked)

    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setFocusPolicy(Qt.ClickFocus)
    icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
    self.open_button.setIcon(icon)
    self.connect(self.open_button,
                 QtCore.SIGNAL('clicked()'),
                 self.openButtonClicked)
    self.open_button.setAutoRaise(True)

    # Search input
    self.search_input = QtGui.QLineEdit(self)
    self.setFocusProxy(self.search_input)
    #self.search_input.setReadOnly(True)
    #self.connect(self.search_input, 
    #             QtCore.SIGNAL('returnPressed()'),
    #             self.returnPressed)
    self.connect(self.search_input,
                 QtCore.SIGNAL('textEdited(const QString&)'),
                 self.textEdited)
    # suppose garbage was entered, we need to refresh the content
    self.connect(self.search_input,
                 QtCore.SIGNAL('editingFinished()'),
                 self.editingFinished)

    self.completer = QtGui.QCompleter()
    self.completions_model = self.CompletionsModel(self.completer)
    self.completer.setModel(self.completions_model)
    self.completer.setCaseSensitivity(Qt.CaseInsensitive)
    self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
    self.connect(self.completer,
                 QtCore.SIGNAL('activated(const QModelIndex&)'),
                 self.completionActivated)
    self.search_input.setCompleter(self.completer)

    # Setup layout
    self.layout.addWidget(self.search_input)
    self.layout.addWidget(self.search_button)
    self.layout.addWidget(self.open_button)
    self.setLayout(self.layout)
    self.setAutoFillBackground(True);
   
  def textEdited(self, text):
    
    def create_search_completion(text):
      return lambda: self.search_completions(text)
    
    self.admin.mt.post(create_search_completion(unicode(text)),
                       self.display_search_completions)
    self.completer.complete()

  @model_function
  def search_completions(self, text):
    """Search for object that match text, to fill the list of completions

:return: a list of tuples of (object_representation, object_getter)
"""
    search_decorator = create_entity_search_query_decorator(self.admin, text)
    return [(unicode(e),create_constant_function(e))
            for e in search_decorator(self.admin.entity.query).limit(20)]
  
  @gui_function
  def display_search_completions(self, completions):
    import sip
    if not sip.isdeleted(self):
      self.completions_model.setCompletions(completions)
      self.completer.complete()

  def completionActivated(self, index):
    object_getter = index.data(Qt.EditRole)
    self.setEntity(object_getter.toPyObject())

  def openButtonClicked(self):
    if self.entity_set:
      return self.createFormView()
    else:
      return self.createNew()
    
  def returnPressed(self):
    if not self.entity_set:
      self.createSelectView()
      
  def searchButtonClicked(self):
    if self.entity_set:
      self.setEntity(lambda:None)
    else:
      self.createSelectView()
      
  def trashButtonClicked(self):
    self.setEntity(lambda:None)
    
  @gui_function
  def createNew(self):
    
    @model_function
    def get_has_subclasses():
      return len(self.admin.getSubclasses())
    
    @gui_function
    def show_new_view(has_subclasses):
      selected = QtGui.QDialog.Accepted
      admin = self.admin
      if has_subclasses:
        from camelot.view.controls.inheritance import SubclassDialog
        select_subclass = SubclassDialog(self, self.admin)
        select_subclass.setWindowTitle('Select')
        selected = select_subclass.exec_()
        admin = select_subclass.selected_subclass
      if selected:
        from camelot.view.workspace import get_workspace
        workspace = get_workspace()
        form = admin.create_new_view(workspace)
        workspace.addSubWindow(form)
        self.connect(form, form.entity_created_signal, self.selectEntity)
        form.show()

    self.admin.mt.post(get_has_subclasses, show_new_view)

  def createFormView(self):
    if self.entity_instance_getter:
      
      def get_admin_and_title():
        object = self.entity_instance_getter()
        admin = self.admin.getSubclassEntityAdmin(object.__class__)
        return admin, ''
      
      def show_form_view(admin_and_title):
        admin, title = admin_and_title
        
        def create_collection_getter(instance_getter):
          return lambda:[instance_getter()]
        
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.view.workspace import get_workspace
  
        workspace = get_workspace()
        model = CollectionProxy(admin,
                         create_collection_getter(self.entity_instance_getter),
                         admin.getFields)
        self.connect(model,
                     QtCore.SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                     self.dataChanged)
        form = admin.create_form_view(title, model, 0, workspace)
        workspace.addSubWindow(form)
        form.show()
        
      self.admin.mt.post(get_admin_and_title, show_form_view)
    
  def dataChanged(self, index1, index2):
    self.setEntity(self.entity_instance_getter, False)
    
  def editingFinished(self):
    self.search_input.setText(self._entity_representation)
    
  def set_value(self, value):
    value = CustomEditor.set_value(self, value)
    if value:
      self.setEntity(value, propagate=False)
      
  def setEntity(self, entity_instance_getter, propagate=True):
    
    def create_instance_getter(entity_instance):
      return lambda:entity_instance
    
    def get_instance_represenation():
      """Get a representation of the instance

:return: (unicode, pk) its unicode representation and its primary key 
or ('', False) if the instance was None
"""
      entity = entity_instance_getter()
      self.entity_instance_getter = create_instance_getter(entity)
      if entity and hasattr(entity, 'id'):
        return (unicode(entity), entity.id)
      elif entity:
        return (unicode(entity), False)
      return ('', False)
    
    def set_instance_represenation(representation):
      """Update the gui"""
      import sip
      desc, pk = representation
      self._entity_representation = desc
      if not sip.isdeleted(self):
        self.search_input.setText(desc)
        if pk != False:
          icon = Icon('tango/16x16/places/folder.png').getQIcon()
          self.open_button.setIcon(icon)
          icon = Icon('tango/16x16/actions/edit-clear.png').getQIcon()
          self.search_button.setIcon(icon)
          self.entity_set = True
          #self.search_input.setReadOnly(True)
        else:
          icon = Icon('tango/16x16/actions/document-new.png').getQIcon()
          self.open_button.setIcon(icon)
          icon = Icon('tango/16x16/actions/system-search.png').getQIcon()
          self.search_button.setIcon(icon)
          self.entity_set = False
          #self.search_input.setReadOnly(False)
      if propagate:
        self.emit(QtCore.SIGNAL('editingFinished()'))
      
    self.admin.mt.post(get_instance_represenation, set_instance_represenation)
    
  def selectEntity(self, entity_instance_getter):
    self.setEntity(entity_instance_getter)
