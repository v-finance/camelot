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

import os
import logging

from camelot.view.model_thread import post
from camelot.core.utils import ugettext as _
from camelot.view.controls.exception import model_thread_exception_message_box

from PyQt4 import QtGui
from PyQt4 import QtCore

LOGGER = logging.getLogger('camelot.view.storage')

class OpenFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(
            self, _('Please wait'), QtCore.QString(), 0, 0
        )
        self.setWindowTitle(_('Open file'))
        self.setRange(0, 0)

    def open_path(self, path):
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

    def file_stored(self):
        """Called when the file has been stored at path"""
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

def save_stored_file(parent, stored_file):
    """Save a stored file as another file"""
    settings = QtCore.QSettings()
    default_dir = settings.value('datasource').toString()
    proposal = os.path.join(unicode(default_dir), unicode(stored_file.verbose_name) )

    path = QtGui.QFileDialog.getSaveFileName(
        parent, _('Save as'), proposal
    )

    if path:
        progress = OpenFileProgressDialog()

        def save_as():
            destination = open(path, 'wb')
            destination.write( stored_file.storage.checkout_stream(stored_file).read() )

        post(save_as, progress.file_stored, model_thread_exception_message_box)
        progress.exec_()

def create_stored_file(parent, storage, on_finish, filter='All files (*)',
                       remove_original = False,
                       filename = None):
    """Popup a QFileDialog, put the selected file in the storage and
    return the call on_finish with the StoredFile when done
    
    :param on_finish: function that will be called in the gui thread when
    the file is stored.  the first argument of the function should be the
    StoredFile
    
    :param filename: if None, a dialog will pop up, asking the user for
    the file, otherwise a string with the name of the file to be stored
    """
    settings = QtCore.QSettings()
    dir = settings.value('lastpath').toString()
    # use last path saved in settings, if none current dir is used by Qt
    if filename == None:
        filename = QtGui.QFileDialog.getOpenFileName(
            parent, 'Open file', dir, filter
        )
    if filename:
        filename = unicode( filename )
        remove = False
        if remove_original:
            reply = QtGui.QMessageBox(
                QtGui.QMessageBox.Warning,
                _('The file will be stored.'),
                _('Do you want to remove the original file?'),
                QtGui.QMessageBox.No | QtGui.QMessageBox.Yes,
            )
            reply.setDefaultButton(QtGui.QMessageBox.Yes)
            reply.exec_()
            if reply == QtGui.QMessageBox.Yes:
                remove = True
        # save it back
        settings.setValue('lastpath', QtCore.QVariant( os.path.dirname( filename ) ) )
        progress = SaveFileProgressDialog()

        def checkin():
            new_path = storage.checkin( filename )
            if remove:
                try:
                    os.remove( filename )
                except Exception, e:
                    LOGGER.warn('could not remove file', exc_info=e)
            return lambda:on_finish(new_path)

        post(checkin, progress.finish, model_thread_exception_message_box)
        progress.exec_()

