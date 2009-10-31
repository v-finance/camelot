#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================

"""QT Response handler class to be used when constructing
a model thread. Construct this response handler within the
GUI thread to have all responses being handled within the
event loop of the GUI thread."""

import logging
logger = logging.getLogger('response_handler')

from PyQt4.QtCore import QObject, SIGNAL

class ResponseHandler(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.response_signal = SIGNAL("responseAvailable")
        self.start_signal = SIGNAL("startProcessingRequest")
        self.stop_signal = SIGNAL("stopProcessingRequest")
        self.connect(self, self.response_signal, self.handleResponse)
    def handleResponse(self, mt):
        mt.process_responses()
    def responseAvailable(self, mt):
        self.emit(self.response_signal, mt)
    def startProcessingRequest(self, mt):
        self.emit(self.start_signal)
    def stopProcessingRequest(self, mt):
        self.emit(self.stop_signal)
