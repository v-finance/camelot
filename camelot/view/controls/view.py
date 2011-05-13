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

"""Functionality common to TableViews and FormViews"""

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.model_thread import post
from camelot.view.model_thread import model_function


class AbstractView(QtGui.QWidget):
    """A string used to format the title of the view ::
    title_format = 'Movie rental overview'

    .. attribute:: header_widget

    The widget class to be used as a header in the table view::

    header_widget = None
    """

    title_format = ''
    header_widget = None

    title_changed_signal = QtCore.pyqtSignal(QtCore.QString)
    icon_changed_signal = QtCore.pyqtSignal(QtGui.QIcon)

    @QtCore.pyqtSlot()
    def refresh(self):
        """Refresh the data in the current view"""
        pass

    @QtCore.pyqtSlot(object)
    def change_title(self, new_title):
        """Will emit the title_changed_signal"""
        #import sip
        #if not sip.isdeleted(self):
        self.title_changed_signal.emit( unicode(new_title) )
        
    @QtCore.pyqtSlot(object)
    def change_icon(self, new_icon):
        self.icon_changed_signal.emit(new_icon)

    @model_function
    def to_html(self):
        pass

    @model_function
    def export_to_word(self):
        from camelot.view.export.word import open_html_in_word
        html = self.to_html()
        open_html_in_word(html)

    @model_function
    def export_to_excel(self):
        from camelot.view.export.excel import open_data_with_excel
        title = self.getTitle()
        columns = self.getColumns()
        data = [d for d in self.getData()]
        open_data_with_excel(title, columns, data)

    @model_function
    def export_to_mail(self):
        from camelot.view.export.outlook import open_html_in_outlook
        html = self.to_html()
        open_html_in_outlook(html)

class TabView(AbstractView):
    """Class to combine multiple views in Tabs and let them behave as one view.
    This class can be used when defining custom create_table_view methods on an
    ObjectAdmin class to group multiple table views together in one view."""

    def __init__(self, parent, views=[], admin=None):
        """:param views: a list of the views to combine"""
        AbstractView.__init__(self, parent)
        layout = QtGui.QVBoxLayout()
        if self.header_widget:
            self.header = self.header_widget(self, admin)
        else:
            self.header = None
        layout.addWidget(self.header)
        self._tab_widget = QtGui.QTabWidget(self)
        self._tab_widget.setObjectName( 'tab_widget' )
        layout.addWidget(self._tab_widget)
        self.setLayout(layout)

        def get_views_and_titles():
            return [(view, view.get_title()) for view in views]

        post(get_views_and_titles, self.set_views_and_titles)
        post(lambda:self.title_format, self.change_title)

    @QtCore.pyqtSlot()
    def refresh(self):
        """Refresh the data in the current view"""
        for i in range(self._tab_widget.count()):
            view = self._tab_widget.widget(i)
            view.refresh()

    def set_views_and_titles(self, views_and_titles):
        for view, title in views_and_titles:
            self._tab_widget.addTab(view, title)

    def export_to_excel(self):
        return self._tab_widget.currentWidget().export_to_excel()

    def export_to_word(self):
        return self._tab_widget.currentWidget().export_to_word()

    def export_to_mail(self):
        return self._tab_widget.currentWidget().export_to_mail()

    def to_html(self):
        return self._tab_widget.currentWidget().to_html()


