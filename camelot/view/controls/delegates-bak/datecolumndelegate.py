
from customdelegate import *

class DateColumnDelegate(CustomDelegate):
  """Custom delegate for date values"""

  editor = editors.DateEditor

  def paint(self, painter, option, index):
    myoption = QtGui.QStyleOptionViewItem(option)
    myoption.displayAlignment |= Qt.AlignRight | Qt.AlignVCenter
    QtGui.QItemDelegate.paint(self, painter, myoption, index)

  def sizeHint(self, option, index):
    return editors.DateEditor().sizeHint()
