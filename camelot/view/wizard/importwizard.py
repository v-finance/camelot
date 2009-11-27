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
from PyQt4.QtGui import QColor

from camelot.view.controls.editors.one2manyeditor import One2ManyEditor
from camelot.core.utils import ugettext as _
from camelot.view.art import Pixmap
from camelot.view.wizard.utils import *

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

class RowData(object):
    """Class representing the data in a single row of the imported file as an
    object with attributes column_1, column_2, ..., each representing the data
    in a single column of that row"""

    def __init__(self, row_number, row_data):
        """:param row_data: a list containing the data [column_1_data,
        column_2_data, ...] for a single row
        """
        self.id = row_number + 1
        for i, data in enumerate(row_data):
            self.__setattr__('column_%i'%i, data)

class RowDataAdminDecorator(object):
    """Decorator that transforms the Admin of the class to be imported to an
    Admin of the RowData objects to be used when previewing and validating the
    data to be imported"""

    def __init__(self, object_admin):
        """:param object_admin: the object_admin object that will be
        decorated"""
        self._object_admin = object_admin

    def __getattr__(self, attr):
        return getattr(self._object_admin, attr)

    def get_columns(self):
        original_columns = self._object_admin.get_columns()

        def new_field_attributes(i, original_field_attributes, original_field):
            from camelot.view.controls import delegates
            attributes = dict(original_field_attributes)
            attributes['delegate'] = delegates.PlainTextDelegate
            attributes['python_type'] = str
            attributes['original_field'] = original_field

            if 'from_string' in attributes:

                def get_background_color(o):
                    """If the string is not convertible with from_string, or the result
                    is None when a value is required, set the background to pink"""
                    value = getattr(o, 'column_%i'%i)
                    if not value and (attributes['nullable']==False):
                        return QColor('Pink')
                    try:
                        value = attributes['from_string'](value)
                        return None
                    except:
                        return QColor('Pink')

                attributes['background_color'] = get_background_color

            return attributes

        new_columns = [
            ('column_%i'%i, new_field_attributes(i, attributes, original_field))
            for i, (original_field, attributes) in enumerate(original_columns)
        ]

        return new_columns


class DataPreviewPage(QtGui.QWizardPage):
    """DataPreviewPage is the previewing page for the import wizard"""

    def __init__(self, parent=None, model=None, collection_getter=None):
        super(DataPreviewPage, self).__init__(parent)
        assert model
        assert collection_getter
        self.setTitle(_('Data Preview'))
        msg = 'Please review the data below.'
        self.setSubTitle(_(msg))
        self.model = model
        self.collection_getter = collection_getter

        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())

        self.setButtonText(QtGui.QWizard.NextButton, _('Import'))
        self.previewtable = One2ManyEditor(admin=model.get_admin(), parent=self, create_inline=True)

        ly = QtGui.QVBoxLayout()
        ly.addWidget(self.previewtable)
        self.setLayout(ly)

    def initializePage(self):
        """Gets all info needed from SelectFilePage and feeds table"""
        filename = self.field('datasource').toString()
        self.model.set_collection_getter( self.collection_getter(filename) )
        self.previewtable.set_value(self.model)
        self.emit(QtCore.SIGNAL('completeChanged()'))

    def isComplete(self):
        return True

class FinalPage(QtGui.QWizardPage):
    """FinalPage is the final page in the import process"""

    def __init__(self, parent=None, model=None):
        super(FinalPage, self).__init__(parent)
        self.setTitle(_('Import Progress'))
        self.model = model
        self.admin = model.get_admin()
        msg = 'Please wait while data is being imported.'
        self.setSubTitle(_(msg))
        
        icon = 'tango/32x32/mimetypes/x-office-spreadsheet.png'
        self.setPixmap(QtGui.QWizard.LogoPixmap, Pixmap(icon).getQPixmap())
        self.setButtonText(QtGui.QWizard.FinishButton, _('Close'))
        self.progressbar = QtGui.QProgressBar()

        label = QtGui.QLabel(_(
            'The data will be ready when the progress reaches 100%. '
            'The import can be cancelled at any time.'
        ))
        label.setWordWrap(True)

        ly = QtGui.QVBoxLayout()
        ly.addWidget(label)
        ly.addWidget(self.progressbar)
        self.setLayout(ly)
        
    def run_import(self):
        for row in self.model.get_collection_getter()():
            new_entity_instance = self.admin.entity()
            for field_name, attributes in self.admin.get_columns():
                setattr( new_entity_instance,
                         attributes['original_field'],
                         attributes['from_string'](getattr(row, field_name)) )
            self.admin.add(new_entity_instance)
            self.admin.flush(new_entity_instance)
        
    def import_finished(self):
        self.progressbar.setMaximum(1)
        self.progressbar.setValue(1)
        self.emit(QtCore.SIGNAL('completeChanged()'))
    
    def isComplete(self):
        return self.progressbar.value() == self.progressbar.maximum()
            
    def initializePage(self):
        from camelot.view.model_thread import post
        self.progressbar.setMaximum(0)
        self.progressbar.setValue(0)        
        post(self.run_import, self.import_finished, self.import_finished)
        
class ImportWizard(QtGui.QWizard):
    """ImportWizard provides a two-step wizard for importing data as objects into Camelot.  To create a
    custom wizard, subclass this ImportWizard and overwrite its class attributes.
    
    To import different file formats, you probably need a custom collection_getter for this file type.
    """
    
    select_file_page = SelectFilePage
    data_preview_page = DataPreviewPage
    final_page = FinalPage
    collection_getter = None
    window_title = 'Import CSV data'
    
    def __init__(self, parent=None, admin=None):
        """:param admin: camelot model admin"""
        from camelot.view.proxy.collection_proxy import CollectionProxy
        super(ImportWizard, self).__init__(parent)
        assert admin

        row_data_admin = RowDataAdminDecorator(admin)
        model = CollectionProxy(
            row_data_admin,
            lambda:[],
            row_data_admin.get_columns
        )  
        
        self.addPage(SelectFilePage(parent=self))
        self.addPage(DataPreviewPage(parent=self, model=model, collection_getter=self.collection_getter))
        self.addPage(FinalPage(parent=self, model=model))
        self.setWindowTitle(_(self.window_title))
