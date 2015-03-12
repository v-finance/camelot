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

import six

from ...core.qt import QtGui, QtCore, QtWidgets, Qt, q_string, py_to_variant

LOGGER = logging.getLogger( 'camelot.view.controls.progress_dialog' )

class ProgressDialog(QtWidgets.QProgressDialog):
    """
A Progress Dialog, used during the :meth:`gui_run` of an action.

.. image:: /_static/controls/progress_dialog.png
    """

    progress_icon = Icon('tango/32x32/actions/appointment-new.png')

    def __init__(self, name, icon=progress_icon):
        QtWidgets.QProgressDialog.__init__( self, q_string(u''), q_string(u''), 0, 0 )
        label = QtWidgets.QLabel( six.text_type(name) )
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setObjectName('progress_bar')
        cancel_button = QtWidgets.QPushButton( ugettext('Cancel') )
        cancel_button.setObjectName( 'cancel' )
        ok_button = QtWidgets.QPushButton( ugettext('OK') )
        ok_button.setObjectName( 'ok' )
        ok_button.clicked.connect( self.accept )
        ok_button.hide()
        copy_button = QtWidgets.QPushButton( ugettext('Copy') )
        copy_button.setObjectName( 'copy' )
        copy_button.clicked.connect( self.copy_clicked )
        copy_button.hide()
        copy_button.setToolTip(ugettext('Copy details to clipboard'))
        self.setBar( progress_bar )
        self.setLabel( label )
        self.setCancelButton( cancel_button )
        self.setWindowTitle( ugettext('Please wait') )
        # use a list view to display details, for performance reasons,
        # since this widget will not freeze in case the list of details
        # becomes long
        details = QtWidgets.QListView( parent = self )
        details.setObjectName( 'details' )
        details.hide()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( label )
        layout.addWidget( progress_bar )
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setDirection( QtWidgets.QBoxLayout.RightToLeft )
        button_layout.addWidget( ok_button )
        button_layout.addWidget( cancel_button )
        button_layout.addWidget( copy_button )
        button_layout.addStretch()
        layout.addWidget( details )
        layout.addLayout( button_layout )
        self.setLayout( layout )
        # show immediately, to prevent a pop up before another window
        # opened in an action_step
        self.show() 
        #QtCore.QTimer.singleShot( 1000, self.show )

    # This method is overwritten,to undo the overwrite of this method
    # in QProgressDialog, as the QProgressDialog then manually relayouts
    # the dialog instead of using the normal layouts
    def resizeEvent(self, event):
        return QtWidgets.QWidget.resizeEvent(self, event)

    @QtCore.qt_slot(bool)
    def copy_clicked(self, checked):
        details = self.findChild( QtWidgets.QListView, 'details' )
        if details is None:
            return
        model = details.model()
        if model is not None:
            text = u'\n'.join([six.text_type(s) for s in model.stringList()])
            QtWidgets.QApplication.clipboard().setText(text)

    def add_detail( self, text ):
        """Add detail text to the list of details in the progress dialog
        :param text: a string
        """
        details = self.findChild( QtWidgets.ListView, 'details' )
        copy_button = self.findChild( QtWidgets.QPushButton, 'copy' )
        if copy_button is not None:
            copy_button.show()
        if details is not None:
            # a standarditem model is used, in the ideal case, the item
            # model with the real data should live in the model thread, and
            # this should only be a proxy
            if details.isHidden():
                details.show()
                model = QtGui.QStringListModel( parent = self )
                details.setModel( model )
            model = details.model()
            model.insertRow(model.rowCount())
            model.setData(model.index(model.rowCount()-1, 0),
                          py_to_variant(text),
                          Qt.DisplayRole)

    def clear_details( self ):
        """Clear the detail text"""
        details = self.findChild( QtWidgets.QListView, 'details' )
        if details != None:
            details.model().clear()

    def set_ok_hidden( self, hidden = True ):
        ok_button = self.findChild( QtWidgets.QPushButton, 'ok' )
        progress_bar = self.findChild(QtWidgets.QProgressBar, 'progress_bar')
        if ok_button:
            ok_button.setHidden( hidden )
            progress_bar.setHidden(not hidden)
            self.setWindowTitle(ugettext('Completed'))

    def set_cancel_hidden( self, hidden = True ):
        cancel_button = self.findChild( QtWidgets.QPushButton, 'cancel' )
        if cancel_button:
            cancel_button.setHidden( hidden )

class SplashProgress( QtWidgets.QSplashScreen ):
    """
    Wrapper around :class:`QtWidgets.QSplashScreen` to make it behave as if
    it were a progress dialog, this allows reuse of the progress related
    action steps within a splash screen.
    """
    # don't let splash screen stay on top, this might hinder
    # registration wizards or others that wait for user input
    # while camelot is starting up  

    def __init__( self, pixmap ):
        super( SplashProgress, self ).__init__(pixmap)
        # allow the splash screen to keep the application alive, even
        # if the last dialog was closed
        layout = QtWidgets.QVBoxLayout()
        progress_bar = QtWidgets.QProgressBar(parent=self)
        progress_bar.setObjectName('progress_bar')
        layout.addStretch(1)
        layout.addWidget(progress_bar)
        self.setAttribute(Qt.WA_QuitOnClose)
        self.setWindowTitle(' ')
        # support transparency
        if pixmap.mask(): self.setMask(pixmap.mask())
        self.setLayout(layout)

    def setMaximum( self, maximum ):
        progress_bar = self.findChild(QtWidgets.QProgressBar, 'progress_bar')
        progress_bar.setMaximum(maximum)

    def setValue( self, value ):
        progress_bar = self.findChild(QtWidgets.QProgressBar, 'progress_bar')
        progress_bar.setValue(value)

    def setLabelText( self, text ):
        progress_bar = self.findChild(QtWidgets.QProgressBar, 'progress_bar')
        progress_bar.setFormat(text)

    def wasCanceled( self ):
        return False

    def clear_details( self ):
        pass

    def add_detail( self, text ):
        self.setLabelText(text)

    def set_cancel_hidden( self, hidden = True ):
        pass

    def set_ok_hidden( self, hidden = True ):
        pass

    def exec_(self):
        pass
