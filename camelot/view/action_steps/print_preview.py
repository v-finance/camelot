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

from PyQt4 import QtCore, QtGui

from camelot.admin.action import ActionStep

class PrintPreview( ActionStep ):
    """
    Display a print preview dialog box.
    
    :param html: a string containing the html to render in the print
        preview.
        
    the rendering of the html can be customised using these attributes :
    
    .. attribute:: html_document
    
        the class used to render the html, by default a
        :class:`QtGui.QTextDocument` is taken, but a :class:`QtWebKit.QWebView` 
        can be used as well.
    
    .. attribute:: page_size
    
        the page size, by default :class:`QtGui.QPrinter.A4` is used
    
    .. attribute:: page_orientation
    
        the page orientation, by default :class:`QtGui.QPrinter.Portrait`
        is used.
    
    .. image:: /_static/simple_report.png
        """
    
    def __init__( self, html ):
        self.html_document = None
        self.printer = None
        self.page_size = None
        self.page_orientation = None
        self.html = html

    def render( self ):
        """create the print preview widget. this method is used to unit test
        the action step."""
        if not self.printer:
            self.printer = QtGui.QPrinter()
        if not self.printer.isValid():
            self.printer.setOutputFormat( QtGui.QPrinter.PdfFormat )
        if self.page_size != None:
            self.printer.setPageSize( self.page_size )
        if self.page_orientation != None:
            self.printer.setOrientation( self.page_orientation )
        dialog = QtGui.QPrintPreviewDialog( self.printer, flags=QtCore.Qt.Window )
        dialog.paintRequested.connect( self.paint_on_printer )
        # show maximized seems to trigger a bug in qt which scrolls the page 
        # down dialog.showMaximized()
        desktop = QtGui.QApplication.desktop()
        available_geometry = desktop.availableGeometry( dialog )
        # use the size of the screen instead to set the dialog size
        dialog.resize( available_geometry.width() * 0.75, 
                       available_geometry.height() * 0.75 )
        return dialog

    @QtCore.pyqtSlot( QtGui.QPrinter )
    def paint_on_printer( self, printer ):
        doc = (self.html_document or QtGui.QTextDocument)()
        doc.setHtml( self.html )
        doc.print_( printer )
     
    def gui_run( self, gui_context ):
        dialog = self.render()
        dialog.exec_()

class PrintJinjaTemplate( PrintPreview ):
    """Render a jinja template into a print preview dialog.
    
    :param environment: a :class:`jinja2.Environment` object to be used
        to load templates from.
        
    :param template: the name of the template as it can be fetched from
        the Jinja environment.
        
    :param context: a dictionary with objects to be used when rendering
        the template
    """
        
    def __init__( self,
                  environment,
                  template, 
                  context={}, ):
        template = environment.get_template( template )
        html = template.render( context )
        super( PrintJinjaTemplate, self).__init__( html )
