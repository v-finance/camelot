'''
Created on Jan 7, 2010

@author: tw55413
'''

from PyQt4 import QtCore, QtGui

from camelot.core.utils import ugettext_lazy as _


class ProgressPage(QtGui.QWizardPage):
    """Generic progress page for a wizard.
    
    Subclass and reimplement the run method.  And within this run method,
    regulary emit the update_progress_signal and the update_maximum_signal.
    
    the update_maximum_signal should have as its single argument an integer
    value indicating the maximum of the progress bar.
    
    the update_progress_signal should two arguments, the first is an integer
    indicating the current position of the progress bar, and the second is
    a string telling the user what is going on.
    
    If required, set the title and sub_title class attribute to change the
    text displayed to the user.
    """
    
    update_progress_signal = QtCore.SIGNAL('update_progress')
    update_maximum_signal = QtCore.SIGNAL('update_maximum')
    
    title = _('Action in progress')
    sub_title = _('Please wait for completion')
    
    def __init__(self, parent):
        super(ProgressPage, self).__init__( parent )
        self.connect(self, self.update_progress_signal, self.update_progress)
        self.connect(self, self.update_maximum_signal, self.update_maximum)
        self._complete = False
        self.setTitle(unicode(self.title))
        self.setSubTitle(unicode(self.sub_title))
        layout = QtGui.QVBoxLayout()
        self.progress = QtGui.QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(1)
        self.label = QtGui.QTextEdit(self)
        self.label.setReadOnly(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.label)
        layout.addStretch(1)
        self.setLayout(layout)
        self._wizard = parent
    
    def isComplete(self):
        return self._complete
    
    def update_maximum(self, maximum):
        self.progress.setMaximum(maximum)
    
    def update_progress(self, value, label):
        self.progress.setValue(value)
        self.label.setHtml(unicode(label))

    def exception(self, args):
        self.finished()
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box(args)
        
    def finished(self):
        self._complete = True
        self.progress.setMaximum(1)
        self.progress.setValue(1)
        self.emit(QtCore.SIGNAL('completeChanged()'))        
        
    def run(self):
        """
        This method contains the actual action, that will be run in the model thread.
        
        Reimplement this method, while regulary emiting update_progress_signal and
        update_maximum_signal to keep the progress bar moving.
        """
        pass
                      
    def initializePage(self):
        from camelot.view.model_thread import post
        post(self.run, self.finished, self.exception)
