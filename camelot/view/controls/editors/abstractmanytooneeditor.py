from PyQt4 import QtGui, QtCore

class AbstractManyToOneEditor(object):
    """Helper functions for implementing a `ManyToOneEditor`, to be used in the
  `ManyToOneEditor` and in the `ManyToManyEditor`
  """
    
    def createSelectView(self):
        #search_text = unicode(self.search_input.text())
        search_text = ''
        admin = self.admin
        query = self.admin.entity.query
        
        class SelectDialog(QtGui.QDialog):
            def __init__(self, parent):
                super(SelectDialog, self).__init__(parent)
                self.entity_selected_signal = QtCore.SIGNAL("entity_selected")
                layout = QtGui.QVBoxLayout()
                layout.setMargin(0)
                layout.setSpacing(0)
                self.setWindowTitle('Select %s'%admin.get_verbose_name())
                self.select = admin.create_select_view(query,
                                                       parent=parent,
                                                       search_text=search_text)
                layout.addWidget(self.select)
                self.setLayout(layout)
                self.connect(self.select, self.select.entity_selected_signal, self.selectEntity)
        
            def selectEntity(self, entity_instance_getter):
                self.emit(self.entity_selected_signal, entity_instance_getter)
                self.close()
        
        selectDialog = SelectDialog(self)
        self.connect(selectDialog, selectDialog.entity_selected_signal, self.selectEntity)
        selectDialog.exec_()
        
    def selectEntity(self, entity_instance_getter):
        #raise Exception('Not implemented')
        raise NotImplementedError
