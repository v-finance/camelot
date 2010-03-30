from PyQt4 import QtCore

from camelot.view import forms
from camelot.view.controls import delegates
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.application_admin import ApplicationAdmin

class FormWithHiddenWidget(forms.Form):
    
    def render(self, widgets, *args, **kwargs):

        form_widget = super(FormWithHiddenWidget, self).render(widgets, *args, **kwargs)
        
        _show_more_label, show_more_editor = widgets['show_more']
        hidden_label, hidden_editor        = widgets['details']
        
        form_widget.connect(show_more_editor, QtCore.SIGNAL('stateChanged(int)'), hidden_label.setVisible)
        form_widget.connect(show_more_editor, QtCore.SIGNAL('stateChanged(int)'), hidden_editor.setVisible)
        
        hidden_label.hide()
        hidden_editor.hide()

        return form_widget
        
class ExampleObject(object):
    
    def __init__(self):
        self.show_more = False
        self.details = u''
        
    class Admin(ObjectAdmin):
        form_display = FormWithHiddenWidget(['show_more', 'details'])
        field_attributes = {'show_more':{'delegate':delegates.BoolDelegate, 'editable':True},
                            'details':{'delegate':delegates.RichTextDelegate, 'editable':True}}
        
if __name__ == "__main__":
    from camelot.view.main import main
    from PyQt4 import QtGui
    app_admin = ApplicationAdmin()
    
    def show_form():
        dialog = QtGui.QDialog()
        example_admin = ExampleObject.Admin(app_admin, ExampleObject)
        form = example_admin.create_new_view(parent=dialog)
        form.show()
        dialog.exec_()
        
    main(app_admin, initialization=show_form)
