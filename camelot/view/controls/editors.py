#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
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
#  ==================================================================================

"""Editors for various type of values"""

import logging

logger = logging.getLogger('editors')
logger.setLevel(logging.DEBUG)

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view import art

class IntegerEditor(QtGui.QSpinBox):
  """Widget for editing integer values"""
  def __init__(self, minimum=0, maximum=100, parent=None):
    super(IntegerEditor, self).__init__(parent)
    self.setRange(minimum, maximum)
    self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

class PlainTextEditor(QtGui.QLineEdit):
  """Widget for editing plain text"""
  def __init__(self, parent=None):
    super(PlainTextEditor, self).__init__(parent)

class DateEditor(QtGui.QDateEdit):
  """Widget for editing date values"""
  def __init__(self, minimum, maximum, format, parent=None):
    super(DateEditor, self).__init__(parent)
    self.format = format
    self.minimum = minimum
    self.maximum = maximum
    self.set_date_range()
    self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.setDisplayFormat(QtCore.QString(format))
    self.setCalendarPopup(True)

  def python_to_qt(self, value):
    return QtCore.QDate(value.day, value.month, value.year)

  def qt_to_python(self, value):
    import datetime
    return datetime.date(value.year(), value.month(), value.day())
  
  def set_date_range(self):
    qdate_min = self.python_to_qt(self.minimum)
    qdate_max = self.python_to_qt(self.maximum)
    self.setDateRange(qdate_min, qdate_max)

class FloatEditor(QtGui.QDoubleSpinBox):
  """Widget for editing float values"""
  def __init__(self, minimum=0.0, maximum=100.0, precision=3, parent=None):
    super(FloatEditor, self).__init__(parent)
    self.setRange(minimum, maximum)
    self.setDecimals(precision)
    self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.setSingleStep(1.0)

class Many2OneComboBox(QtGui.QComboBox):
  """Widget for editing many 2 one relations"""
  def __init__(self, entity_admin, parent=None):
    logger.info('Create Many2OneComboBox')
    from camelot.view.proxy.combo_proxy import ComboProxy
    QtGui.QComboBox.__init__(self, parent)
#    self.insertItem(0, 'zero')
#    self.insertItem(1, 'one')
#    self.insertItem(2, 'two')
    self.view = QtGui.QListView()
    self.model = ComboProxy(entity_admin, self.view, entity_admin.entity.query)
    #self.model = ComboProxy(entity_admin, self, entity_admin.entity.query)
    self.setModel(self.model)
    self.setView(self.view)
    self.view.setCurrentIndex(self.model.index(2,0))
    self.setCurrentIndex(2)
    self.setEditText('edit text')
  def setEntityInstance(self, entity_instance_getter):
    """Sets the current entity in the combo box"""
    self.model.setFirstRow(entity_instance_getter)

class CodeEditor(QtGui.QWidget):
  
  def __init__(self, parts, parent=None):
    super(CodeEditor, self).__init__(parent)
    self.setFocusPolicy(Qt.StrongFocus)
    self.parts = parts
    self.part_editors = []
    layout = QtGui.QHBoxLayout()
    #layout.setSpacing(0)
    layout.setMargin(0)
    for part in parts:
      editor = QtGui.QLineEdit()
      editor.setInputMask(part)
      self.part_editors.append(editor)
      layout.addWidget(editor)
      self.setFocusProxy(editor)
    self.setLayout(layout)
        
class Many2OneEditor(QtGui.QWidget):
  """Widget for editing many 2 one relations
  @param entity_admin : The Admin interface for the object on the one side of the relation
  """
  def __init__(self, entity_admin, parent=None):
    super(Many2OneEditor, self).__init__(parent)
    self.admin = entity_admin
    self.entity_instance_getter = None
    self.entity_set = False
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    # Search button
    self.search_button = QtGui.QToolButton()
    self.search_button.setIcon(QtGui.QIcon(art.icon16('actions/system-search')))
    self.search_button.setAutoRaise(True)
    self.connect(self.search_button, QtCore.SIGNAL('clicked()'), self.createSelectView)
    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
    self.connect(self.open_button, QtCore.SIGNAL('clicked()'), self.openButtonClicked)
    self.open_button.setAutoRaise(True)
    # Trash button
    self.trash_button = QtGui.QToolButton()
    self.trash_button.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
    self.connect(self.trash_button, QtCore.SIGNAL('clicked()'), self.trashButtonClicked)
    self.trash_button.setAutoRaise(True)     
    # Search input
    self.search_input = QtGui.QLineEdit()
    self.search_input.setReadOnly(True)
    #self.connect(self.search_input, QtCore.SIGNAL('returnPressed()'), self.emit_search)
    # Setup layout
    self.layout.addWidget(self.search_input)
    self.layout.addWidget(self.open_button)
    self.layout.addWidget(self.search_button)
    self.layout.addWidget(self.trash_button)
    self.setLayout(self.layout)
    
  def openButtonClicked(self):
    if self.entity_set:
      return self.createFormView()
    else:
      return self.createNew()
    
  def trashButtonClicked(self):
    self.setEntity(lambda:None)
    
  def createNew(self):
    from camelot.view.workspace import get_workspace, key_from_entity
    workspace = get_workspace()
    form = self.admin.createNewView(workspace)
    workspace.addWindow('new', form)
    self.connect(form, form.entity_created_signal, self.selectEntity)
    form.show()
        
  def createFormView(self):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace, key_from_entity
    if self.entity_instance_getter:
      
      def create_collection_getter(instance_getter):
        return lambda:[instance_getter()]
      
      workspace = get_workspace()  
      model = CollectionProxy(self.admin, create_collection_getter(self.entity_instance_getter), self.admin.getFields)
      form = self.admin.createFormView('', model, 0, workspace)
      workspace.addWindow(key_from_entity(self.admin.entity, 0), form)
      form.show()
    
  def setEntity(self, entity_instance_getter):
    
    def create_instance_getter(entity_instance):
      return lambda:entity_instance
    
    def get_instance_represenation():
      """Get a representation of the instance
      @return: (unicode, pk) its unicode representation and its primary key or ('', False) if the instance was None
      """
      entity = entity_instance_getter()
      self.entity_instance_getter = create_instance_getter(entity)
      if entity:
        return (unicode(entity), entity.id)
      return ('', False)
    
    def set_instance_represenation(representation):
      """Update the gui"""
      desc, pk = representation
      self.search_input.setText(desc)
      if pk!=False:
        self.open_button.setIcon(QtGui.QIcon(art.icon16('places/folder')))
        self.entity_set = True
      else:
        self.open_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
        self.entity_set = False 
      
    self.admin.mt.post(get_instance_represenation, set_instance_represenation)
    
  def createSelectView(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    select = self.admin.createSelectView(self.admin.entity.query, workspace)
    self.connect(select, select.entity_selected_signal, self.selectEntity)
    workspace.addWindow('select', select)
    select.show()
    
  def selectEntity(self, entity_instance_getter):
    self.setEntity(entity_instance_getter)
    
class One2ManyEditor(QtGui.QWidget):
  
  def __init__(self, entity_admin, field_name, parent=None):
    """
    @param entity_admin: the Admin interface for the objects on the one side of the relation  
    @param field_name: the name of the attribute on the entity_instance that contains the collection
                        of many objects
                        
    after creating the editor, setEntityInstance needs to be called to set
    the actual data to the editor
    """
    QtGui.QWidget.__init__(self, parent)
    self.layout = QtGui.QHBoxLayout()
    #
    # Setup table
    #
    self.table = QtGui.QTableView(parent)
    self.layout.addWidget(self.table)
    logger.debug('create querytable')
    self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.table.setSizePolicy(QtGui.QSizePolicy.Expanding,
                             QtGui.QSizePolicy.Expanding)

    self.connect(self.table.verticalHeader(),
                 QtCore.SIGNAL('sectionClicked(int)'),
                 self.createFormForIndex)
    
    from camelot.view.proxy.collection_proxy import CollectionProxy
    self.field_name = field_name
    self.admin = entity_admin
    self.model = CollectionProxy(entity_admin, lambda:[], entity_admin.getColumns)
    self.table.setModel(self.model)
    
    def update_delegates(*args):
      self.table.setItemDelegate(self.model.getItemDelegate())
      
    entity_admin.mt.post(lambda:None, update_delegates)
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    delete_button = QtGui.QPushButton( QtGui.QIcon(art.icon16('places/user-trash')), '')
    self.connect(delete_button, QtCore.SIGNAL('clicked()'), self.deleteSelectedRows)
    add_button = QtGui.QPushButton( QtGui.QIcon(art.icon16('actions/document-new')), '')
    self.connect(add_button, QtCore.SIGNAL('clicked()'), self.newRow)
    button_layout.addStretch()
    button_layout.addWidget(add_button)
    button_layout.addWidget(delete_button)      
    self.layout.addLayout(button_layout)
    self.setLayout(self.layout)
  
  def setEntityInstance(self, entity_instance_getter):
    self.model.setCollectionGetter(lambda:getattr(entity_instance_getter(), self.field_name))
    
  def newRow(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    form = self.admin.createNewView(workspace, delta_on_new=lambda e:self.model.insertRow(0, lambda:e))
    workspace.addWindow('new', form)
    #self.connect(form, form.entity_created_signal, lambda entity_instance_getter:)
    form.show()
  
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row, None)
          
  def createFormForIndex(self, index):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace
    parent = self.parentWidget().parentWidget().parentWidget().parentWidget()
    model = CollectionProxy(self.admin, self.model.collection_getter, self.admin.getFields, max_number_of_rows=1, edits=None)
    entity = model._get_object(index) 
    title = '%s - %s' % (entity, self.admin.getName())
    form = self.admin.createFormView(title, model, index, parent)
    get_workspace().addWindow('createFormForIndex', form)
    form.show()

class BoolEditor(QtGui.QCheckBox):
  """Widget for editing boolean values"""
  def __init__(self, parent=None):
    super(BoolEditor, self).__init__(parent)

class ImageEditor(QtGui.QLabel):
  pass

    
