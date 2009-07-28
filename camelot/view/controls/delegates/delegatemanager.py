
from customdelegate import *

import logging
logger = logging.getLogger('camelot.view.controls.delegates.delegatemanager')

class DelegateManager(QItemDelegate):
  """Manages custom delegates, should not be used by the application
developer
"""

  def __init__(self, parent=None, **kwargs):
    QItemDelegate.__init__(self, parent)
    self.delegates = {}

  def set_columns_desc(self, columnsdesc):
    self.columnsdesc = columnsdesc

  def insertColumnDelegate(self, column, delegate):
    """Inserts a custom column delegate"""
    logger.debug('inserting delegate for column %s' % column)
    delegate.setParent(self)
    self.delegates[column] = delegate
    self.connect(delegate, SIGNAL('commitData(QWidget*)'), self.commitData)
    self.connect(delegate, SIGNAL('closeEditor(QWidget*)'), self.closeEditor)

  def commitData(self, editor):
    self.emit(SIGNAL('commitData(QWidget*)'), editor)
    
  def closeEditor(self, editor):
    self.emit(SIGNAL('closeEditor(QWidget*)'), editor)
    
  def removeColumnDelegate(self, column):
    """Removes custom column delegate"""
    logger.debug('removing a new custom column delegate')
    if column in self.delegates:
      del self.delegates[column]

  def paint(self, painter, option, index):
    """Use a custom delegate paint method if it exists"""
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.paint(painter, option, index)
    else:
      QItemDelegate.paint(self, painter, option, index)

  def createEditor(self, parent, option, index):
    """Use a custom delegate createEditor method if it exists"""
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      return delegate.createEditor(parent, option, index)
    else:
      QItemDelegate.createEditor(self, parent, option, index)

  def setEditorData(self, editor, index):
    """Use a custom delegate setEditorData method if it exists"""
    logger.debug('setting editor data for column %s' % index.column())
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.setEditorData(editor, index)
    else:
      QItemDelegate.setEditorData(self, editor, index)

  def setModelData(self, editor, model, index):
    """Use a custom delegate setModelData method if it exists"""
    logger.debug('setting model data for column %s' % index.column())
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      delegate.setModelData(editor, model, index)
    else:
      QItemDelegate.setModelData(self, editor, model, index)
      
  def sizeHint(self, option, index):
    option = QtGui.QStyleOptionViewItem()
    delegate = self.delegates.get(index.column())
    if delegate is not None:
      return delegate.sizeHint(option, index)
    else:
      return QItemDelegate.sizeHint(self, option, index)
