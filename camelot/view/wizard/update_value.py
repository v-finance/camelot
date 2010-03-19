#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================

"""A wizard to update a field on a collection of objects"""

from PyQt4 import QtGui

from camelot.view.controls.editors import ChoicesEditor
from camelot.core.utils import ugettext_lazy as _

class SelectValuePage(QtGui.QWizardPage):
    """Page to select a value to update"""

    sub_title = _('Select the field to update and enter its new value')
    
    def __init__(self, parent=None):
        super(SelectValuePage, self).__init__(parent)
        self.setSubTitle( unicode(self.sub_title) )

        self.editor = ChoicesEditor()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)

class UpdateValueWizard(QtGui.QWizard):
    """This wizard presents the user with a selection of the possible fields to
    update and a new value.  Then this field is changed for all objects in a given
    collection"""

    select_value_page = SelectValuePage
    
    window_title = _('Update value')

    def __init__(self, parent=None, admin=None):
        """:param admin: camelot model admin"""
        super(UpdateValueWizard, self).__init__(parent)
        assert admin
        self.addPage(SelectValuePage(parent=self))