#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from camelot.admin.action.base import Action
from application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )

class FormActionModelContext( ApplicationActionModelContext ):
    """On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`, 
    this context contains :
        
    .. attribute:: current_row
    
        the row in the list that is currently displayed in the form
        
    .. attribute:: collection_count
    
        the number of objects that can be reached in the form.
        
    .. attribute:: selection_count
    
        the number of objects displayed in the form, at most 1.
                
    .. attribute:: session
    
        The session to which the objects in the list belong.
        
    The :attr:`selection_count` attribute allows the 
    :meth:`model_run` to quickly evaluate the size of the collection without 
    calling the potetially time consuming method :meth:`get_collection`.
    """
    
    def __init__( self ):
        super( FormActionModelContext, self ).__init__()
        self._model = None
        self.admin = None
        self.current_row = None
        self.collection_count = 0
        self.selection_count = 1
        
    @property
    def session( self ):
        return self._model.admin.get_query().session
        
    def get_object( self ):
        """
        :return: the object currently displayed in the form, None if no object
            is displayed yet
        """
        if self.current_row != None:
            return self._model._get_object( self.current_row )
    
    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self._model.get_collection():
            yield obj
            
    def get_selection( self, yield_per = None ):
        """
        Method to be compatible with a 
        :class:`camelot.admin.action.list_action.ListActionModelContext`, this
        allows creating a single Action to be used on a form and on list.
        
        :param yield_per: this parameter has no effect, it's here only for
            compatibility with :meth:`camelot.admin.action.list_action.ListActionModelContext.get_selection`
        :return: a generator that yields the current object displayed in the 
            form and does not yield anything if no object is displayed yet
            in the form.
        """
        if self.current_row != None:
            yield self._model._get_object( self.current_row )
        
class FormActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a form.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: widget_mapper

       the :class:`QtGui.QDataWidgetMapper` class that relates the form 
       widget to the model.
       
    """
        
    model_context = FormActionModelContext
    
    def __init__( self ):
        super( FormActionGuiContext, self ).__init__()
        self.widget_mapper = None

    def create_model_context( self ):
        context = super( FormActionGuiContext, self ).create_model_context()
        context._model = self.widget_mapper.model()
        context.collection_count = context._model.rowCount()
        context.current_row = self.widget_mapper.currentIndex()
        return context
        
    def copy( self ):
        new_context = super( FormActionGuiContext, self ).copy()
        new_context.widget_mapper = self.widget_mapper
        return new_context

def structure_to_form_actions( structure ):
    """Convert a list of python objects to a list of form actions.  If the python
    object is a tuple, a CallMethod is constructed with this tuple as arguments.  If
    the python object is an instance of as Action, it is kept as is.
    """
    from list_action import CallMethod
    
    def object_to_action( o ):
        if isinstance( o, Action ):
            return o
        return CallMethod( o[0], o[1] )

    return [object_to_action( o ) for o in structure]
