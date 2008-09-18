"""Controls related to visualizing object hierarchy"""
import logging
import settings
import os

logger = logging.getLogger('controls.inheritance')

from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui

from camelot.view.controls.modeltree import ModelItem, ModelTree

#winnew = os.path.join(settings.CANTATE_ART_DIRECTORY, 'tango/16x16/actions/window-new.png')

QT_MAJOR_VERSION = float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2]))

#class SubclassTree(QtGui.QTreeWidget):
class SubclassTree(ModelTree):
  """Widget to select subclasses of a certain entity, where the
  subclasses are represented in a tree
  
  emits subclasssClicked when a subclass has been selected
  """
  
  def __init__(self, admin, parent):
    #QtGui.QTreeWidget.__init__(self, parent)
    header_labels = ['Types']
    super(SubclassTree, self).__init__(header_labels, parent)

    #if QT_MAJOR_VERSION > 4.3:
    #  self.setHeaderHidden(True)
    #else:
    #  self.setHeaderLabels(['Types'])

    self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    #self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
    self.admin = admin
    self.subclasses = []
    self.mt = admin.getModelThread()
    self.mt.post(lambda:self.admin.getSubclasses(), lambda subclasses:self.setSubclasses(subclasses))
    self.connect(self, QtCore.SIGNAL('clicked(const QModelIndex&)'), self.emitSubclassClicked)
        
  def setSubclasses(self, subclasses):
    logger.debug('set subclass tree')
    self.subclasses = subclasses
    if len(subclasses) > 1:
      self.clear_model_items()
      for cls in subclasses:
        #item = QtGui.QTreeWidgetItem(self, [cls.getName()])
        #column = 0
        #item.setIcon(column, QtGui.QIcon(winnew))
        item = ModelItem(self, [cls.getName()])
        self.modelitems.append(item)
    else:
      self.setMaximumWidth(0)

  def emitSubclassClicked(self, index):
    logger.debug('subclass clicked at position %s'%index.row())
    self.emit(QtCore.SIGNAL('subclasssClicked'), self.subclasses[index.row()])
