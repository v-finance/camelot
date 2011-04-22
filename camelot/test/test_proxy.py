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

import sys
import unittest
import subprocess
from subprocess import PIPE

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtNetwork
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import QEventLoop

from camelot.test.http_proxy import HTTPProxy
from camelot.core.dbprofiles import get_network_proxy


_application_ = None
if not QtGui.QApplication.instance():
    _application_ = QtGui.QApplication([a for a in sys.argv if a])


def setup_a_win32_http_system_proxy(hostname, port):
    # XXX:
    # We are not using a system proxy with regards to Windows. PyQt will go
    # through the registry first and look for a system proxy setting, then
    # through Internet Explorer's settings.  Not sure how Internet Explorer's
    # settings can be changed programmatically so we will simulate a system
    # proxy with proxcfg which should be in PATH
    # reference page:
    # http://msdn.microsoft.com/en-us/library/aa384069%28v=vs.85%29.aspx
    http_proxy_value = 'http=http://%s:%s' % (hostname, port)
    command = ['proxycfg', '-p', http_proxy_value, '"<local>"']
    subprocess.call(command, shell=True, stdin=PIPE, stdout=PIPE,
        stderr=PIPE, universal_newlines=True)


def clear_win_http_settings():
    # XXX:
    # setting a system proxy in Windows writes to the registry and that
    # key needs to be deleted as said on the reference page, but a user
    # might have set a "real" proxy using the same WinHTTPSettings ...
    import win32api
    import win32con
    opened_key = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE,
        'SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings'\
        '\Connections', 0, win32con.KEY_ALL_ACCESS)
    win32api.RegDeleteValue(opened_key, 'WinHttpSettings')

    ERROR_SUCCESS = 0
    error_code = win32api.GetLastError()
    if error_code != ERROR_SUCCESS:
        print 'win32 error code %d', error_code, \
            win32api.FormatMessage(error_code)


class ProxyTestCase(unittest.TestCase):

    def setUp(self):
        self.server = HTTPProxy()
        setup_a_win32_http_system_proxy('127.0.0.1', 8000)

    def tearDown(self):
        self.server.stopServing()
        clear_win_http_settings()

    def test_proxy(self):
        proxy = get_network_proxy()
        self.assertTrue(isinstance(proxy, QtNetwork.QNetworkProxy))
        self.assertEquals(str(proxy.hostName()), '127.0.0.1')
        self.assertEquals(proxy.port(), 8000)

        #manager = QtNetwork.QNetworkAccessManager()
        #manager.setProxy(proxy)

        #event_loop = QEventLoop()
        #request_timer = QTimer()
        #request_timer.timeout.connect(event_loop.exit)
        #manager.finished.connect(event_loop.exit)

        #request = QtNetwork.QNetworkRequest()
        #request.setUrl(QtCore.QUrl('http://aws.amazon.com/'))
        #reply = manager.get(request)
        #self.server.handler_request()
        #reply.readyRead.connect(self.server.handle_request)
        #request_timer.start(5*1000)
        #event_loop.exec_(flags=QEventLoop.ExcludeUserInputEvents)

        #if reply.isFinished():
        #    parts = self.server_log.getvalue().split()
        #    hostname = parts[0]
        #    url = parts[6]
        #    response_code = parts[8]
        #    self.assertTrue(hostname in ['localhost', '127.0.0.1'])
        #    self.assertEquals(url, 'http://aws.amazon.com/')
        #    self.assertEquals(response_code, '200')
        #else:
        #    if reply.isRunning():
        #        self.failUnless(False, msg='The request has timed out.')
        #    else:
        #        self.failUnless(False, msg='Something else happened; the '
        #            'request is not running.')


if __name__ == '__main__':
    unittest.main()
