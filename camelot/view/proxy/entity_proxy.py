from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class EntityProxy(QtCore.QObject):
  
  def __init__(self, admin, entity_getter):
    print 'entity proxy created'
    self.admin = admin
    self.entity_getter = entity_getter
    
  