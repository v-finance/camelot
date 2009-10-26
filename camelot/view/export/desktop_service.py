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
