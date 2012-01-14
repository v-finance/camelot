#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

"""Action steps to be used in the 
:class:`camelot.admin.action.application.Backup` and 
:class:`camelot.admin.action.application.Restore` action
"""

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import ugettext, variant_to_pyobject
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.art import Icon
import logging

logger = logging.getLogger('camelot.view.action_step.backup')

class LabelLineEdit( QtGui.QLineEdit ):
    
    _file_name = ''

    def __init__( self, storage, parent = None ):
        super(LabelLineEdit, self).__init__( parent )
        self.textChanged.connect( self._onTextChanged )
        self._storage = storage

    def _onTextChanged(self, text):
        if text == '':
            self._file_name = ''
        else:
            file_name = '%s.db'%text
            if self._storage.exists( file_name ):
                self._file_name = ''
            else:
                self._file_name = file_name

    def filename(self):
        return self._file_name

class LabelComboBox(QtGui.QComboBox):
    
    _file_name = ''

    def __init__(self, stored_files, parent = None):
        super( LabelComboBox, self ).__init__( parent )
        for i, stored_file in enumerate( stored_files):
            if i == 0:
                self._file_name = stored_file.name
            self.addItem( unicode( stored_file.verbose_name ), 
                          QtCore.QVariant( stored_file ) )            
        self.currentIndexChanged[int].connect(self._onCurrentIndexChanged)

    def _onCurrentIndexChanged( self, index ):
        self._file_name = variant_to_pyobject( self.itemData(index) ).name

    def filename( self ):
        return self._file_name

class SelectDialog( StandaloneWizardPage ):

    caption = _('Select file')
    extension = '.db'
    settings_key = 'custom_backup_filename'

    def __init__( self, title, default_storage, default_label, parent = None ):
        super(SelectDialog, self).__init__( title, 
                                            parent )
        self.default_storage = default_storage
        self.default_label = default_label
        self.storage = None
        self.label = None
        self.setup_widgets()
        # final touches - select the default radio button
        self._default_radio.setChecked( True )
        self.show_widgets( self._default_radio )
        self.complete_changed()

    def _setPath(self, dir):
        """Override this method in a subclass, to make the page do something"""
        raise NotImplementedError()
    
    def setup_widgets(self):
        # controls
        self._default_radio = QtGui.QRadioButton(ugettext('Default Location'))
        self._custom_radio = QtGui.QRadioButton(ugettext('Custom Location'))
        self._custom_edit = QtGui.QLineEdit()
        self._custom_button = QtGui.QPushButton(ugettext('Browse...'))
        button_group = QtGui.QButtonGroup(self)
        button_group.addButton(self._default_radio)
        button_group.addButton(self._custom_radio)

        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._default_radio)
        self._hlayout = QtGui.QHBoxLayout()
        layout.addLayout(self._hlayout)
        layout.addWidget(self._custom_radio)
        hlayout2 = QtGui.QHBoxLayout()
        hlayout2.addWidget(self._custom_edit)
        hlayout2.addWidget(self._custom_button)
        layout.addLayout(hlayout2)        
        self.main_widget().setLayout( layout )

        # connect signals to slots
        button_group.buttonClicked[QtGui.QAbstractButton].connect( self.show_widgets )
        button_group.buttonClicked[QtGui.QAbstractButton].connect( self.complete_changed )
        self._custom_button.clicked.connect(self._customButtonClicked)
        self._custom_edit.textChanged.connect(self.complete_changed)
        
        # buttons
        cancel_button = QtGui.QPushButton( ugettext('Cancel') )
        ok_button = QtGui.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        ok_button.setEnabled( False )
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )

    def show_widgets(self, selection):
        default_selected = self._isDefaultSelected(selection)
        self._custom_edit.setVisible(not default_selected)
        self._custom_button.setVisible(not default_selected)

    def _isDefaultSelected(self, selection):
        return (selection == self._default_radio)

    def _customButtonClicked(self):
        settings = QtCore.QSettings()
        previous_location = settings.value( self.settings_key ).toString()
        path = self._setPath( previous_location )
        if path:
            self._custom_edit.setText(QtCore.QDir.toNativeSeparators(path))
            settings.setValue( self.settings_key, path )

class SelectBackupDialog( SelectDialog ):    
    
    icon = Icon('tango/32x32/actions/document-save.png')

    def __init__( self, default_storage, default_label, parent = None ):
        super(SelectBackupDialog, self).__init__( ugettext('Select backup file'),
                                                  default_storage,
                                                  default_label,
                                                  parent )
        
        self.set_banner_logo_pixmap( self.icon.getQPixmap() )
        self.set_banner_title( ugettext('Select file') )
        self.set_banner_subtitle( ugettext('Please select a backup file. All data in this file will be overwritten.') )
        self.banner_widget().setStyleSheet('background-color: white;')
        
    def setup_widgets( self ):
        super( SelectBackupDialog, self ).setup_widgets()
        self._default_label = QtGui.QLabel( ugettext('Label:') )
        self._default_edit = LabelLineEdit( self.default_storage )
        self._default_label.setBuddy( self._default_edit )
        self._hlayout.addWidget( self._default_label )
        self._hlayout.addWidget( self._default_edit )
        self._default_edit.textChanged.connect( self._onDefaultEditChanged )
        self._default_edit.textChanged.connect( self.complete_changed )
        self._default_edit.setText( self.default_label )
        
    def _onDefaultEditChanged(self, text):
        if self._default_radio.isChecked():
            self.label = self._default_edit.filename()
    
    def show_widgets(self, selection):
        default_selected = self._isDefaultSelected( selection )
        self._default_label.setVisible( default_selected )
        self._default_edit.setVisible( default_selected )
        super( SelectBackupDialog, self ).show_widgets( selection )

    def complete_changed( self ):
        default_selected = self._default_radio.isChecked()
        if default_selected:
            self.storage = self.default_storage
            self.label = self._default_edit.filename()
        else:
            self.storage = None
            self.label = self._custom_edit.text()
        ok_button = self.findChild( QtGui.QPushButton, 'ok' )
        if ok_button:
            ok_button.setEnabled( self.label != '' )
            
    def _setPath(self, dir):
        path = QtGui.QFileDialog.getSaveFileName(
                self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
            )
        return path

class SelectRestoreDialog( SelectDialog ):
    
    icon = Icon('tango/32x32/devices/drive-harddisk.png')

    def __init__( self, default_storage, stored_files, parent = None ):
        self.stored_files = stored_files
        super( SelectRestoreDialog, self ).__init__( ugettext('Select restore file'),
                                                     default_storage,
                                                     None,
                                                     parent )
        self.set_banner_logo_pixmap( self.icon.getQPixmap() )
        self.set_banner_title( ugettext('Select file') )
        self.set_banner_subtitle( ugettext('Please select a backup file from which to restore the database. <br/>All data in the database will be overwritten with data from this file') )
        self.banner_widget().setStyleSheet('background-color: white;')
        if not len( stored_files ):
            self._default_radio.setEnabled( False )
            self._custom_radio.setChecked( True )
            self.show_widgets( self._custom_radio )

    def setup_widgets( self ):
        super( SelectRestoreDialog, self ).setup_widgets()
        self._default_combo = LabelComboBox( self.stored_files )
        self._default_combo.currentIndexChanged[int].connect( self.complete_changed )
        self._hlayout.addWidget( self._default_combo )

    def show_widgets( self, selection ):
        default_selected = self._isDefaultSelected( selection )
        self._default_combo.setVisible( default_selected )
        super( SelectRestoreDialog, self ).show_widgets( selection )

    def complete_changed( self ):
        default_selected = self._default_radio.isChecked()
        if default_selected:
            self.label = self._default_combo.filename()
            self.storage = self.default_storage
        else:
            self.label = self._custom_edit.text()
            self.storage = None
        ok_button = self.findChild( QtGui.QPushButton, 'ok' )
        if ok_button:
            ok_button.setEnabled( self.label != '' )

    def _setPath(self, dir):
        path = QtGui.QFileDialog.getOpenFileName(
            self, unicode(self.caption), dir, ugettext('Database files (*%s);;All files (*.*)' % self.extension),
        )
        return path

class SelectBackup( ActionStep ):
    
    def __init__( self, backup_mechanism ):
        locale = QtCore.QLocale()
        format = locale.dateTimeFormat(locale.ShortFormat)
        formatted_date_time = QtCore.QDateTime.currentDateTime().toString(format)
        # replace all non-ascii chars with underscores
        import string
        formatted_date_time_str = unicode(formatted_date_time)
        for c in formatted_date_time_str:
            if c not in string.ascii_letters and c not in string.digits:
                formatted_date_time_str = formatted_date_time_str.replace(c, '_')                
        filename_prefix = backup_mechanism.get_filename_prefix()
        self.default_label = '-'.join([filename_prefix, formatted_date_time_str])
        self.default_storage = backup_mechanism.get_default_storage()
        
    def render( self ):
        dialog = SelectBackupDialog( self.default_storage, self.default_label )
        return dialog
    
    def gui_run( self, gui_context ):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return ( dialog.label, dialog.storage )

class SelectRestore( SelectBackup ):
    
    def __init__( self, backup_mechanism ):
        self.default_storage = backup_mechanism.get_default_storage()
        self.stored_files = list( self.default_storage.list() )
        
    def render( self ):
        dialog = SelectRestoreDialog( self.default_storage, self.stored_files )
        return dialog

