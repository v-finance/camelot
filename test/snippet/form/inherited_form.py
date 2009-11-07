from copy import deepcopy

from camelot.view import forms
from nested_form import Admin

class InheritedAdmin(Admin):
    form_display = deepcopy(Admin.form_display)
    form_display.add_tab('Work', forms.Form(['employers', 'directed_organizations', 'shares'])) 

