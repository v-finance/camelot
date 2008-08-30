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

import unittest
import logging
import sys
          
from PyQt4.QtCore import *
from PyQt4.QtGui import *
           
logger = logging.getLogger('view.unittests')   
def testSuites():

  from model_thread import get_model_thread, construct_model_thread
  from response_handler import ResponseHandler
    
  construct_model_thread(ResponseHandler())
  get_model_thread().start()
  
  class model_thread_tests(unittest.TestCase):
      def setUp(self):
        self.mt = get_model_thread()
      def testRequestAndResponseInDifferentThread(self):
        """Test if the request function is really executed in another thread"""
        
        def get_request_thread():
          import threading
          return threading.currentThread()
        
        def compare_with_response_thread(thread):
          import threading
          self.assertNotEqual(thread, threading.currentThread())
          
        event = self.mt.post( get_request_thread, compare_with_response_thread )
        event.wait()
        self.mt.process_responses()
        
      def testUpdateGuiInResponse(self):

        class testApp(QApplication):
          def __init__(s):
            QApplication.__init__(s, sys.argv)
            s.window = QMainWindow()
            s.window.show()
            QTimer.singleShot(0, s, SLOT('startTests()'))
          @pyqtSignature("startTests()")
          def startTests(s):
            logger.debug('start gui tests')
            t = self.mt.post(lambda :3)
            t.wait()
            s.window.close()
            s.exit()
            
        app = testApp()
        app.exec_()
        logger.debug('finished exec')
        
  import inspect
  for c in locals().values():
    if inspect.isclass(c):
      yield unittest.makeSuite(c, 'test')
        
if __name__ == "__main__":
  logging.basicConfig()
  logging.root.handlers[0].setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)-5s] [%(name)-35s] - %(message)s'))
  logging.root.setLevel(logging.DEBUG)  

  import sys
  import os
  sys.path.insert(0, '..')
  sys.path.insert(0, os.path.join('..', 'libraries'))
  sys.path.insert(0, os.path.join('..', 'mockups'))
  runner=unittest.TextTestRunner()
  for s in testSuites():
    runner.run(s)