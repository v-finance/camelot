from camelot.container import Container
from camelot.core.utils import ugettext as _

class PlotContainer( Container ):
    
    def __init__(self, label=_('graph'), color=None, load=None, marker='o',zorder=0):
        self.label = label
        self.color = color
        assert load != None
        assert len(load) == 2
        assert len(load[1]) == len(load[0])
        assert len(load[0]) > 0
        assert len(load[1]) > 0
        self.load = load
        self.marker = marker
        self.zorder = zorder
    
    def plot(self, axes):
        (load_x, load_y) = self.load
        axes.plot(load_x, load_y, color=self.color, marker=self.marker, zorder=self.zorder, label=self.label)
                    
def structure_to_plots( structure ):
    """Convert a list of python objects to a list of plots.  If the python
    object is a tuple, a PlotContainer is constructed with this tuple as arguments. If
    the python object is an instance of a PlotContainer, it is kept as is.
    """

    def object_to_plot_container( o ):
        if isinstance( o, PlotContainer ):
            return o
        return PlotContainer( o )

    return [object_to_plot_container( o ) for o in structure]
