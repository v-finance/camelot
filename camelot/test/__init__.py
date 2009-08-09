"""
Camelot unittest framework
"""

import unittest

_application_ = []

def get_application():
  """Get the singleton QApplication"""
  from PyQt4.QtGui import QApplication
  if not len(_application_):
    import sys
    _application_.append(QApplication(sys.argv))
  return _application_[0]

class ModelThreadTestCase(unittest.TestCase):
  """Base class for implementing test cases that need a running model_thread.
  """
  
  images_path = ''
  
  def grab_widget(self, widget, suffix=None):
    """Save a widget as a png file :

- the name of the png file is the name of the test case, without 'test'
- it is stored in the directory with the same name as the class, without 'test'     
    """
    import sys
    import os
    from PyQt4.QtGui import QPixmap
    self.process()
    widget.adjustSize()
    pixmap = QPixmap.grabWidget(widget)
    # TODO checks if path exists
    images_path = os.path.join(self.images_path, self.__class__.__name__.lower()[:-len('Test')])
    if not os.path.exists(images_path):
      os.makedirs(images_path)
    test_case_name = sys._getframe(1).f_code.co_name[5:]
    image_name = '%s.png'%test_case_name
    if suffix:
      image_name = '%s_%s.png'%(test_case_name, suffix)
    pixmap.save(os.path.join(images_path, image_name), 'PNG')
    
  def process(self):
    """Wait until all events are processed and the queues of the model thread are empty"""
    self.mt.post_and_block(lambda:None)
    self.app.processEvents()
    self.mt.process_responses()
    self.app.processEvents()

  def setUp(self):
    from camelot.test import get_application
    self.app = get_application()
    from camelot.view.model_thread import get_model_thread, construct_model_thread
    from camelot.view.response_handler import ResponseHandler
    from camelot.view.remote_signals import construct_signal_handler
    rh = ResponseHandler()
    construct_model_thread(rh)
    construct_signal_handler()
    self.mt = get_model_thread()
    if not self.mt.ident:
      self.mt.start()
    
  def tearDown(self):
    self.mt.exit()