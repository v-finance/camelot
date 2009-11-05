import logging
logger = logging.getLogger('camelot.view.controls.delegates.delegatemanager')

from PyQt4 import QtGui, QtCore

class DelegateManager(QtGui.QItemDelegate):
    """Manages custom delegates, should not be used by the application
  developer
  """
  
    def __init__(self, parent=None, **kwargs):
        QtGui.QItemDelegate.__init__(self, parent)
        self.delegates = {}
    
    def set_columns_desc(self, columnsdesc):
        self.columnsdesc = columnsdesc
        
    def get_column_delegate(self, column):
        try:
            return self.delegates[column]
        except KeyError:
            logger.error('Programming Error, no delegate available for column %s'%column)
            logger.error('Available columns : %s'%unicode(self.delegates.keys()))
            raise KeyError
    
    def insertColumnDelegate(self, column, delegate):
        """Inserts a custom column delegate"""
        logger.debug('inserting delegate for column %s' % column)
        assert delegate
        delegate.setParent(self)
        self.delegates[column] = delegate
        self.connect(delegate, QtCore.SIGNAL('commitData(QWidget*)'), self.commitData)
        self.connect(delegate, QtCore.SIGNAL('closeEditor(QWidget*)'), self.closeEditor)
    
    def commitData(self, editor):
        self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
        
    def closeEditor(self, editor):
        self.emit(QtCore.SIGNAL('closeEditor(QWidget*)'), editor)
        
    def removeColumnDelegate(self, column):
        """Removes custom column delegate"""
        logger.debug('removing a custom column delegate')
        if column in self.delegates:
            del self.delegates[column]
      
    def paint(self, painter, option, index):
        """Use a custom delegate paint method if it exists"""
        delegate = self.get_column_delegate(index.column())
        delegate.paint(painter, option, index)
      
    def createEditor(self, parent, option, index):
        """Use a custom delegate createEditor method if it exists"""
        delegate = self.get_column_delegate(index.column())
        editor = delegate.createEditor(parent, option, index)
        assert editor
        return editor
    
    def setEditorData(self, editor, index):
        """Use a custom delegate setEditorData method if it exists"""
        logger.debug('setting editor data for column %s' % index.column())
        delegate = self.get_column_delegate(index.column())
        delegate.setEditorData(editor, index)
      
    def setModelData(self, editor, model, index):
        """Use a custom delegate setModelData method if it exists"""
        logger.debug('setting model data for column %s' % index.column())
        delegate = self.get_column_delegate(index.column())
        delegate.setModelData(editor, model, index)
            
    def sizeHint(self, option, index):
        option = QtGui.QStyleOptionViewItem()
        delegate = self.get_column_delegate(index.column())
        return delegate.sizeHint(option, index)
