#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui, QtCore

from camelot.core.utils import ugettext as _
from camelot.view.art import Icon
from camelot.view.model_thread import post

class FormPage(QtGui.QWizardPage):
    """FormPage is a generic wizard page that displays a form for an object
    in a wizard page, subclass this class to use it.  The class attribute 'Data'
    should be the class of the object to be used to store the form information.
    
    To access the data stored by the wizard form into a data object, use its
    get_data method.
    
    The 'Next' button will only be activated when the form is complete.
    """

    icon = Icon('tango/32x32/mimetypes/x-office-spreadsheet.png')
    title = None
    sub_title = None
    Data = None
    Admin = None

    def __init__(self, parent=None):
        
        from camelot.view.controls.formview import FormWidget
        from camelot.view.proxy.collection_proxy import CollectionProxy
        
        super(FormPage, self).__init__(parent)
        assert self.Data
        self.setTitle(unicode(self.get_title()))
        self.setSubTitle(unicode(self.get_sub_title()))
        self.setPixmap(QtGui.QWizard.LogoPixmap, self.get_icon().getQPixmap())
        self._data = self.Data()
        self._complete = False
        
        admin = self.get_admin()
        self._model = CollectionProxy(admin, lambda:[self._data], admin.get_fields)
        validator = self._model.get_validator()
        
        layout = QtGui.QVBoxLayout()
        form = FormWidget(self, admin)
        validator.validity_changed_signal.connect( self._validity_changed )
        form.set_model(self._model)
        layout.addWidget(form)
        self.setLayout(layout)

        if hasattr(admin, 'form_size'):
            self.setMinimumSize(admin.form_size[0], admin.form_size[1])
    
    def initializePage(self):
        # do inital validation, so the validity changed signal is valid
        self._complete = False
        self.completeChanged.emit()
        self._validity_changed(0)
        
    @QtCore.pyqtSlot(int)
    def _validity_changed(self, row):
        
        def is_valid():
            return self._model.get_validator().isValid(0)
        
        post(is_valid, self._change_complete)
        
    def _change_complete(self, complete):
        self._complete = complete
        self.completeChanged.emit()
            
    def isComplete(self):
        return self._complete
    
    def get_admin(self):
        from camelot.admin.application_admin import get_application_admin
        app_admin = get_application_admin()
        if self.Admin:
            return self.Admin(app_admin, self.Data)
        return app_admin.get_entity_admin(self.Data)
    
    def get_title(self):
        return self.title or self.get_admin().get_verbose_name()
    
    def get_sub_title(self):
        return self.sub_title or _('Please complete')
        
    def get_icon(self):
        return self.icon

    def get_data(self):
        return self._data


