from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls import delegates

class Coordinate(object):
  
  def __init__(self):
    self.id = 1
    self.x = 0
    self.y = 0
    
  class Admin(ObjectAdmin):
    form_display = ['x', 'y']
    field_attributes = dict(x=dict(delegate=delegates.FloatDelegate),
                            y=dict(delegate=delegates.FloatDelegate),)