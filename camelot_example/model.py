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

import time
import datetime

# begin basic imports
from camelot.core.orm import Entity
from camelot.admin.entity_admin import EntityAdmin

from sqlalchemy import orm
from sqlalchemy.schema import Column, ForeignKey, Table
import sqlalchemy.types
# end basic imports

import camelot.types
from camelot.core.sql import metadata
from camelot.admin.action import Action
from camelot.admin.action import list_filter
from camelot.core.utils import ugettext_lazy as _
from camelot.model.party import Person
from camelot.view import action_steps
from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm, Stretch
from camelot.view.art import ColorScheme

from camelot_example.change_rating import ChangeRatingAction
from camelot_example.drag_and_drop import DropAction

#
# Some helper functions that will be used later on
#

def genre_choices( entity_instance ):
    """Choices for the possible movie genres"""
    return [
    ((None),('')),
    (('action'),('Action')),
    (('animation'),('Animation')),
    (('comedy'),('Comedy')),
    (('drama'),('Drama')),
    (('sci-fi'),('Sci-Fi')),
    (('war'),('War')),
    (('thriller'),('Thriller')),
    (('family'),('Family')) ]

# begin simple action definition
class BurnToDisk( Action ):
    
    verbose_name = _('Burn to disk')
    name = 'burn'
    
    def model_run( self, model_context ):
        yield action_steps.UpdateProgress( 0, 3, _('Formatting disk') )
        time.sleep( 0.7 )
        yield action_steps.UpdateProgress( 1, 3, _('Burning movie') )
        time.sleep( 0.7 )
        yield action_steps.UpdateProgress( 2, 3, _('Finishing') )
        time.sleep( 0.5 )
# end simple action definition

    def get_state( self, model_context ):
        """Turn the burn to disk button on, only if the title of the
        movie is entered"""
        state = super( BurnToDisk, self ).get_state( model_context )
        for obj in model_context.get_selection():
            if obj.title:
                state.enabled = True
            else:
                state.enabled = False
                break
        return state
    
# begin short movie definition
