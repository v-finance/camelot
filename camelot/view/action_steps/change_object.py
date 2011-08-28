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

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage

class ChangeObjectDialog( StandaloneWizardPage ):
    
    def __init__( self, 
                  obj, 
                  admin, 
                  parent=None, 
                  flags=QtCore.Qt.WindowFlags(0) ):
        """A dialog to change an object.  This differs from a FormView in that
        it does not contains Actions, and has an OK button that is enabled when
        the object is valid.
        :param obj: The object to change
        :param admin: The admin class used to create a form
        """
        from camelot.view.controls.formview import FormWidget
        from camelot.view.proxy.collection_proxy import CollectionProxy
        super(ChangeObjectDialog, self).__init__( '', parent, flags )
        
        self.setWindowTitle( admin.get_verbose_name() )
        #self.set_banner_logo_pixmap(art.Icon('tango/22x22/categories/preferences-system.png').getQPixmap())
        self.set_banner_title( _('Please complete') )
        self.set_banner_subtitle(_('Complete the form and press the OK button'))
        self.banner_widget().setStyleSheet('background-color: white;')
        
        model = CollectionProxy(admin, lambda:[obj], admin.get_fields)
        validator = model.get_validator()
        layout = QtGui.QVBoxLayout()
        form_widget = FormWidget( parent=self, admin=admin )
        layout.addWidget( form_widget )
        validator.validity_changed_signal.connect( self._validity_changed )
        form_widget.set_model( model )
        self.main_widget().setLayout(layout)
    
        # do inital validation, so the validity changed signal is valid
        self._valid = False
        #self._validity_changed(0)
        
        cancel_button = QtGui.QPushButton( _('Cancel') )
        ok_button = QtGui.QPushButton( _('OK') )
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        layout.addWidget( cancel_button )
        layout.addWidget( ok_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        
    @QtCore.pyqtSlot(int)
    def _validity_changed(self, row):
        
        def is_valid():
            return self._model.get_validator().isValid(0)
        
        post(is_valid, self._change_complete)
        
    def _change_complete(self, complete):
        self._complete = complete

class ChangeObject( ActionStep ):
    
    def __init__( self, obj, admin=None ):
        """
        Pop up a form for the user to change an object
        
        :param obj: the object to change
        :param admin: an instance of an admin class to use to edit the
            object, None if the default is to be taken
        """
        self._obj = obj
        self._admin = admin

    def gui_run( self, gui_context ):
        cls = self._obj.__class__
        admin = self._admin or gui_context.get_admin().get_related_admin( cls )
        dialog = ChangeObjectDialog( self._obj, admin )
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return self._obj
