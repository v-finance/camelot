#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================



from ...core.qt import QtWidgets, Qt
from camelot.core.utils import ugettext_lazy as _


class HSeparator(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super(HSeparator, self).__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Shape.HLine | QtWidgets.QFrame.Shadow.Sunken)


class StandaloneWizardPage(QtWidgets.QDialog):
    """A Standalone Wizard Page Dialog for quick configuration windows"""

    def __init__(self, window_title=None, parent=None, flags=Qt.WindowType.Dialog):
        super(StandaloneWizardPage, self).__init__(parent, flags)
        self.setWindowTitle( str(window_title or ' ') )
        self.set_layouts()

    def set_layouts(self):
        self._vlayout = QtWidgets.QVBoxLayout()
        self._vlayout.setSpacing(0)
        self._vlayout.setContentsMargins(0,0,0,0)

        # needed in case we have a widget that changes the size
        # of the widget and can be hidden
        # this prevents the ChangeObjects dialog from being scaleable,
        # therefor commented out
        #self._vlayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        banner_layout = QtWidgets.QGridLayout()
        banner_layout.setColumnStretch(0, 1)
        banner_layout.addWidget(QtWidgets.QLabel(), 0, 1, Qt.AlignmentFlag.AlignRight)
        banner_layout.addLayout(QtWidgets.QVBoxLayout(), 0, 0)

        # TODO: allow banner widget to be supplied
        banner_widget = QtWidgets.QWidget()
        banner_widget.setLayout(banner_layout)

        self._vlayout.addWidget(banner_widget)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QtWidgets.QFrame(), 1)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QtWidgets.QWidget())
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
        title_widget = QtWidgets.QLabel('<dt><b>%s</b></dt>' % title)
        self.banner_text_layout().insertWidget(0, title_widget)

    def set_banner_subtitle(self, subtitle):
        # setting the subtitle without setting the title crashes the dialog,
        # probably because index 1 is invalid
        index = 1 if self.banner_text_layout().count() else 0
        subtitle_widget = QtWidgets.QLabel('<dd>%s</dd>' % subtitle)
        self.banner_text_layout().insertWidget(index, subtitle_widget)

    def set_default_buttons( self,
                             accept = _('OK'),
                             reject = _('Cancel'),
                             done = None ):
        """add an :guilabel:`ok` and a :guilabel:`cancel` button.
        """
        layout = QtWidgets.QHBoxLayout()
        layout.setDirection( QtWidgets.QBoxLayout.Direction.RightToLeft )
        if accept != None:
            ok_button = QtWidgets.QPushButton( str( accept ), self )
            ok_button.setObjectName( 'accept' )
            ok_button.pressed.connect( self.accept )
            layout.addWidget( ok_button )
        if reject != None:
            cancel_button = QtWidgets.QPushButton( str( reject ), self )
            cancel_button.setObjectName( 'reject' )
            cancel_button.pressed.connect( self.reject )
            layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )

