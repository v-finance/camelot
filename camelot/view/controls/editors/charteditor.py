#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import logging

from ....core.qt import QtGui, QtWidgets, QtCore
from camelot.admin.action.list_action import ListActionGuiContext
from camelot.core.utils import ugettext as _
from camelot.view.controls.editors.customeditor import AbstractCustomEditor
from camelot.view.controls.editors.wideeditor import WideEditor
from camelot.view.proxy import ValueLoading
from camelot.view.art import Icon

PAD_INCHES = 0.1

LOGGER = logging.getLogger('camelot.view.controls.editors.charteditor')

class ChartEditor( QtWidgets.QFrame, AbstractCustomEditor, WideEditor ):
    """Editor to display and manipulate matplotlib charts.  The editor
    itself is generic for all kinds of plots,  it simply provides the
    data to be ploted with a set of axes.  The data itself should know
    how exactly to plot itself.
    """

    show_fullscreen_signal = QtCore.qt_signal()
    editingFinished = QtCore.qt_signal()

    def __init__(self, parent=None, width=50, height=40, dpi=50, field_name='chart', **kwargs):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        super(ChartEditor, self).__init__( parent )
        AbstractCustomEditor.__init__( self )
        self.setObjectName( field_name )

        chart_frame = QtWidgets.QFrame( self )
        chart_frame.setFrameShape( self.Box )
        chart_frame.setContentsMargins( 1, 1, 1, 1 )
        chart_frame_layout = QtWidgets.QHBoxLayout()
        chart_frame_layout.setContentsMargins( 0, 0, 0, 0)
        chart_frame.setLayout( chart_frame_layout )

        # find out background color, because using a transparent
        # figure fails when the window is resized: the background
        # is not redrawn
        # need to do str() else matplotlib gets confused by the qstring
        # bgcolorrgb = str(self.palette().background().color().name())
        self.fig = Figure(
            figsize=(width, height),
            dpi=dpi,
            facecolor='#ffffff',
        )
        layout = QtWidgets.QHBoxLayout()
        self.canvas = FigureCanvas( self.fig )
        chart_frame_layout.addWidget( self.canvas )
        layout.addWidget(chart_frame)
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing( 0 )

        icon = Icon( 'tango/16x16/actions/document-print-preview.png' ).getQIcon()
        button_layout.addStretch()

        print_button = QtWidgets.QToolButton()
        print_button.setIcon( icon )
        print_button.setAutoRaise( True )
        print_button.setToolTip( _('Print Preview') )
        print_button.clicked.connect( self.print_preview )
        button_layout.addWidget( print_button )

        icon = Icon( 'tango/16x16/actions/edit-copy.png' ).getQIcon()
        copy_button = QtWidgets.QToolButton()
        copy_button.setIcon( icon )
        copy_button.setAutoRaise( True )
        copy_button.setToolTip( _('Copy to clipboard') )
        copy_button.clicked.connect( self.copy_to_clipboard )
        button_layout.addWidget( copy_button )

        layout.addLayout( button_layout )
        layout.setContentsMargins( 0, 0, 0, 0)
        self.setLayout(layout)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.canvas.installEventFilter(self)
        self.show_fullscreen_signal.connect(self.show_fullscreen)
        self.canvas.updateGeometry()
        self._litebox = None
        self.gui_context = ListActionGuiContext()

    @QtCore.qt_slot()
    def copy_to_clipboard(self):
        """Copy the chart to the clipboard"""
        clipboard = QtWidgets.QApplication.clipboard()
        pixmap = QtGui.QPixmap.grabWidget( self.canvas )
        clipboard.setPixmap( pixmap )

    @QtCore.qt_slot()
    def print_preview(self):
        """Popup a print preview dialog for the Chart"""
        from camelot.view.action_steps import PrintChart
        print_chart = PrintChart( self._value )
        print_chart.gui_run( self.gui_context )

    def set_field_attributes(self, *args, **kwargs):
        """Overwrite set_field attributes because a ChartEditor cannot be
        disabled or have its background color changed"""
        pass

    @staticmethod
    def show_fullscreen_chart(chart, parent):
        """
        :param chart: a chart container
        :return: the widget showing the chart, by default a LiteBoxView
        """
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        from camelot.view.controls.liteboxview import LiteBoxView
        from camelot.container.chartcontainer import structure_to_figure_container
        figure_container = structure_to_figure_container( chart )
        litebox = LiteBoxView(parent)
        fig = Figure(facecolor='#ffffff')
        canvas = FigureCanvas(fig)
        canvas.updateGeometry()
        figure_container.plot_on_figure(fig)
        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(canvas)
        litebox.show_fullscreen_item(proxy)
        canvas.draw()
        return litebox

    @QtCore.qt_slot()
    def show_fullscreen(self):
        """Show the plot full screen, using the litebox"""
        if self._value:
            # if we give the litebox a parent, the close button does not work ??
            self._litebox = self.show_fullscreen_chart(self._value, None)

    def eventFilter(self, object, event):
        """intercept mouse clicks on a chart to show the chart fullscreen"""
        if not object.isWidgetType():
            return False
        if event.type() != QtCore.QEvent.MouseButtonPress:
            return False
        if event.modifiers() != QtCore.Qt.NoModifier:
            return False
        if event.buttons() == QtCore.Qt.LeftButton:
            self.show_fullscreen_signal.emit()
            return True
        return False

    def set_value(self, value):
        """Accepts a camelot.container.chartcontainer.FigureContainer or a
        camelot.container.chartcontainer.AxesContainer """
        from camelot.container.chartcontainer import structure_to_figure_container
        self._value = structure_to_figure_container( AbstractCustomEditor.set_value( self, value ) )
        self.on_draw()

    def get_value(self):
        return AbstractCustomEditor.get_value( self ) or self._value

#    def _get_tightbbox(self, fig, pad_inches):
#        renderer = fig.canvas.get_renderer()
#        bbox_inches = fig.get_tightbbox(renderer)
#        return bbox_inches.padded(pad_inches)
#
#    def tight_borders(self, fig, pad_inches=PAD_INCHES):
#        """Stretch subplot boundaries to figure edges plus padding."""
#        # call draw to update the renderer and get accurate bboxes.
#        import numpy as np
#        fig.canvas.draw()
#        bbox_original = fig.bbox_inches
#        bbox_tight = self._get_tightbbox(fig, pad_inches)
#
#        print bbox_tight
#
#        # figure dimensions ordered like bbox.extents: x0, y0, x1, y1
#        lengths = np.array([bbox_original.width, bbox_original.height,
#                            bbox_original.width, bbox_original.height])
#        whitespace = (bbox_tight.extents - bbox_original.extents) / lengths
#
#        # border padding ordered like bbox.extents: x0, y0, x1, y1
#        current_borders = np.array([fig.subplotpars.left, fig.subplotpars.bottom,
#                                    fig.subplotpars.right, fig.subplotpars.top])
#
#
#        left, bottom, right, top = current_borders - whitespace
#        print self.canvas.size()
#        print left, bottom, right, top
#        fig.subplots_adjust(bottom=bottom, top=top, left=left, right=right)

    def on_draw(self):
        """draw the matplotlib figure on the canvas"""
        if self._value not in (None, ValueLoading):
            self._value.plot_on_figure(self.fig)
            self.canvas.draw()
#        renderer = self.fig.canvas.get_renderer()
#        print 'widget size', self.canvas.size()
#        print 'renderer size', renderer.get_canvas_width_height()
#        print 'points_to_pixels', renderer.points_to_pixels(1.0)
#        print 'tightbbox', self.fig.get_tightbbox(renderer)
#        #self.fig.subplots_adjust(bottom=0.3, right=0.9, top=0.9, left=0.1)
#        self.tight_borders(self.fig)
#        self.canvas.draw()


