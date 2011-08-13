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
    
    update_progress_signal = QtCore.pyqtSignal(int, str)
    update_maximum_signal = QtCore.pyqtSignal(int)
    
    title = _('Action in progress')
    sub_title = _('Please wait for completion')
    
    def __init__(self, parent=None):
        super(ProgressPage, self).__init__( parent )
        self.update_progress_signal.connect( self.update_progress )
        self.update_maximum_signal.connect( self.update_maximum )
        self._complete = False
        self.setTitle(unicode(self.title))
        self.setSubTitle(unicode(self.sub_title))
        layout = QtGui.QVBoxLayout()
        progress = QtGui.QProgressBar(self)
        progress.setObjectName('progress')
        progress.setMinimum(0)
        progress.setMaximum(1)
        label = QtGui.QTextEdit(self)
        label.setObjectName('label')
        label.setSizePolicy( QtGui.QSizePolicy.Expanding,
                             QtGui.QSizePolicy.Expanding )
        label.setReadOnly(True)
        layout.addWidget(progress)
        layout.addWidget(label)
        self.setLayout(layout)
    
    def isComplete(self):
        return self._complete
    
    @QtCore.pyqtSlot(int)
    def update_maximum(self, maximum):
        progress = self.findChild(QtGui.QWidget, 'progress' )
        if progress:
            progress.setMaximum(maximum)
    
    @QtCore.pyqtSlot(int, str)
    def update_progress(self, value, label):
        progress_widget = self.findChild(QtGui.QWidget, 'progress' )
        if progress_widget:
            progress_widget.setValue(value)
        label_widget = self.findChild(QtGui.QWidget, 'label' )
        if label_widget:            
            label_widget.setHtml(unicode(label))

    def exception(self, args):
        self.finished()
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box(args)
        
    def finished(self):
        self._complete = True
        progress_widget = self.findChild(QtGui.QWidget, 'progress' )
        if progress_widget:
            progress_widget.setMaximum(1)
            progress_widget.setValue(1)
        self.completeChanged.emit()     
        
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
