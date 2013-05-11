#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Functions and classes to use a progress dialog in combination with
a model thread"""

import logging

from camelot.core.utils import ugettext
from camelot.view.art import Icon

from PyQt4 import QtGui, QtCore

LOGGER = logging.getLogger( 'camelot.view.controls.progress_dialog' )

class ProgressDialog(QtGui.QProgressDialog):
    """
A Progress Dialog to be used in combination with a post to the model thread:
    
to display a progress dialog until my_function has finished::

    d = ProgressDialog()
    post(my_function, d.finished, d.exception)
    d.exec_()
    
.. image:: /_static/controls/progress_dialog.png
    """

    progress_icon = Icon('tango/32x32/actions/appointment-new.png')
    
    def __init__(self, name, icon=progress_icon):
        QtGui.QProgressDialog.__init__( self, QtCore.QString(), QtCore.QString(), 0, 0 )
        label = QtGui.QLabel( unicode(name) )
        progress_bar = QtGui.QProgressBar()
        cancel_button = QtGui.QPushButton( ugettext('Cancel') )
        ok_button = QtGui.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        ok_button.clicked.connect( self.accept )
        ok_button.hide()
        self.setBar( progress_bar )
        self.setLabel( label )
        self.setCancelButton( cancel_button )
        self.setWindowTitle( ugettext('Please wait') )
        # use a list view to display details, for performance reasons,
        # since this widget will not freeze in case the list of details
        # becomes long
        details = QtGui.QListView( parent = self )
        details.setObjectName( 'details' )
        details.hide()
        layout = QtGui.QVBoxLayout()
        layout.addWidget( label )
        layout.addWidget( progress_bar )
        button_layout = QtGui.QHBoxLayout()
        button_layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        button_layout.addWidget( ok_button )
        button_layout.addWidget( cancel_button )
        button_layout.addStretch()
        layout.addLayout( button_layout )
        layout.addWidget( details )        
        self.setLayout( layout )
        # show immediately, to prevent a pop up before another window
        # opened in an action_step
        self.show() 
        #QtCore.QTimer.singleShot( 1000, self.show )
            
    def add_detail( self, text ):
        """Add detail text to the list of details in the progress dialog
        :param text: a string
        """
        details = self.findChild( QtGui.QListView, 'details' )
        if details != None:
            # a standarditem model is used, in the ideal case, the item
            # model with the real data should live in the model thread, and
            # this should only be a proxy
            if details.isHidden():
                details.show()
                model = QtGui.QStandardItemModel( parent = self )
                details.setModel( model )
            model = details.model()
            model.appendRow( QtGui.QStandardItem( text ) )
        
    def clear_details( self ):
        """Clear the detail text"""
        details = self.findChild( QtGui.QListView, 'details' )
        if details != None:
            details.model().clear()
            
    def set_ok_hidden( self, hidden = True ):
        ok_button = self.findChild( QtGui.QPushButton, 'ok' )
        if ok_button:
            ok_button.setHidden( hidden )
        
    @QtCore.pyqtSlot(bool)
    @QtCore.pyqtSlot()
    def finished(self, success=True):
        self.close()
        
    @QtCore.pyqtSlot(object)
    def exception(self, exception_info):
        from camelot.view.controls.exception import model_thread_exception_message_box
        model_thread_exception_message_box(exception_info)
        self.finished(False)
        
    @QtCore.pyqtSlot(object)
    def exit(self, return_code):
        """Stop the application event loop, with the given return code"""
        LOGGER.info( 'exit application with code %s'%return_code )
        QtGui.QApplication.exit( int( return_code ) ) 

class SplashProgress( QtGui.QSplashScreen ):
    """
    Wrapper around :class:`QtGui.QSplashScreen` to make it behave as if
    it were a progress dialog, this allows reuse of the progress related
    action steps within a splash screen.
    """
    # don't let splash screen stay on top, this might hinder
    # registration wizards or others that wait for user input
    # while camelot is starting up  
    
    def __init__( self, pixmap ):
        super( SplashProgress, self ).__init__( pixmap )
        # support transparency
        if pixmap.mask(): self.setMask(pixmap.mask()) 
        
    def setMaximum( self, _maximum ):
        pass
    
    def setValue( self, _value ):
        pass
    
    def setLabelText( self, text ):
        self.showMessage( text, QtCore.Qt.AlignTop, QtCore.Qt.white )
        
    def wasCanceled( self ):
        return False
        
    def clear_details( self ):
        pass
    
    def add_detail( self ):
        pass   
