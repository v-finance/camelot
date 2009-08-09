"""
Camelot unittest framework
"""

_application_ = []

def get_application():
  """Get the singleton QApplication"""
  from PyQt4.QtGui import QApplication
  if not len(_application_):
    import sys
    _application_.append(QApplication(sys.argv))
  return _application_[0]