#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from camelot.view.model_thread import post
from camelot.core.utils import ugettext as _
from camelot.view.controls.exception import model_thread_exception_message_box

from PyQt4 import QtGui
from PyQt4 import QtCore

class OpenFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(
            self, _('Please wait'), QtCore.QString(), 0, 0
        )
        self.setWindowTitle(_('Open file'))
        self.setRange(0, 0)

    def open_path(self, path):
        import os
        if not os.path.exists(path):
            QtGui.QMessageBox.critical(
                self,
                _('Could not open file'),
                _('%s does not exist') % path,
            )
        #
        # support for windows shares
        #
        if not path.startswith(r'\\'):
            url = QtCore.QUrl.fromLocalFile(path)
        else:
            url = QtCore.QUrl(path, QtCore.QUrl.TolerantMode)
        QtGui.QDesktopServices.openUrl(url)
        self.close()


class SaveFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(
            self, _('Please wait'), QtCore.QString(), 0, 0
        )
        self.setWindowTitle(_('Save file'))
        self.setRange(0, 0)

    def finish(self, on_finish):
        on_finish()
        self.close()


def open_stored_file(parent, stored_file):
    """Open the stored file with the default system editor for
    this file type"""

    progress = OpenFileProgressDialog()

    def get_path():
        return stored_file.storage.checkout(stored_file)

    post(get_path, progress.open_path, model_thread_exception_message_box)
    progress.exec_()


def create_stored_file(parent, storage, on_finish, filter='All files (*)'):
    """Popup a QFileDialog, put the selected file in the storage and
    return the call on_finish with the StoredFile when done"""
    settings = QtCore.QSettings()
    dir = settings.value('lastpath').toString()
    # use last path saved in settings, if none current dir is used by Qt
    filename = QtGui.QFileDialog.getOpenFileName(
        parent, 'Open file', dir, filter
    )
    if filename:
        # save it back
        settings.setValue('lastpath', QtCore.QVariant(filename))
        progress = SaveFileProgressDialog()

        def checkin():
            new_path = storage.checkin(unicode(filename))
            return lambda:on_finish(new_path)

        post(checkin, progress.finish, model_thread_exception_message_box)
        progress.exec_()
