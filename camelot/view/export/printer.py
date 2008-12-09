import logging
logger = logging.getLogger('camelot.view.export.printer')

def open_html_in_print_preview_from_gui_thread(html):
  from PyQt4 import QtGui, QtCore
  printer = QtGui.QPrinter()
  printer.setPageSize(QtGui.QPrinter.A4)
  # TODO: maximize button
  dialog = QtGui.QPrintPreviewDialog(printer)
  
  def render():
    doc = QtGui.QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)
    
  dialog.connect(dialog, QtCore.SIGNAL('paintRequested(QPrinter*)'), render)
  dialog.exec_()
  
def open_html_in_print_preview(html):
  from camelot.view.model_thread import get_model_thread
  mt = get_model_thread()
  
  def create_html_getter(html):
    return lambda:html

  mt.post(create_html_getter(html), open_html_in_print_preview_from_gui_thread)