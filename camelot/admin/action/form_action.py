#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui

from camelot.admin.action.base import Action
from camelot.core.utils import ugettext as _
from camelot.view.art import Icon

from application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )
import list_action

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
       
    .. attribute:: view
    
       a :class:`camelot.view.controls.view.AbstractView` class that represents
       the view in which the action is triggered.
       
    """
        
    model_context = FormActionModelContext
    
    def __init__( self ):
        super( FormActionGuiContext, self ).__init__()
        self.widget_mapper = None
        self.view = None

    def create_model_context( self ):
        context = super( FormActionGuiContext, self ).create_model_context()
        context._model = self.widget_mapper.model()
        context.collection_count = context._model.rowCount()
        context.current_row = self.widget_mapper.currentIndex()
        return context
        
    def copy( self, base_class = None ):
        new_context = super( FormActionGuiContext, self ).copy( base_class )
        new_context.widget_mapper = self.widget_mapper
        new_context.view = self.view
        return new_context

class CloseForm( Action ):
    
    shortcut = QtGui.QKeySequence.Close
    icon = Icon('tango/16x16/actions/system-log-out.png')
    verbose_name = _('Close')
    tooltip = _('Close this form')
    
    def gui_run( self, gui_context ):
        gui_context.widget_mapper.submit()
        super( CloseForm, self ).gui_run( gui_context )
        
    def model_run( self, model_context ):
        from PyQt4 import QtGui
        from camelot.view import action_steps
        yield action_steps.UpdateProgress( text = _('Closing form') )
        validator = model_context.admin.get_validator()
        obj = model_context.get_object()
        admin  = model_context.admin
        if obj == None:
            yield action_steps.CloseView()
        #
        # validate the object, and if the object is valid, simply close
        # the view
        #
        messages = validator.objectValidity( obj )
        valid = ( len( messages ) == 0 )
        if valid:
            yield action_steps.CloseView()
        else:
            #
            # if the object is not valid, request the user what to do
            #
            message = action_steps.MessageBox( '\n'.join( messages ),
                                               QtGui.QMessageBox.Warning,
                                               _('Invalid form'),
                                               QtGui.QMessageBox.Ok | QtGui.QMessageBox.Discard )
            reply = yield message
            if reply == QtGui.QMessageBox.Discard:
                yield action_steps.CloseView()
                if admin.is_persistent( obj ):
                    admin.refresh( obj )
                    yield action_steps.UpdateObject( obj )
                else:
                    yield action_steps.DeleteObject( obj )
                    admin.expunge( obj )
    
class ToPreviousForm( list_action.ToPreviousRow ):
    """Move to the previous form"""

    def gui_run( self, gui_context ):
        gui_context.view.to_previous()
        
    def get_state( self, model_context ):
        return Action.get_state( self, model_context )
    
class ToFirstForm( list_action.ToFirstRow ):
    """Move to the form"""
    
    def gui_run( self, gui_context ):
        gui_context.view.to_first()

    def get_state( self, model_context ):
        return Action.get_state( self, model_context )
    
class ToNextForm( list_action.ToNextRow ):
    """Move to the next form"""

    def gui_run( self, gui_context ):
        gui_context.view.to_next()

    def get_state( self, model_context ):
        return Action.get_state( self, model_context )
    
class ToLastForm( list_action.ToLastRow ):
    """Move to the last form"""

    def gui_run( self, gui_context ):
        gui_context.view.to_last()

    def get_state( self, model_context ):
        return Action.get_state( self, model_context )
    
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

