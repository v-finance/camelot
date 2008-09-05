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

class Many2OneEditor(QtGui.QWidget):
  """Widget for editing many 2 one relations
  @param entity_admin : The Admin interface for the object on the one side of the relation
  """
  def __init__(self, entity_admin, parent=None):
    super(Many2OneEditor, self).__init__(parent)
    self.admin = entity_admin
    layout = QtGui.QHBoxLayout()
    layout.setSpacing(0)
    layout.setMargin(0)
    # Search button
    self.search_button = QtGui.QToolButton()
    self.search_button.setIcon(QtGui.QIcon(art.icon16('actions/system-search')))
    self.search_button.setAutoRaise(True)
    self.connect(self.search_button, QtCore.SIGNAL('clicked()'), self.createSelectView)
    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setIcon(QtGui.QIcon(art.icon16('places/folder')))
    self.open_button.setAutoRaise(True)    
    # Search input
    self.search_input = QtGui.QLineEdit()
    self.search_input.setReadOnly(True)
    #self.connect(self.search_input, QtCore.SIGNAL('returnPressed()'), self.emit_search)
    # Setup layout
    layout.addWidget(self.search_input)
    layout.addWidget(self.open_button)
    layout.addWidget(self.search_button)
    self.setLayout(layout)
  def setEntity(self, entity_instance_getter):
    
    def get_unicode():
      """Get unicode representation of instance"""
      return unicode(entity_instance_getter())
    
    def set_unicode(txt):
      self.search_input.setText(txt)
      
    self.admin.mt.post(get_unicode, set_unicode)
    
  def createSelectView(self):
    parent = self.parentWidget().parentWidget().parentWidget().parentWidget()
    select = self.admin.createSelectView(self.admin.entity.query, parent)
    parent.workspace.addWindow(select)
    select.show()
    
  def createForm(self):
    pass
    
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
    self.model = CollectionProxy(entity_admin, self.table, lambda:[], entity_admin.getColumns, max_number_of_rows=10, edits=None)
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
    self.model.insertRow(0, None)
  
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row, None)
          
  def createFormForIndex(self, index):
    title = 'Row %s - %s' % (index, self.admin.getName())
    parent = self.parentWidget().parentWidget().parentWidget().parentWidget()
    
    existing = parent.findMdiChild(title)
    if existing is not None:
      parent.workspace.setActiveWindow(existing)
      return

    form = self.admin.createFormView(title, self.model, index, parent)

    width = int(parent.width() / 2)
    height = int(parent.height() / 2)
    form.resize(width, height)
    
    parent.workspace.addWindow(form)
    
    key = 'Form View: %s' % str(title)
    parent.childwindows[key] = form

    form.show()

class BoolEditor(QtGui.QCheckBox):
  """Widget for editing boolean values"""
  def __init__(self, parent=None):
    super(BoolEditor, self).__init__(parent)
#    self.addItems(['false', 'true'])
#    self.setEditable(True)

    
