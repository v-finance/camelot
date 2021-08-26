from collections import Iterable

from dataclasses import field

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.dataclasses import dataclass
from camelot.core.qt import QtGui, QtWidgets
from camelot.view.forms import AbstractForm


@dataclass
class CustomForm( AbstractForm ):
    content: Iterable = field(init=False)
    scrollbars: bool = field(init=False)
    columns: int = field(init=False)
    
    def __post_init__(self):
        self.content = ['first_name', 'last_name']
        super().__init__(self.content)

    @classmethod
    def render(cls, editor_factory, form, parent=None, nomargins=False ):
        widget = QtWidgets.QWidget( parent )
        layout = QtWidgets.QFormLayout()
        layout.addRow( QtWidgets.QLabel('Please fill in the complete name :', widget ) )
        for field_name in cls.get_content_fields(form):
            field_editor = editor_factory.create_editor( field_name, widget )
            field_label = editor_factory.create_label( field_name, field_editor, widget )
            layout.addRow( field_label, field_editor )
        widget.setLayout( layout )
        widget.setBackgroundRole( QtGui.QPalette.ToolTipBase )
        widget.setAutoFillBackground( True )
        return widget

class Admin(EntityAdmin):
    list_display = ['first_name', 'last_name']
    form_display = CustomForm()
    form_size = (300,100)
