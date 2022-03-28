#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
"""Example code for attaching actions to camelot views
"""

from camelot.admin.action import Action
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.action_steps import ChangeObject, FlushSession, UpdateProgress
from camelot.view.controls import delegates
from camelot.core.utils import ugettext_lazy as _

class Options(object):
    """A python object in which we store the change in rating
    """
    
    def __init__(self):
        self.only_selected = True
        self.change = 1

    # Since Options is a plain old python object, we cannot
    # use an EntityAdmin, and should use the ObjectAdmin            
    class Admin( ObjectAdmin ):
        verbose_name = _('Change rating options')
        form_display = ['change', 'only_selected']
        form_size = (100, 100)
        # Since there is no introspection, the delegate should
        # be specified explicitely, and set to editable
        field_attributes = {'only_selected':{'delegate': delegates.BoolDelegate,
                                             'nullabel': False,
                                             'editable': True},
                            'change':{'delegate':delegates.IntegerDelegate,
                                      'nullable': False,
                                      'editable': True},
                            }

# begin change rating action definition
class ChangeRatingAction( Action ):
    """Action to print a list of movies"""
    
    verbose_name = _('Change Rating')
    name = 'change_rating'
    
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
            yield UpdateProgress( text = u'Change %s'% str( movie ) )
            movie.rating = min( 5, max( 0, (movie.rating or 0 ) + options.change ) )
        #
        # FlushSession will write the changes to the database and inform
        # the GUI
        #
        yield FlushSession( model_context.session )
# end change rating action definition
