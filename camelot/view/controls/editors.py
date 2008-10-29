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
import os
import os.path
import tempfile
import logging
import settings

logger = logging.getLogger('editors')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view import art
from camelot.view.model_thread import model_function

class DateEditor(QtGui.QWidget):
  """Widget for editing date values"""
  def __init__(self, delegate=None, nullable=True, format='dd/MM/yyyy', parent=None):
    super(DateEditor, self).__init__(parent)
    self.format = format
    self.delegate = delegate
    self.index = None
    self.qdateedit = QtGui.QDateEdit(self)
    self.connect(self.qdateedit, QtCore.SIGNAL('editingFinished ()'), self.editingFinished)
    self.qdateedit.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.qdateedit.setDisplayFormat(QtCore.QString(format))
    self.hlayout = QtGui.QHBoxLayout()
    self.hlayout.addWidget(self.qdateedit)
    
    if nullable:
      nullbutton = QtGui.QToolButton()
      nullbutton.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
      nullbutton.setAutoRaise(True)
      #nullbutton.setCheckable(True)
      self.connect(nullbutton, QtCore.SIGNAL('clicked()'), self.setMinimumDate)
      self.qdateedit.setSpecialValueText('0/0/0')
      self.hlayout.addWidget(nullbutton)
          
    self.hlayout.setContentsMargins(0, 0, 0, 0)
    self.hlayout.setMargin(0)
    self.hlayout.setSpacing(0)

    self.setContentsMargins(0, 0, 0, 0)
    self.setLayout(self.hlayout)

    import datetime
    self.minimum = datetime.date.min
    self.maximum = datetime.date.max
    self.set_date_range()

    self.setFocusProxy(self.qdateedit)

  def _python_to_qt(self, value):
    return QtCore.QDate(value.year, value.month, value.day)

  def _qt_to_python(self, value):
    import datetime
    return datetime.date(value.year(), value.month(), value.day())
  
  def editingFinished(self):
    if self.index:
      self.delegate.setModelData(self, self.index.model(), self.index)
      
  def set_date_range(self):
    qdate_min = self._python_to_qt(self.minimum)
    qdate_max = self._python_to_qt(self.maximum)
    self.qdateedit.setDateRange(qdate_min, qdate_max)

  def date(self):
    return self.qdateedit.date()

  def minimumDate(self):
    return self.qdateedit.minimumDate()

  def setMinimumDate(self):
    self.qdateedit.setDate(self.minimumDate())
    if self.index:
      self.delegate.setModelData(self, self.index.model(), self.index)

  def setDate(self, date):
    self.qdateedit.setDate(date)

class VirtualAddressEditor(QtGui.QWidget):
  
  def __init__(self, parent=None):
    import camelot.types
    super(VirtualAddressEditor, self).__init__(parent)
    self.delegate = None
    self.index = None
    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    self.combo = QtGui.QComboBox()
    self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
    layout.addWidget(self.combo)
    self.editor = QtGui.QLineEdit()
    layout.addWidget(self.editor)
    self.connect(self.editor, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.setLayout(layout)
  def editingFinished(self):
    if self.delegate:
      self.delegate.setModelData(self, self.index.model(), self.index)
        
class CodeEditor(QtGui.QWidget):
  
  def __init__(self, parts=['99', 'AA'], delegate=None, parent=None):
    super(CodeEditor, self).__init__(parent)
    self.setFocusPolicy(Qt.StrongFocus)
    self.parts = parts
    self.part_editors = []
    self.delegate = delegate
    self.index = None
    layout = QtGui.QHBoxLayout()
    #layout.setSpacing(0)
    layout.setMargin(0)
    for part in parts:
      editor = QtGui.QLineEdit()
      editor.setInputMask(part)
      editor.installEventFilter(self)
      self.part_editors.append(editor)
      layout.addWidget(editor)
      self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.setLayout(layout)
  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))
    self.delegate.setModelData(self, self.index.model(), self.index)
        
class Many2OneEditor(QtGui.QWidget):
  """Widget for editing many 2 one relations
  @param entity_admin : The Admin interface for the object on the one side of the relation
  """
  def __init__(self, entity_admin=None, delegate=None, parent=None):
    super(Many2OneEditor, self).__init__(parent)
    self.admin = entity_admin
    self.index = None
    self.entity_instance_getter = None
    self.entity_set = False
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    self.delegate = delegate
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
    
  def setEntity(self, entity_instance_getter, propagate=True):
    
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
      if propagate:
        self.delegate.setModelData(self, self.index.model(), self.index)
      
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
  
  def __init__(self, entity_admin=None, field_name=None, parent=None):
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

    self.admin = entity_admin
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    delete_button = QtGui.QToolButton()
    delete_button.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
    delete_button.setAutoRaise(True)
    self.connect(delete_button, QtCore.SIGNAL('clicked()'), self.deleteSelectedRows)
    add_button = QtGui.QToolButton()
    add_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
    add_button.setAutoRaise(True)
    self.connect(add_button, QtCore.SIGNAL('clicked()'), self.newRow)
    button_layout.addStretch()
    button_layout.addWidget(add_button)
    button_layout.addWidget(delete_button)      
    self.layout.addLayout(button_layout)
    self.setLayout(self.layout)
    self.model = None
  
  def setModel(self, model):
    self.model = model
    self.table.setModel(model)
    
    def create_fill_model_cache(model):
      
      def fill_model_cache():
        model._extend_cache(0, 10)
        
      return fill_model_cache
        
    def create_delegate_updater(model):
      
      def update_delegates(*args):
        self.table.setItemDelegate(model.getItemDelegate())
        self.table.resizeColumnsToContents()
          
      return update_delegates
      
    self.admin.mt.post(create_fill_model_cache(model), create_delegate_updater(model))
    
  def newRow(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    form = self.admin.createNewView(workspace)
    workspace.addWindow('new', form)
    self.connect(form, form.entity_created_signal, self.entityCreated)
    form.show()
  
  def entityCreated(self, entity_instance_getter):
    self.model.insertRow(0, entity_instance_getter)
    
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row)
          
  def createFormForIndex(self, index):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace
    model = CollectionProxy(self.admin, self.model.collection_getter, self.admin.getFields, max_number_of_rows=1, edits=None)
    title = self.admin.getName()
    form = self.admin.createFormView(title, model, index, get_workspace())
    get_workspace().addWindow('createFormForIndex', form)
    form.show()

#class ImageEditor(QtGui.QLabel):
#  def __init__(self, parent=None):
#    QtGui.QLabel.__init__(self, parent)
#    self.setAcceptDrops(True)
    
#  def dragEnterEvent(self, event):
#    event.acceptProposedAction()

#  def dragMoveEvent(self, event):
#    event.acceptProposedAction()

#  def dropEvent(self, event):
#    if event.mimeData().hasUrls():
#      url = event.mimeData().urls()[0]
#      filename = url.toLocalFile()
#      if filename != '':
#        self.setPixmap(QtGui.QPixmap(filename))
#        self.file_url = url

try:
  from PIL import Image as PILImage
except:
  import Image as PILImage

class ImageEditor(QtGui.QWidget):
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.image = None
    self.delegate = None
    self.index = None    
    self.layout = QtGui.QHBoxLayout()
    #
    # Setup label
    #
    self.label = QtGui.QLabel(parent)
    self.layout.addWidget(self.label)
    self.label.setAcceptDrops(True)
    self.draw_border()
    self.label.__class__.dragEnterEvent = self.dragEnterEvent
    self.label.__class__.dragMoveEvent = self.dragEnterEvent
    self.label.__class__.dropEvent = self.dropEvent
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    button_layout.setMargin(0)

    clear_button = QtGui.QToolButton()
    clear_button.setIcon( QtGui.QIcon(art.icon16('places/user-trash')))
    clear_button.setToolTip('Clear image')
    clear_button.setAutoRaise(True)
    self.connect(clear_button, QtCore.SIGNAL('clicked()'), self.clearImage)

    file_button = QtGui.QToolButton()
    file_button.setIcon( QtGui.QIcon(art.icon16('status/folder-open')))
    file_button.setAutoRaise(True)
    file_button.setToolTip('Open file')
    self.connect(file_button, QtCore.SIGNAL('clicked()'), self.openFileDialog)

    app_button = QtGui.QToolButton()
    app_button.setIcon( QtGui.QIcon(art.icon16('actions/document-new')))
    app_button.setAutoRaise(True)
    app_button.setToolTip('Open in viewer')
    self.connect(app_button, QtCore.SIGNAL('clicked()'), self.openInApp)

    vspacerItem = QtGui.QSpacerItem(20,20,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
    
    button_layout.addItem(vspacerItem)
    button_layout.addWidget(clear_button)
    button_layout.addWidget(file_button)      
    button_layout.addWidget(app_button)      

    self.layout.addLayout(button_layout)
    
    hspacerItem = QtGui.QSpacerItem(20,20,QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
    self.layout.addItem(hspacerItem)
    self.setLayout(self.layout)
    #
    # Image
    #
    self.dummy_image = os.path.normpath(art.icon32('apps/stock_help'))
    if self.image is None:
      testImage = QtGui.QImage(self.dummy_image)
      if not testImage.isNull():
        fp = open(self.dummy_image, 'rb')
        self.image = PILImage.open(fp)
        self.setPixmap(QtGui.QPixmap(self.dummy_image))
  #
  # Drag & Drop
  #
  def dragEnterEvent(self, event):
    event.acceptProposedAction()

  def dragMoveEvent(self, event):
    event.acceptProposedAction()

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      url = event.mimeData().urls()[0]
      filename = url.toLocalFile()
      if filename != '':
        self.pilimage_from_file(filename)

  #
  # Buttons methods
  #
  def clearImage(self):
    self.pilimage_from_file(self.dummy_image)
    self.draw_border()

  def openFileDialog(self):
    filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm)
All files (*)"""
    
    filename = QtGui.QFileDialog.getOpenFileName(self, 
                                                'Open file', 
                                                QtCore.QDir.currentPath(),
                                                filter)
    if filename != '':
      self.pilimage_from_file(filename)

  def openInApp(self):
    if self.image != None:
      tmpfp, tmpfile = tempfile.mkstemp(suffix='.png')
      self.image.save(os.fdopen(tmpfp, 'wb'), 'png')
      QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(tmpfile))

  #
  # Utils methods
  #

  def pilimage_from_file(self, filepath):
    testImage = QtGui.QImage(filepath)
    if not testImage.isNull() and self.delegate:
      fp = open(filepath, 'rb')
      self.image = PILImage.open(fp)
      self.delegate.setModelData(self, self.index.model(), self.index )
  
  def draw_border(self):
    self.label.setFrameShape(QtGui.QFrame.Box)
    self.label.setFrameShadow(QtGui.QFrame.Plain)
    self.label.setLineWidth(1)
    self.label.setFixedSize(100, 100)
   
  def setPixmap(self, pixmap):
    self.label.setPixmap(pixmap)      

  def __setattr__(self, name, value):
    QtGui.QWidget.__setattr__(self, name, value)
    if name == 'delegate':
      if 'label' in self.__dict__:
        self.draw_border() 
        

class RichTextEditor(QtGui.QTextEdit):
  
  def __init__(self, parent=None):
    QtGui.QTextEdit.__init__(self, parent)


    
