from filedelegate import FileDelegate
from camelot.view.controls import editors

class ImageDelegate(FileDelegate):
    """
    .. image:: ../_static/image.png
    """
    
    editor = editors.ImageEditor

