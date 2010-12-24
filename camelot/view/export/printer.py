#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

import logging
logger = logging.getLogger('camelot.view.export.printer')

from PyQt4 import QtCore
from PyQt4.QtCore import QCoreApplication

from PyQt4.QtGui import QPrinter
from PyQt4.QtGui import QTextDocument
from PyQt4.QtGui import QPrintPreviewDialog

from camelot.view.model_thread import gui_function


@gui_function
def open_html_in_print_preview_from_gui_thread(html,
    html_document=QTextDocument, page_size=None, page_orientation=None):

     printer = QPrinter()
     printer.setPageSize(page_size or QPrinter.A4)
     printer.setOrientation(page_orientation or QPrinter.Portrait)
     dialog = QPrintPreviewDialog(printer)

     @QtCore.pyqtSlot(QPrinter)
     def render(printer):
         doc = html_document()
         doc.setHtml(html)
         doc.print_(printer)

     dialog.paintRequested.connect(render)
     # show maximized seems to trigger a bug in qt which scrolls the page down
     #dialog.showMaximized()
     desktop = QCoreApplication.instance().desktop()
     # use the size of the desktop instead to set the dialog size
     dialog.resize(desktop.width() * 0.75, desktop.height() * 0.75)
     dialog.exec_()