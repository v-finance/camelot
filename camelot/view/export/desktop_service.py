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
import logging
logger = logging.getLogger('camelot.view.export.html')

def open_html_in_desktop_service(html):
    import os
    import tempfile
    html_fd, html_fn = tempfile.mkstemp(suffix='.html')
    html_file = os.fdopen(html_fd, 'wb')
    html_file.write(html.encode('utf-8'))
    html_file.close()
    from PyQt4 import QtGui, QtCore
    QtGui.QDesktopServices.openUrl(QtCore.QUrl('file://%s' % html_fn))



