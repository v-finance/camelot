#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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
#  ============================================================================

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.controls.editors.customeditor import CustomEditor
from camelot.view.controls.editors.wideeditor import WideEditor
from camelot.view.proxy import ValueLoading

from camelot.view.controls.liteboxview import LiteBoxView

LOGGER = logging.getLogger('camelot.view.controls.editors.charteditor')

class ChartEditor(CustomEditor, WideEditor):
    """Editor to display and manipulate matplotlib charts.  The editor
    itself is generic for all kinds of plots,  it simply provides the
    data to be ploted with a set of axes.  The data itself should know
    how exactly to plot itself.
    """

    show_fullscreen_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, width=50, height=40, dpi=50, **kwargs):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        super(ChartEditor, self).__init__(parent)

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
        ovbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        self.canvas = FigureCanvas(self.fig)
        hbox.addWidget(self.canvas)
        vbox = QtGui.QVBoxLayout()
        vboxw = QtGui.QWidget()
        vboxw.setLayout(vbox)
        hbox.addWidget(vboxw)
        vbox.addStretch()

        hboxw = QtGui.QWidget()
        hboxw.setLayout(hbox)
        ovbox.addWidget(hboxw)
        self.setLayout(ovbox)
        self.canvas.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding
        )
        self.canvas.installEventFilter(self)
        self.lite_box = LiteBoxView()
        self.show_fullscreen_signal.connect(self.show_fullscreen)
        self.canvas.updateGeometry()

    @QtCore.pyqtSlot()
    def show_fullscreen(self):
        """Show the plot full screen, using the litebox"""
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
        if self._value:
            fig = Figure(
                figsize=(200, 100),
                dpi=100,
                facecolor='#ffffff',
            )
            canvas = FigureCanvas(self.fig)
            self._value.plot_on_figure(fig)
            proxy = QtGui.QGraphicsProxyWidget()
            proxy.setWidget(canvas)
            self.lite_box.show_fullscreen_item(proxy)

    def eventFilter(self, object, event):
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
        from camelot.container.chartcontainer import structure_to_figure_container
        self._value = structure_to_figure_container( super(ChartEditor, self).set_value(value) )
        self.on_draw()

    def on_draw(self):
        if self._value not in (None, ValueLoading):
            self._value.plot_on_figure(self.fig)
            self.canvas.draw()
#            self.canvas.updateGeometry()

