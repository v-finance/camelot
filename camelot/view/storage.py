from camelot.view.controls.exception import model_thread_exception_message_box
from camelot.view.model_thread import post

from PyQt4 import QtGui, QtCore

class OpenFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(self, 'Open file', QtCore.QString(), 0, 0)
        self.setRange(0, 0)

    def open_path(self, path):
        url = QtCore.QUrl.fromLocalFile(path)
        QtGui.QDesktopServices.openUrl(url)
        self.close()

class SaveFileProgressDialog(QtGui.QProgressDialog):

    def __init__(self):
        QtGui.QProgressDialog.__init__(self, 'Save file', QtCore.QString(), 0, 0)
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
