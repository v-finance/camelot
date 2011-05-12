"""Example code for attaching actions to camelot views
"""

from camelot.admin.list_action import PrintHtmlListAction
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.controls.delegates import BoolDelegate

class PrintMovieListAction( PrintHtmlListAction ):
    """Action to print a list of movies"""
    
    class Options(object):
        """A python object in which the options for
        the action will be stored.
        """
        
        def __init__(self):
            self.only_selected = False

        # Since Options is a plain old python object, we cannot
        # use an EntityAdmin, and should use the ObjectAdmin            
        class Admin( ObjectAdmin ):
            form_display = ['only_selected']
            # Since there is no introspection, the delegate should
            # be specified explicitely, and set to editable
            field_attributes = {'only_selected':{'delegate':BoolDelegate,
                                                 'editable':True}}
                                   
    def html(self, collection, selection, options):
        if options.only_selected:
            generator = selection
        else:
            generator = collection
            
        return '<br/>'.join([movie.title for movie in generator])