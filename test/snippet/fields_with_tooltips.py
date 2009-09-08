from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls import delegates

def dynamic_tooltip_x(coordinate):
  return u'The <b>x</b> value of the coordinate, now set to %s'%(coordinate.x)

def dynamic_tooltip_y(coordinate):
  return u'The <b>y</b> value of the coordinate, now set to %s'%(coordinate.y)
  
class Coordinate(object):
  
  def __init__(self):
    self.id = 1
    self.x = 0.0
    self.y = 0.0
      
  class Admin(ObjectAdmin):
    form_display = ['x', 'y',]
    field_attributes = dict(x=dict(delegate=delegates.FloatDelegate, 
                                   tooltip=dynamic_tooltip_x),
                            y=dict(delegate=delegates.FloatDelegate,
                                   tooltip=dynamic_tooltip_y),
                            )
    form_size = (100,100)