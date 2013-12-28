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

import six 

from ...core.qt import QtGui, Qt
from camelot.view.model_thread import object_thread
from camelot.core.utils import ugettext_lazy as _

class HSeparator(QtGui.QFrame):

    def __init__(self, parent=None):
        super(HSeparator, self).__init__(parent)
        self.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Sunken)

class StandaloneWizardPage(QtGui.QDialog):
    """A Standalone Wizard Page Dialog for quick configuration windows"""

    def __init__(self, window_title=None, parent=None, flags=Qt.Dialog):
        super(StandaloneWizardPage, self).__init__(parent, flags)
        self.setWindowTitle( six.text_type(window_title or ' ') )
        self.set_layouts()

    def set_layouts(self):
        assert object_thread( self )
        self._vlayout = QtGui.QVBoxLayout()
        self._vlayout.setSpacing(0)
        self._vlayout.setContentsMargins(0,0,0,0)

        # needed in case we have a widget that changes the size
        # of the widget and can be hidden
        # this prevents the ChangeObjects dialog from being scaleable,
        # therefor commented out
        #self._vlayout.setSizeConstraint(QLayout.SetFixedSize)

        banner_layout = QtGui.QGridLayout()
        banner_layout.setColumnStretch(0, 1)
        banner_layout.addWidget(QtGui.QLabel(), 0, 1, Qt.AlignRight)
        banner_layout.addLayout(QtGui.QVBoxLayout(), 0, 0)

        # TODO: allow banner widget to be supplied
        banner_widget = QtGui.QWidget()
        banner_widget.setLayout(banner_layout)

        self._vlayout.addWidget(banner_widget)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QtGui.QFrame(), 1)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QtGui.QWidget())
        self.setLayout(self._vlayout)

    def banner_widget(self):
        return self._vlayout.itemAt(0).widget()

    def main_widget(self):
        return self._vlayout.itemAt(2).widget()

    def buttons_widget(self):
        return self._vlayout.itemAt(4).widget()

    def banner_layout(self):
        return self.banner_widget().layout()

    def banner_logo_holder(self):
        return self.banner_layout().itemAtPosition(0, 1).widget()

    def banner_text_layout(self):
        return self.banner_layout().itemAtPosition(0, 0).layout()

    def set_banner_logo_pixmap(self, pixmap):
        self.banner_logo_holder().setPixmap(pixmap)

    def set_banner_title(self, title):
        title_widget = QtGui.QLabel('<dt><b>%s</b></dt>' % title)
        self.banner_text_layout().insertWidget(0, title_widget)

    def set_banner_subtitle(self, subtitle):
        subtitle_widget = QtGui.QLabel('<dd>%s</dd>' % subtitle)
        self.banner_text_layout().insertWidget(1, subtitle_widget)

    def set_default_buttons( self,
                             accept = _('OK'),
                             reject = _('Cancel'),
                             done = None ):
        """add an :guilabel:`ok` and a :guilabel:`cancel` button.
        """
        layout = QtGui.QHBoxLayout()
        layout.setDirection( QtGui.QBoxLayout.RightToLeft )
        if accept != None:
            ok_button = QtGui.QPushButton( six.text_type( accept ), self )
            ok_button.setObjectName( 'accept' )            
            ok_button.pressed.connect( self.accept )   
            layout.addWidget( ok_button )
        if reject != None:
            cancel_button = QtGui.QPushButton( six.text_type( reject ), self )
            cancel_button.setObjectName( 'reject' )
            cancel_button.pressed.connect( self.reject )
            layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )

