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

from camelot.core.utils import ugettext_lazy as _
from camelot.view.wizard.pages.backup_page import SelectBackupFilePage, SelectRestoreFilePage
from camelot.view.wizard.pages.progress_page import ProgressPage

class BackupPage(ProgressPage):
    title = _('Backup in progress')
    
    def __init__(self, backup_mechanism, parent=None):
        super(BackupPage, self).__init__(parent)
        self._backup_mechanism = backup_mechanism
        self.setFinalPage ( True )

    def run(self):
        backup_mechanism = self._backup_mechanism(self.wizard().filename, 
                                                  self.wizard().storage)
        for completed, total, description in backup_mechanism.backup():
            self.update_maximum_signal.emit( total )
            self.update_progress_signal.emit( completed, description )

class BackupWizard(QtGui.QWizard):
    """Wizard to perform a backup using a BackupMechanism"""
    
    window_title = _('Backup')
    select_backup_file_page = SelectBackupFilePage
    backup_page = BackupPage

    def __init__(self, backup_mechanism, parent=None):
        super(BackupWizard, self).__init__(parent)
        self.storage = backup_mechanism.get_default_storage()
        self.setWindowTitle( unicode(self.window_title) )
        self.addPage(self.select_backup_file_page(backup_mechanism))
        self.addPage(self.backup_page(backup_mechanism))
        
class RestorePage(ProgressPage):
    
    title = _('Restore in progress')
    
    def __init__(self, backup_mechanism, parent=None):
        super(RestorePage, self).__init__(parent)
        self._backup_mechanism = backup_mechanism
        self.setFinalPage ( True )
        
    def run(self):
        backup_mechanism = self._backup_mechanism(self.wizard().filename, 
                                                  self.wizard().storage)
        for completed, total, description in backup_mechanism.restore():
            self.update_maximum_signal.emit( total )
            self.update_progress_signal.emit( completed, description )
            
class RestoreWizard(QtGui.QWizard):
    """Wizard to perform a restore using a BackupMechanism"""
    
    window_title = _('Restore')
    select_restore_file_page = SelectRestoreFilePage
    restore_page = RestorePage

    def __init__(self, backup_mechanism, parent=None):
        super(RestoreWizard, self).__init__(parent)
        self.storage = backup_mechanism.get_default_storage()
        self.setWindowTitle( unicode(self.window_title) )
        self.addPage(self.select_restore_file_page(backup_mechanism))
        self.addPage(self.restore_page(backup_mechanism))


