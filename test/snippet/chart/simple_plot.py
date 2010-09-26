from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls import delegates
from camelot.container.chartcontainer import PlotContainer

class Wave(object):
  
    def __init__(self):
        self.amplitude = 1
        self.phase = 0
      
    @property
    def chart(self):
        import math
        x_data = [x/100.0 for x in range(1, 700, 1)]
        y_data = [self.amplitude * math.sin(x - self.phase) for x in x_data]
        return PlotContainer( x_data, y_data )
    
    class Admin(ObjectAdmin):
        form_display = ['amplitude', 'phase', 'chart']
        field_attributes = dict(amplitude = dict(delegate=delegates.FloatDelegate,
                                                 editable=True),
                                phase = dict(delegate=delegates.FloatDelegate,
                                             editable=True),
                                chart = dict(delegate=delegates.ChartDelegate) )