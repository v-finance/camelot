#  ============================================================================
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
#  ============================================================================

"""Wizard and wizard pages to assist in the creation of new objects"""

from PyQt4 import QtGui, QtCore

class SelectSubclassPage(QtGui.QWizardPage):
    """Page for a wizard that allows the selection of a subclass"""

    def __init__(self, parent, admin):
        super(SelectSubclassPage, self).__init__(parent)
        from camelot.view.controls.inheritance import SubclassTree
#    self.setTitle('Dossiers to synchronize')
#    self.setSubTitle('Either synchronize all dossiers in the selected cabinets (more complete), or select a single dossier (faster).')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(SubclassTree(admin, self))
        layout.addStretch(1)
        self.setLayout(layout)

class NewObjectWizard(QtGui.QWizard):

    def __init__(self, parent, admin):
        super(NewObjectWizard, self).__init__(parent)
        self.addPage(SelectSubclassPage(self, admin))
