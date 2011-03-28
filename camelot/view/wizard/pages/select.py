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

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.art import Icon
from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext


class SelectFilePage(QtGui.QWizardPage):
    """SelectFilePage is the file selection page of an import wizard"""

    title = _('Import data from a file')
    sub_title = _(
        "To import data, click 'Browse' to select a file then click 'Next'."
    )
    icon = Icon('tango/32x32/mimetypes/x-office-spreadsheet.png')
    caption = _('Select file')
    save = False

    def __init__(self, parent=None):
        super(SelectFilePage, self).__init__(parent)
        self.setTitle( unicode(self.title) )
        self.setSubTitle( unicode(self.sub_title) )
        self.setPixmap(QtGui.QWizard.LogoPixmap, self.icon.getQPixmap())

        label = QtGui.QLabel(ugettext('Select file:'))
        self.filelineedit = QtGui.QLineEdit()
        label.setBuddy(self.filelineedit)
        browsebutton = QtGui.QPushButton(ugettext('Browse...'))

        # file path is a mandatory field
        self.registerField('datasource*', self.filelineedit)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self.filelineedit)
        hlayout.addWidget(browsebutton)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        browsebutton.clicked.connect( self.setpath )

    @QtCore.pyqtSlot()
    def setpath(self):
        settings = QtCore.QSettings()
        dir = settings.value('datasource').toString()
        #if not os.path.exists(dir)
        #    dir = QDesktopServices.displayName(
        #    QDesktopServices.DocumentsLocation
        #)
        if self.save:
            path = QtGui.QFileDialog.getSaveFileName(
                self, unicode(self.caption), dir
            )
        else:
            path = QtGui.QFileDialog.getOpenFileName(
                self, unicode(self.caption), dir
            )
        if path:
            self.filelineedit.setText(QtCore.QDir.toNativeSeparators(path))
            settings.setValue('datasource', QtCore.QVariant(path))


