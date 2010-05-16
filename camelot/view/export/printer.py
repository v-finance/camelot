import logging
logger = logging.getLogger( 'camelot.view.export.printer' )

from PyQt4 import QtGui, QtCore

from camelot.view.model_thread import gui_function

@gui_function
def open_html_in_print_preview_from_gui_thread( html, html_document=QtGui.QTextDocument ):
    
    printer = QtGui.QPrinter()
    printer.setPageSize( QtGui.QPrinter.A4 )
# TODO: make landscape optional
#  printer.setOrientation(QtGui.QPrinter.Landscape)
    # TODO: maximize button
    dialog = QtGui.QPrintPreviewDialog( printer )
  
    def render():
        doc = html_document()
        doc.setHtml( html )
        doc.print_( printer )
    
    dialog.connect( dialog, QtCore.SIGNAL( 'paintRequested(QPrinter*)' ), render )
    dialog.showMaximized()
    dialog.exec_()
