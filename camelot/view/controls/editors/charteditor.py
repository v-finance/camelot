import logging

from PyQt4 import QtGui, QtCore

from camelot.view.controls.editors.customeditor import CustomEditor
from camelot.view.proxy import ValueLoading

from camelot.view.controls.liteboxview import LiteBoxView

logger = logging.getLogger('camelot.view.controls.editors.charteditor')

class ChartEditor(CustomEditor):
    """Editor to display and manipulate matplotlib charts.  The editor
    itself is generic for all kinds of plots,  it simply provides the
    data to be ploted with a set of axes.  The data itself should know
    how exactly to plot itself.
    """
        
    show_fullscreen_signal = QtCore.SIGNAL('show_fullscreen')
    
    def __init__(self,
          parent=None,
          width=50, height=40,
          dpi=50,
          **kwargs
    ):
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
        self.connect(self, self.show_fullscreen_signal, self.show_fullscreen)
        self.canvas.updateGeometry()
        
    def show_fullscreen(self):
        """Show the plot full screen, using the litebox"""
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas         
        if self.value_:
            fig = Figure(
                figsize=(200, 100),
                dpi=100,
                facecolor='#ffffff',
            )
            canvas = FigureCanvas(self.fig)
            self.value_.draw(fig)
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
            self.emit(self.show_fullscreen_signal)
            return True        
        return False
            
    def set_value(self, value):
        self.value_ = super(ChartEditor, self).set_value(value)
        self.on_draw()

    def on_draw(self):
        if self.value_ not in (None, ValueLoading):
            self.value_.draw(self.fig)
            self.canvas.draw()
