from camelot.admin.entity_admin import EntityAdmin
from camelot.core.utils import ugettext_lazy as _
from camelot.view import forms


class Admin(EntityAdmin):
    verbose_name = _('person')
    verbose_name_plural = _('persons')
    list_display = ['first_name', 'last_name', ]
    form_display = forms.TabForm([('Basic', forms.Form(['first_name', 'last_name', 'contact_mechanisms',])),
                                  ('Official', forms.Form(['birthdate', 'social_security_number', 'passport_number',
                                                           'passport_expiry_date','addresses',])), ])
