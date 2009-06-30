from camelot.view.controls.exception import model_thread_exception_message_box

def open_stored_file(parent, stored_file):
  """Open the stored file with the default system editor for this file type"""
  from PyQt4 import QtGui, QtCore
  from camelot.view.model_thread import get_model_thread
  model_thread = get_model_thread()
  progress = QtGui.QProgressDialog('Open file', QtCore.QString(), 0, 0)
  progress.setRange(0, 0)
    
  def get_path():
    return stored_file.storage.checkout(stored_file)
      
  def open_path(path):
    url = QtCore.QUrl.fromLocalFile(path)
    QtGui.QDesktopServices.openUrl(url)
    progress.close()
    
  model_thread.post(get_path, open_path, model_thread_exception_message_box)
  
def create_stored_file(parent, storage, on_finish):
  """Popup a QFileDialog, put the selected file in the storage and return the
  call on_finish with the StoredFile when done"""
  from PyQt4 import QtGui, QtCore
  from camelot.view.model_thread import get_model_thread
  filename = QtGui.QFileDialog.getOpenFileName(parent, 'Open file', 
                                               QtCore.QDir.currentPath())
  if filename:
    model_thread = get_model_thread()
    progress = QtGui.QProgressDialog('Save file', QtCore.QString(), 0, 0)
    progress.setRange(0, 0)
    
    def checkin():
      return storage.checkin(str(filename))
          
    def finish(stored_file):
      progress.close()
      on_finish(stored_file)
      
    model_thread.post(checkin, finish, model_thread_exception_message_box)
