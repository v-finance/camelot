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

"""Functionality common to TableViews and FormViews"""

import six

from ...core.qt import QtCore, QtGui

class AbstractView(QtGui.QWidget):
    """A string used to format the title of the view ::
    title_format = 'Movie rental overview'

    .. attribute:: header_widget

    The widget class to be used as a header in the table view::

    header_widget = None
    """

    title_format = ''
    header_widget = None

    title_changed_signal = QtCore.qt_signal(six.text_type)
    icon_changed_signal = QtCore.qt_signal(QtGui.QIcon)

    @QtCore.qt_slot()
    def refresh(self):
        """Refresh the data in the current view"""
        pass

    @QtCore.qt_slot(object)
    def change_title(self, new_title):
        """Will emit the title_changed_signal"""
        #import sip
        #if not sip.isdeleted(self):
        self.title_changed_signal.emit( six.text_type(new_title) )
        
    @QtCore.qt_slot(object)
    def change_icon(self, new_icon):
        self.icon_changed_signal.emit(new_icon)
