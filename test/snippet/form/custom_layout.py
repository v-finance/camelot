from PyQt4 import QtGui

from camelot.view import forms
from camelot.admin.entity_admin import EntityAdmin

class CustomForm(forms.Form):
    
    def __init__(self):
        super(CustomForm, self).__init__(['first_name', 'last_name'])
        
    def render( self, widgets, parent = None, nomargins = False ):
        widget = QtGui.QWidget(parent)
        layout = QtGui.QFormLayout()
        layout.addRow(QtGui.QLabel('Please fill in the complete name :', widget))
        for _field_name,(field_label, field_editor) in widgets.items():
            layout.addRow(field_label, field_editor)
        widget.setLayout(layout)
        widget.setBackgroundRole(QtGui.QPalette.ToolTipBase)
        widget.setAutoFillBackground(True)
        return widget

class Admin(EntityAdmin):
    list_display = ['first_name', 'last_name']
    form_display = CustomForm()
    form_size = (300,100)