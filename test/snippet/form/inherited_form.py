from copy import deepcopy

from camelot.view import forms

from .nested_form import Admin


class InheritedAdmin(Admin):
    form_display = deepcopy(Admin.form_display)
    form_display.add_tab('Official', forms.Form(['social_security_number', 'passport_number', 'passport_expiry_date'])) 
