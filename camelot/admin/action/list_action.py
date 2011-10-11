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
        
    .. attribute:: session
    
        The session to which the objects in the list belong.
        
    """
    
    def __init__( self ):
        super( ListActionModelContext, self ).__init__()
        self._model = None
        self.admin = None
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
        
class ListActionGuiContext( ApplicationActionGuiContext ):
    
    model_context = ListActionModelContext
    
    def __init__( self ):
        """The context for an :class:`ListAction`.  On top of the attributes of the 
        :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
        this context contains :
    
        .. attribute:: item_view
        
           the :class:`QtGui.QAbstractItemView` class that relates to the table 
           view on which the widget will be placed.
           
        """
        super( ListActionGuiContext, self ).__init__()
        self.item_view = None

    def create_model_context( self ):
        context = super( ListActionGuiContext, self ).create_model_context()
        context._model = self.item_view.model()
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
    
    def __init__( self, verbose_name, method ):
        """
        Call a method on all objects in a selection, and flush the
        session.
        
        :param verbose_name: the name of the action, as it should appear
            to the user
        :param method: the method to call on the objects
        """
        self.verbose_name = verbose_name
        self.method = method
        
    def model_run( self, model_context ):
        from camelot.view.action_steps import UpdateProgress, FlushSession
        if isinstance( model_context, ListActionModelContext ):
            step = max( 1, model_context.selection_count / 100 )
            for i, obj in enumerate( model_context.get_selection() ):
                if i%step == 0:
                    yield UpdateProgress( i, model_context.selection_count )
                self.method( obj )
            yield FlushSession( model_context.session )
