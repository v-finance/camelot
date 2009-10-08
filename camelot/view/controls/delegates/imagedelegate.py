
from customdelegate import *
import camelot.types

class ImageDelegate(CustomDelegate):
  """
.. image:: ../_static/image.png
"""
    
  editor = editors.ImageEditor
    
  def setModelData(self, editor, model, index):
    if editor.isModified():
      model.setData(index, 
                    create_constant_function(
                      camelot.types.StoredImage(editor.image)))
