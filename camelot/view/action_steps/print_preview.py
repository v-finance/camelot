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

from PyQt4 import QtCore, QtGui

from camelot.admin.action import ( ActionStep,
                                   DocumentActionGuiContext )
from camelot.core.templates import environment
from camelot.view.action_steps.open_file import OpenFile
from camelot.view.utils import resize_widget_to_screen

class PrintPreviewDialog( QtGui.QPrintPreviewDialog ):
    """A custom :class:`QtGui.QPrintPreviewDialog` that allows additional 
    actions on the toolbar.
    
    :param printer: a :class:`QtGui.QPrinter`
    :param gui_context: the :class:`camelot.admin.action.base.GuiContext` to 
        pass to the actions    
    :param actions: a list of :class:`camelot.admin.action.base.Action` objects
    :param parent: a :class:`QtGui.QWidget`
    :param flags: a :class:`Qt.WindowFlags`
    """
    
    def __init__( self, printer, gui_context, 
                  actions = [], parent = None, flags = 0 ):
        super( PrintPreviewDialog, self ).__init__( printer, parent, flags )
        toolbar = self.findChild( QtGui.QToolBar )
        self.gui_context = gui_context
        for action in actions:
            qaction = action.render( self.gui_context, toolbar )
            qaction.triggered.connect( self.action_triggered )
            toolbar.addAction( qaction )
        self.paintRequested.connect( self.paint_on_printer )
            
    @QtCore.pyqtSlot( bool )
    def action_triggered( self, _checked = False ):
        action_action = self.sender()
        action_action.action.gui_run( self.gui_context ) 
        preview_widget = self.findChild( QtGui.QPrintPreviewWidget )
        preview_widget.updatePreview()
        
    @QtCore.pyqtSlot( QtGui.QPrinter )
    def paint_on_printer( self, printer ):
        self.gui_context.document.print_( printer )

class PrintPreview( ActionStep ):
    """
    Display a print preview dialog box.
    
    :param document: an instance of :class:`QtGui.QTextDocument` or 
        :class:`QtWebKit.QWebView` that has a :meth:`print_` method.  The
        thread affinity of this object will be changed to be able to use it
        in the GUI.
        
    the print preview can be customised using these attributes :
    
    .. attribute:: margin_left

        change the left margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_top

        change the top margin of the content to the page border, unit is set by margin_unit    

    .. attribute:: margin_right

        change the right margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_bottom

        change the bottom margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_unit

        defin which unit is used for the defined margins (e.g. margin_left, margin_bottom)

    .. attribute:: page_size
    
        the page size, by default :class:`QtGui.QPrinter.A4` is used
    
    .. attribute:: page_orientation
    
        the page orientation, by default :class:`QtGui.QPrinter.Portrait`
        is used.
        
    .. attribute:: document
        
        the :class:`QtGui.QTextDocument` holding the document that will be shown in the print
        preview
    
    .. image:: /_static/simple_report.png
        """
    
    def __init__( self, document ):
        self.document = document
        self.document.moveToThread( QtCore.QCoreApplication.instance().thread() )
        self.printer = None
        self.margin_left = None
        self.margin_top = None
        self.margin_right = None
        self.margin_bottom = None
        self.margin_unit = QtGui.QPrinter.Millimeter
        self.page_size = None
        self.page_orientation = None

    def get_printer( self ):
        if not self.printer:
            self.printer = QtGui.QPrinter()
        if not self.printer.isValid():
            self.printer.setOutputFormat( QtGui.QPrinter.PdfFormat )
        return self.printer

    def config_printer( self ):
        self.printer = self.get_printer()
        if self.page_size != None:
            self.printer.setPageSize( self.page_size )
        if self.page_orientation != None:
            self.printer.setOrientation( self.page_orientation )
        if None not in [self.margin_left, self.margin_top, self.margin_right, self.margin_bottom, self.margin_unit]:
            self.printer.setPageMargins( self.margin_left, self.margin_top, self.margin_right, self.margin_bottom, self.margin_unit )
        return self.printer

    def render( self, gui_context ):
        """create the print preview widget. this method is used to unit test
        the action step."""
        self.config_printer()
        gui_context = gui_context.copy( DocumentActionGuiContext )
        gui_context.document = self.document
        from camelot.admin.action.document import EditDocument
        dialog = PrintPreviewDialog( self.printer, 
                                     gui_context, 
                                     actions = [EditDocument()],
                                     flags = QtCore.Qt.Window )
        # show maximized seems to trigger a bug in qt which scrolls the page 
        # down dialog.showMaximized()
        resize_widget_to_screen( dialog )
        return dialog
     
    def gui_run( self, gui_context ):
        dialog = self.render( gui_context )
        dialog.exec_()
        
    def get_pdf( self ):
        self.config_printer()
        self.printer.setOutputFormat( QtGui.QPrinter.PdfFormat )
        filepath = OpenFile.create_temporary_file('.pdf')
        self.printer.setOutputFileName(filepath)
        self.document.print_(self.printer)
        return filepath        

class ChartDocument( QtCore.QObject ):
    """Helper class to print matplotlib charts

    :param chart: a :class:`camelot.container.chartcontainer.FigureContainer` object
        or a :class:`camelot.container.chartcontainer.AxesContainer` subclass

    """
    
    def __init__( self, chart ):
        from camelot.container.chartcontainer import structure_to_figure_container
        super( ChartDocument, self ).__init__()
        self.chart = structure_to_figure_container( chart )
        
    def print_( self, printer ):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        rect = printer.pageRect( QtGui.QPrinter.Inch )
        dpi = printer.resolution()
        fig = Figure( facecolor='#ffffff')
        fig.set_size_inches( ( rect.width(), rect.height() ) )
        fig.set_dpi( dpi )
        self.chart.plot_on_figure( fig )
        canvas = FigureCanvas( fig )
        canvas.render( printer )   
        
class PrintChart( PrintPreview ):
    """
    Display a print preview dialog box for a matplotlib chart.
    
    :param chart: a :class:`camelot.container.chartcontainer.FigureContainer` object
        or a :class:`camelot.container.chartcontainer.AxesContainer` subclass
        
    Example use of this action step :
        
    .. literalinclude:: ../../../test/test_action.py
       :start-after: begin chart print
       :end-before: end chart print
    """

    def __init__( self, chart ):
        super( PrintChart, self ).__init__( ChartDocument( chart ) )
    
class PrintHtml( PrintPreview ):
    """
    Display a print preview dialog box for an html string.
    
    :param html: a string containing the html to render in the print
        preview.
        
    the rendering of the html can be customised using the same attributes
    as those of the :class:`PrintPreview` class.
        """
    
    def __init__( self, html ):
        document = QtGui.QTextDocument()
        document.setHtml( html )
        super( PrintHtml, self ).__init__( document )

class PrintJinjaTemplate( PrintHtml ):
    """Render a jinja template into a print preview dialog.
            
    :param template: the name of the template as it can be fetched from
        the Jinja environment.
        
    :param context: a dictionary with objects to be used when rendering
        the template
        
    :param environment: a :class:`jinja2.Environment` object to be used
        to load templates from.  This defaults to the `environment` object
        available in :mod:`camelot.core.templates`
    """
        
    def __init__( self,
                  template, 
                  context={},
                  environment = environment ):
        self.template = environment.get_template( template )
        self.html = self.template.render( context )
        self.context = context
        super( PrintJinjaTemplate, self).__init__( self.html )
