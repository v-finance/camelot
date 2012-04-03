"""Example code for drag and drop
"""

from camelot.admin.action import Action

# begin drop action definition
class DropAction( Action ):
    
    drop_mime_types = ['text/plain']
    
# end drop action definition
