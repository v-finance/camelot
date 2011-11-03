"""Example code for attaching actions to camelot views
"""

from camelot.admin.action import Action, Mode
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.action_steps import ChangeObject, FlushSession, UpdateProgress
from camelot.view.controls import delegates
from camelot.core.utils import ugettext_lazy as _

class Options(object):
    """A python object in which the options for
    the action will be stored.
    """
    
    def __init__(self):
        self.only_selected = True
        self.change = 1

    # Since Options is a plain old python object, we cannot
    # use an EntityAdmin, and should use the ObjectAdmin            
    class Admin( ObjectAdmin ):
        form_display = ['change', 'only_selected']
        form_size = (100, 100)
        # Since there is no introspection, the delegate should
        # be specified explicitely, and set to editable
        field_attributes = {'only_selected':{'delegate':delegates.BoolDelegate,
                                             'editable':True},
                            'change':{'delegate':delegates.IntegerDelegate,
                                      'editable':True},
                            }

# begin change rating action definition
class ChangeRatingAction( Action ):
    """Action to print a list of movies"""
    
    verbose_name = _('Change Rating')
    
    def model_run( self, model_context ):
        #
        # the model_run generator method yields various ActionSteps
        #
        options = Options()
        yield ChangeObject( options )
        if options.only_selected:
            iterator = model_context.get_selection()
        else:
            iterator = model_context.get_collection()
        for movie in iterator:
            yield UpdateProgress( text = u'Change %s'%unicode( movie ) )
            movie.rating = min( 5, max( 0, (movie.rating or 0 ) + options.change ) )
        #
        # FlushSession will write the changes to the database and inform
        # the GUI
        #
        yield FlushSession( model_context.session )
# end change rating action definition