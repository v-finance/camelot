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

"""
This is part of a test implementation of the new actions draft, it is not
intended for production use
"""

from camelot.admin.action.base import Action
from application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )

class ListActionModelContext( ApplicationActionModelContext ):
    """On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`, 
    this context contains :
        
    .. attribute:: selection_count
    
        the number of selected rows.
        
    .. attribute:: collection_count
    
        the number of rows in the list.
        
    .. attribute:: selected_rows
    
        an ordered list with tuples of selected row ranges.  the range is
        inclusive.
        
    .. attribute:: current_row
    
        the current row in the list
        
    .. attribute:: session
    
        The session to which the objects in the list belong.
        
    """
    
    def __init__( self ):
        super( ListActionModelContext, self ).__init__()
        self._model = None
        self.admin = None
        self.current_row = None
        self.selection_count = 0
        self.collection_count = 0
        self.selected_rows = []
        
    @property
    def session( self ):
        return self._model.get_query_getter()().session
        
    def get_selection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects selected
        """
        if self.selection_count == self.collection_count:
            # if all rows are selected, take a shortcut
            for obj in self.get_collection( yield_per ):
                yield obj
        else:
            for (first_row, last_row) in self.selected_rows:
                for row in range( first_row, last_row + 1 ):
                    yield self._model._get_object( row )
    
    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self._model.get_collection():
            yield obj
            
    def get_object( self ):
        """
        :return: the object displayed in the current row or None
        """
        if self.current_row != None:
            return self._model._get_object( self.current_row )
        
class ListActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a table view.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: item_view
    
       the :class:`QtGui.QAbstractItemView` class that relates to the table 
       view on which the widget will be placed.
       
    """
        
    model_context = ListActionModelContext
    
    def __init__( self ):

        super( ListActionGuiContext, self ).__init__()
        self.item_view = None

    def create_model_context( self ):
        context = super( ListActionGuiContext, self ).create_model_context()
        context._model = self.item_view.model()
        context.current_row = self.item_view.currentIndex().row()
        context.collection_count = context._model.rowCount()
        selection_count = 0
        selected_rows = []
        selection = self.item_view.selectionModel().selection()
        for i in range( len( selection ) ):
            selection_range = selection[i]
            rows_range = ( selection_range.top(), selection_range.bottom() )
            selected_rows.append( rows_range )
            selection_count += ( rows_range[1] - rows_range[0] ) + 1
        context.selection_count = selection_count
        context.selected_rows = selected_rows
        return context
        
    def copy( self ):
        new_context = super( ListActionGuiContext, self ).copy()
        new_context.item_view = self.item_view
        return new_context

class CallMethod( Action ):
    
    def __init__( self, verbose_name, method, enabled=None ):
        """
        Call a method on all objects in a selection, and flush the
        session.
        
        :param verbose_name: the name of the action, as it should appear
            to the user
        :param method: the method to call on the objects
        :param enabled: method to call on objects to verify if the action is
            enabled, by default the action is always enabled
        """
        self.verbose_name = verbose_name
        self.method = method
        self.enabled = enabled
        
    def model_run( self, model_context ):
        from camelot.view.action_steps import UpdateProgress, FlushSession
        step = max( 1, model_context.selection_count / 100 )
        for i, obj in enumerate( model_context.get_selection() ):
            if i%step == 0:
                yield UpdateProgress( i, model_context.selection_count )
            self.method( obj )
        yield FlushSession( model_context.session )
        
    def get_state( self, model_context ):
        state = super( CallMethod, self ).get_state( model_context )
        if self.enabled != None:
            for obj in model_context.get_selection():
                if not self.enabled( obj ):
                    state.enabled = False
                    break
        return state
            
class OpenForm( Action ):
    """Open a form view for the current row of a list."""
    
    def gui_run( self, gui_context ):
        from camelot.view.workspace import show_top_level
        from camelot.view.proxy.queryproxy import QueryTableProxy
        model = QueryTableProxy(
            gui_context.admin,
            gui_context.item_view.model().get_query_getter(),
            gui_context.admin.get_fields,
            max_number_of_rows = 1,
            cache_collection_proxy = gui_context.item_view.model()
        )
        row = gui_context.item_view.currentIndex().row()
        formview = gui_context.admin.create_form_view(
            u'', 
            model, 
            row, 
            parent=None
        )
        # make sure there is no 'pythonw' window title in windows for a
        # second
        formview.setWindowTitle( u'' )
        show_top_level( formview, gui_context.item_view )
