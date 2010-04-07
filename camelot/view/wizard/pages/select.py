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


import os.path

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QDesktopServices

from camelot.view.art import Pixmap
from camelot.core.utils import ugettext as _


class SelectFilePage(QtGui.QWizardPage):
    """SelectFilePage is the file selection page of an import wizard"""

    def __init__(self, parent=None):
        super(SelectFilePage, self).__init__(parent)
        self.setTitle(_('Import data from a file'))
        self.setSubTitle(_(
            "To import data, click 'Browse' to "
            "select a file then click 'Import'."
        ))

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        label = QtGui.QLabel(_('Select file:'))
        self.filelineedit = QtGui.QLineEdit()
        label.setBuddy(self.filelineedit)
        browsebutton = QtGui.QPushButton(_('Browse...'))

        # file path is a mandatory field
        self.registerField('datasource*', self.filelineedit)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self.filelineedit)
        hlayout.addWidget(browsebutton)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        self.connect(
            browsebutton,
            QtCore.SIGNAL('clicked()'),
            lambda: self.setpath()
        )

    def setpath(self):
        caption = _('Import Wizard - Set File Path')
        settings = QtCore.QSettings()
        dir = settings.value('datasource').toString()
        #if not os.path.exists(dir)
        #    dir = QDesktopServices.displayName(QDesktopServices.DocumentsLocation)
        path = QtGui.QFileDialog.getOpenFileName(self, caption, dir)
        if path:
            self.filelineedit.setText(QtCore.QDir.toNativeSeparators(path))
            settings.setValue('datasource', QtCore.QVariant(path))
