from customdelegate import CustomDelegate
from camelot.view.controls import editors

class ManyToOneChoicesDelegate( CustomDelegate ):
    """Display a ManyToOne field as a ComboBox, filling the list of choices with
  the objects of the target class. 
  
  .. image:: ../_static/enumeration.png
  
  The items in the ComboBox are the unicode representation of the related objects.
  So these classes need an implementation of their __unicode__ method to show
  up in a human readable way in the ComboBox.
  """
  
    editor = editors.OneToManyChoicesEditor
