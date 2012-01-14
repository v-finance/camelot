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

import sys
import unittest
import StringIO
import subprocess
from subprocess import PIPE

from PyQt4 import QtGui
from PyQt4.QtCore import QUrl
from PyQt4.QtCore import QEventLoop

from PyQt4.QtNetwork import QNetworkProxy
from PyQt4.QtNetwork import QNetworkRequest
from PyQt4.QtNetwork import QNetworkAccessManager

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
        self.server.debug = True
        self.server.log = StringIO.StringIO()

        self.server.startServing()

    def tearDown(self):
        self.server.stopServing()

    def test_getting_proxy(self):
        proxy = get_network_proxy()
        self.assertTrue(isinstance(proxy, QNetworkProxy))
        self.assertEquals(str(proxy.hostName()), '127.0.0.1')
        self.assertEquals(proxy.port(), 8000)

    def test_access_without_credentials(self):
        loop = QEventLoop()
        proxy = get_network_proxy()
        manager = QNetworkAccessManager()

        manager.setProxy(proxy)
        manager.finished.connect(loop.exit)

        reply = manager.get(QNetworkRequest(QUrl('http://aws.amazon.com/')))
        loop.exec_(flags=QEventLoop.ExcludeUserInputEvents)

        if reply.isFinished():
            self.assertEquals(self.server.log.getvalue(),
                '407 Proxy Authentication Required\n\n')
        else:
            if reply.isRunning():
                self.failUnless(False, msg='The request has timed out.')
            else:
                self.failUnless(False, msg='A Network error occurred.')

    def test_access_with_credentials(self):
        loop = QEventLoop()
        proxy = get_network_proxy()
        proxy.setUser(self.server.username)
        proxy.setPassword(self.server.password)
        manager = QNetworkAccessManager()

        manager.setProxy(proxy)
        manager.finished.connect(loop.exit)

        reply = manager.get(QNetworkRequest(QUrl('http://aws.amazon.com/')))
        loop.exec_(flags=QEventLoop.ExcludeUserInputEvents)

        if reply.isFinished():
            self.assertEquals(self.server.log.getvalue(),
                '407 Proxy Authentication Required\n\n'\
                'GET http://aws.amazon.com/ HTTP/1.1\n\n')
        else:
            if reply.isRunning():
                self.failUnless(False, msg='The request has timed out.')
            else:
                self.failUnless(False, msg='A Network error occurred.')

    def test_access_to_remote_succeeded(self):
        loop = QEventLoop()
        proxy = get_network_proxy()
        proxy.setUser(self.server.username)
        proxy.setPassword(self.server.password)
        manager = QNetworkAccessManager()

        manager.setProxy(proxy)
        manager.finished.connect(loop.exit)

        reply = manager.get(QNetworkRequest(QUrl('http://aws.amazon.com/')))
        loop.exec_(flags=QEventLoop.ExcludeUserInputEvents)

        if reply.isFinished():
            response_code = reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute).toString()
            self.assertEquals(response_code, '200')
            self.assertEquals(reply.url(), QUrl('http://aws.amazon.com/'))
        else:
            if reply.isRunning():
                self.failUnless(False, msg='The request has timed out.')
            else:
                self.failUnless(False, msg='A Network error occurred.')



if __name__ == '__main__':
    setup_a_win32_http_system_proxy('127.0.0.1', 8000)
    unittest.main()
    clear_win_http_settings()

