from camelot.view.controls.exception import model_thread_exception_message_box
from camelot.view.model_thread import post
from camelot.core.utils import ugettext as _

from PyQt4 import QtGui, QtCore

class OpenFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(self, _('Please wait'), QtCore.QString(), 0, 0)
        self.setWindowTitle(_('Open file'))
        self.setRange(0, 0)

    def open_path(self, path):
        import os
        if not os.path.exists(path):
            QtGui.QMessageBox.critical (self, _('Could not open file'), _('%s does not exist')%path)
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
        QtGui.QProgressDialog.__init__(self, _('Please wait'), QtCore.QString(), 0, 0)
        self.setWindowTitle(_('Save file'))
        self.setRange(0, 0)

    def finish(self, on_finish):
        on_finish()
        self.close()

def open_stored_file(parent, stored_file):
    """Open the stored file with the default system editor for this file type"""

    progress = OpenFileProgressDialog()

    def get_path():
        return stored_file.storage.checkout(stored_file)

    post(get_path, progress.open_path, model_thread_exception_message_box)
    progress.exec_()

def create_stored_file(parent, storage, on_finish, filter="""All files (*)"""):
    """Popup a QFileDialog, put the selected file in the storage and return the
    call on_finish with the StoredFile when done"""
    filename = QtGui.QFileDialog.getOpenFileName(parent, 'Open file',
                                                 QtCore.QDir.currentPath(),
                                                 filter)
    if filename:
        progress = SaveFileProgressDialog()

        def checkin():
            new_path = storage.checkin(str(filename))
            return lambda:on_finish(new_path)

        post(checkin, progress.finish, model_thread_exception_message_box)
        progress.exec_()
