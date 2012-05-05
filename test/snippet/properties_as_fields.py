import math

from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls import delegates

class Coordinate( object ):
  
  def __init__( self, x = 0, y = 0 ):
    self.id = 1
    self.x = x
    self.y = y
    
  @property
  def r( self ):
    return math.sqr( self.x**2, self.y**2 )
    
  class Admin( ObjectAdmin ):
    form_display = ['x', 'y', 'r']
    field_attributes = dict( x = dict( delegate = delegates.FloatDelegate,
                                       editable = True ),
                             y = dict( delegate = delegates.FloatDelegate,
                                       editable = True ),
                             r = dict( delegate = delegates.FloatDelegate ) )