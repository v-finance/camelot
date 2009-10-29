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

"""Module for managing imports"""

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('camelot.view.wizard.importwizard')

from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui
from camelot.view.art import Pixmap
from camelot.view.wizard.utils import *

_ = lambda x: x


class ImportWizard(QtGui.QWizard):
    """ImportWizard provides a two-step wizard for importing csv data"""

    def __init__(self, admin=None, parent=None):
        """:param admin: camelot model admin"""
        super(ImportWizard, self).__init__(parent)

        self.admin = admin

        self.addPage(SelectFilePage())
        self.addPage(PreviewTablePage())

        self.setWindowTitle(_('Import Data'))


class SelectFilePage(QtGui.QWizardPage):
    """SelectFilePage is the file selection page of the import wizard"""

    def __init__(self, parent=None):
        super(SelectFilePage, self).__init__(parent)
        self.setTitle(_('Import data from a file'))
        msg = "To import data, click 'Browse' to " \
              "select a file then click 'Import'."
        self.setSubTitle(_(msg))

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

        self.connect(browsebutton,
                     QtCore.SIGNAL('clicked()'),
                     lambda: self.setpath())

    def setpath(self):
        caption = _('Import Wizard - Set File Path')
        dir = self.field('datasource').toString()
        path = QtGui.QFileDialog.getOpenFileName(self, caption, dir)
        if path:
            self.filelineedit.setText(QtCore.QDir.toNativeSeparators(path))


class PreviewTable(QtGui.QTableView):
    """PreviewTable subclasses QTableView and displays preview data"""

    def __init__(self, parent=None):
        super(PreviewTable, self).__init__(parent)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.oldgate = None
        self.datamodel = None
        self.nolabels = True

    def enable_drops(self, enable):
        """Shows and hide dropdown label selectors in first row"""
        if self.datamodel is None: return

        if not enable:
            self.setItemDelegateForRow(0, self.oldgate)
            self.nolabels = True
            return

        from camelot.view.controls.delegates.comboboxdelegate \
            import ComboBoxDelegate
        
        labels = tuple((unicode(label), unicode(label)) \
                       for _, label in columns_iter(self.datamodel, 0))

        delegate = ComboBoxDelegate(choices=labels, parent=self)
        self.oldgate = self.itemDelegateForRow(0)
        self.setItemDelegateForRow(0, delegate)
        
        self.nolabels = False

    def are_drops_synced(self):
        """Returns true if no two columns have the same label"""
        if self.datamodel is None: return False
        
        if self.nolabels: return True

        labels = [label for _, label in columns_iter(self.datamodel, 0)]
        return len(set(labels)) == len(labels)

    def rows(self):
        """Returns an iterator over the rows of data"""
        if self.datamodel is None: return []

        if self.nolabels:
            iter = rows_iter(self.datamodel)
        else:
            labels = [label for _, label in columns_iter(self.datamodel, 0)]
            iter = labeled_rows_iter(self.datamodel, labels)

        return iter

    def feed(self, data=None):
        """Feeds model with imported data"""

        # premature optimization is evil :)
        from PyQt4.QtCore import QModelIndex, QVariant

        if data:
            nrows = len(data)
            ncols = len(data[0])
            self.datamodel = QtGui.QStandardItemModel(nrows, ncols)
            self.setModel(self.datamodel)

            for row in range(nrows):
                for col in range(ncols):
                    idx = self.datamodel.index(row, col, QModelIndex())
                    val = QVariant(data[row][col])
                    self.datamodel.setData(idx, val)


class PreviewTablePage(QtGui.QWizardPage):
    """PreviewTablePage is the previewing page of the import wizard"""

    def __init__(self, parent=None):
        super(PreviewTablePage, self).__init__(parent)

        self.setTitle(_('Data Preview'))
        msg = 'Below is a preview of the data being imported.'
        self.setSubTitle(_(msg))

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        self.setButtonText(QtGui.QWizard.FinishButton, _('Import'))

        self.previewtable = PreviewTable()

        cb = QtGui.QCheckBox(_('Use first row as labels selector'))
        self.connect(cb,
                     QtCore.SIGNAL('stateChanged(int)'),
                     lambda checked: self.previewtable.enable_drops(checked))

        ly = QtGui.QVBoxLayout()
        ly.addWidget(cb)
        ly.addWidget(self.previewtable)
        self.setLayout(ly)

    def initializePage(self):
        """Gets all info needed from SelectFilePage and feeds table"""
        source = self.field('datasource').toString()
        self.previewtable.feed(import_csv_data(source))

    def validatePage(self):
        """Called when the button labelled "import" is clicked"""
        if not self.previewtable.are_drops_synced():
            from PyQt4.QtGui import QMessageBox
            QMessageBox.critical(self,
                                 _('Duplicate labels'),
                                 _('Please check duplicate labels'))
            return False

        dia = QtGui.QDialog()
        log = QtGui.QTextBrowser()
        log.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        ly = QtGui.QVBoxLayout()
        ly.addWidget(log)
        dia.setLayout(ly)

        for r in self.previewtable.rows():
            log.append(unicode(r))

        dia.exec_()

        return True


def test_wizard(wizardclass, attrs={}):
    import sys
    from camelot.view.art import Icon
    app = QtGui.QApplication(sys.argv)

    from camelot.view.model_thread import get_model_thread, \
                                          construct_model_thread
    from camelot.view.remote_signals import construct_signal_handler

    construct_model_thread()
    construct_signal_handler()
    get_model_thread().start()

    try:
        ad = attrs.get('admin', None)
        pa = attrs.get('parent', None)
        wizard = wizardclass(admin=ad, parent=pa)
    except AttributeError:
        wizard = wizardclass()

    app.setWindowIcon(Icon('tango/32x32/apps/system-users.png').getQIcon())
    app.connect(wizard,
                QtCore.SIGNAL('accepted()'),
                lambda: sys.stdout.write('accepted\n'))
    app.connect(wizard,
                QtCore.SIGNAL('finished(int)'),
                lambda ret: \
                    sys.stdout.write('finished with return value %d\n' % ret))
    sys.exit(wizard.exec_())


if __name__ == '__main__':
    test_wizard(ImportWizard)
