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

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QFrame, QGridLayout, QLabel, QVBoxLayout, \
    QWidget

from camelot.view.model_thread import object_thread

class HSeparator(QFrame):

    def __init__(self, parent=None):
        super(HSeparator, self).__init__(parent)
        self.setFrameStyle(QFrame.HLine | QFrame.Sunken)


class StandaloneWizardPage(QDialog):
    """A Standalone Wizard Page Dialog for quick configuration windows"""

    def __init__(self, window_title=None, parent=None, flags=Qt.Dialog):
        super(StandaloneWizardPage, self).__init__(parent, flags)
        self.setWindowTitle(window_title or '')
        self.set_layouts()

    def set_layouts(self):
        assert object_thread( self )
        self._vlayout = QVBoxLayout()
        self._vlayout.setSpacing(0)
        self._vlayout.setContentsMargins(0,0,0,0)

        # needed in case we have a widget that changes the size
        # of the widget and can be hidden
        # this prevents the ChangeObjects dialog from being scaleable,
        # therefor commented out
        #self._vlayout.setSizeConstraint(QLayout.SetFixedSize)

        banner_layout = QGridLayout()
        banner_layout.setColumnStretch(0, 1)
        banner_layout.addWidget(QLabel(), 0, 1, Qt.AlignRight)
        banner_layout.addLayout(QVBoxLayout(), 0, 0)

        # TODO: allow banner widget to be supplied
        banner_widget = QWidget()
        banner_widget.setLayout(banner_layout)

        self._vlayout.addWidget(banner_widget)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QFrame(), 1)
        self._vlayout.addWidget(HSeparator())
        self._vlayout.addWidget(QWidget())
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
        title_widget = QLabel('<dt><b>%s</b></dt>' % title)
        self.banner_text_layout().insertWidget(0, title_widget)

    def set_banner_subtitle(self, subtitle):
        subtitle_widget = QLabel('<dd>%s</dd>' % subtitle)
        self.banner_text_layout().insertWidget(1, subtitle_widget)

