
from customdelegate import *

class OneToManyChoicesDelegate(CustomDelegate):
  """Display a OneToMany field as a ComboBox, filling the list of choices with
the objects of the target class. 

.. image:: ../_static/enumeration.png   
"""

  editor = editors.OneToManyChoicesEditor
