#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Proxy representing a collection of entities that live in the model thread.

The proxy represents them in the gui thread and provides access to the data
with zero delay.  If the data is not yet present in the proxy, dummy data is
returned and an update signal is emitted when the correct data is available.
"""

import logging
logger = logging.getLogger( 'camelot.view.proxy.collection_proxy' )

import elixir
import datetime
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore
import sip

from sqlalchemy.orm.session import Session
from camelot.view.art import Icon
from camelot.view.fifo import fifo
from camelot.view.controls import delegates
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import gui_function, \
                                      model_function, post


class DelayedProxy( object ):
    """A proxy object needs to be constructed within the GUI thread. Construct
    a delayed proxy when the construction of a proxy is needed within the Model
    thread.  On first occasion the delayed proxy will be converted to a real
    proxy within the GUI thread
    """
  
    @model_function
    def __init__( self, *args, **kwargs ):
        self.args = args
        self.kwargs = kwargs
    
    @gui_function
    def __call__( self ):
        return CollectionProxy( *self.args, **self.kwargs )
    
@model_function
def tool_tips_from_object(obj, columns):
  
    data = []
    
    for col in columns:
        tooltip_getter = col[1]['tooltip']
        if tooltip_getter:
            data.append( tooltip_getter(obj) )
        else:
            data.append( None )
            
    return data

@model_function
def background_colors_from_object(obj, columns):
  
    data = []
    
    for col in columns:
        background_color_getter = col[1]['background_color']
        if background_color_getter:
            background_color = background_color_getter(obj)
            data.append( background_color )
        else:
            data.append( None )
            
    return data
  
@model_function
def strip_data_from_object( obj, columns ):
    """For every column in columns, get the corresponding value from the
    object.  Getting a value from an object is time consuming, so using
    this function should be minimized.
    :param obj: the object of which to get data
    :param columns: a list of columns for which to get data
    """
    row_data = []
  
    def create_collection_getter( o, attr ):
        return lambda: getattr( o, attr )
    
    for _i, col in enumerate( columns ):
        field_attributes = col[1]
        if field_attributes['python_type'] == list:
            row_data.append( DelayedProxy( field_attributes['admin'],
                            create_collection_getter( obj, col[0] ),
                            field_attributes['admin'].get_columns ) )
        else:
            row_data.append( getattr( obj, col[0] ) )
    return row_data
  
@model_function
def stripped_data_to_unicode( stripped_data, obj, columns ):
    """Extract for each field in the row data a 'visible' form of 
    data"""
  
    row_data = []
  
    for field_data, ( _field_name, field_attributes ) in zip( stripped_data, columns ):
        unicode_data = u''
        if 'unicode_format' in field_attributes:
            unicode_format = field_attributes['unicode_format']
            if field_data != None:
                unicode_data = unicode_format( field_data )
        elif 'choices' in field_attributes:
            choices = field_attributes['choices']
            if callable(choices):
                for key, value in choices( obj ):
                    if key == field_data:
                        unicode_data = value
                        continue
            else:
                unicode_data = field_data
        elif isinstance( field_data, DelayedProxy ):
            unicode_data = u'...'
        elif isinstance( field_data, list ):
            unicode_data = u'.'.join( [unicode( e ) for e in field_data] )
        elif isinstance( field_data, datetime.datetime ):
            # datetime should come before date since datetime is a subtype of date
            if field_data.year >= 1900:
                unicode_data = field_data.strftime( '%d/%m/%Y %H:%M' )
        elif isinstance( field_data, datetime.date ):
            if field_data.year >= 1900:
                unicode_data = field_data.strftime( '%d/%m/%Y' )
        elif field_data != None:
            unicode_data = unicode( field_data )
        row_data.append( unicode_data )
    
    return row_data
  
from camelot.view.proxy import ValueLoading

class EmptyRowData( object ):
    def __getitem__( self, column ):
        return ValueLoading
        return None
    
empty_row_data = EmptyRowData()

class CollectionProxy( QtCore.QAbstractTableModel ):
    """The CollectionProxy contains a limited copy of the data in the actual
    collection, usable for fast visualisation in a QTableView 
    """
  
    _header_font = QtGui.QApplication.font()
    _header_font_required = QtGui.QApplication.font()
    _header_font_required.setBold( True )
    
    header_icon = Icon( 'tango/16x16/places/folder.png' )

    item_delegate_changed_signal = QtCore.SIGNAL('itemDelegateChanged')
  
    @gui_function
    def __init__( self, admin, collection_getter, columns_getter,
                 max_number_of_rows = 10, edits = None, flush_changes = True ):
        """@param admin: the admin interface for the items in the collection
    
        @param collection_getter: a function that takes no arguments and returns
        the collection that will be visualized. This function will be called inside
        the model thread, to prevent delays when this function causes the database
        to be hit.
    
        @param columns_getter: a function that takes no arguments and returns the
        columns that will be cached in the proxy. This function will be called
        inside the model thread.
        """
        from camelot.view.model_thread import get_model_thread
        self.logger = logging.getLogger(logger.name + '.%s'%id(self))
        self.logger.debug('initialize query table for %s' % (admin.get_verbose_name()))
        QtCore.QAbstractTableModel.__init__(self)
        self.admin = admin
        self.iconSize = QtCore.QSize( QtGui.QFontMetrics( self._header_font_required ).height() - 4, QtGui.QFontMetrics( self._header_font_required ).height() - 4 )
        self.form_icon = QtCore.QVariant( self.header_icon.getQIcon().pixmap( self.iconSize ) )
        self.validator = admin.create_validator( self )
        self.collection_getter = collection_getter
        self.column_count = 0
        self.flush_changes = flush_changes
        self.delegate_manager = None
        self.mt = get_model_thread()
        # Set database connection and load data
        self.rows = 0
        self._columns = []
        self.max_number_of_rows = max_number_of_rows
        self.cache = {Qt.DisplayRole         : fifo( 10 * self.max_number_of_rows ),
                      Qt.EditRole            : fifo( 10 * self.max_number_of_rows ),
                      Qt.ToolTipRole         : fifo( 10 * self.max_number_of_rows ),
                      Qt.BackgroundColorRole : fifo( 10 * self.max_number_of_rows ), }
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        # The rows that have unflushed changes
        self.unflushed_rows = set()
        # Set edits
        self.edits = edits or []
        self.rsh = get_signal_handler()
        self.rsh.connect( self.rsh,
                         self.rsh.entity_update_signal,
                         self.handleEntityUpdate )
        self.rsh.connect( self.rsh,
                         self.rsh.entity_delete_signal,
                         self.handleEntityDelete )
        self.rsh.connect( self.rsh,
                         self.rsh.entity_create_signal,
                         self.handleEntityCreate )
    
        def get_columns():
            self._columns = columns_getter()
            return self._columns
      
        post( get_columns, self.setColumns )
#    # the initial collection might contain unflushed rows
        post( self.updateUnflushedRows )
#    # in that way the number of rows is requested as well
        post( self.getRowCount, self.setRowCount )
        self.logger.debug( 'initialization finished' )
        
    
    @model_function
    def updateUnflushedRows( self ):
        """Verify all rows to see if some of them should be added to the
        unflushed rows"""
        for i, e in enumerate( self.collection_getter() ):
            if hasattr(e, 'id') and not e.id:
                self.unflushed_rows.add( i )
        
    def hasUnflushedRows( self ):
        """The model has rows that have not been flushed to the database yet,
        because the row is invalid
        """
        has_unflushed_rows = ( len( self.unflushed_rows ) > 0 )
        self.logger.debug( 'hasUnflushed rows : %s' % has_unflushed_rows )
        return has_unflushed_rows
    
    @model_function
    def getRowCount( self ):
        return len( self.collection_getter() )
    
    @gui_function
    def revertRow( self, row ):
        def create_refresh_entity( row ):
    
            @model_function
            def refresh_entity():
                o = self._get_object( row )
                elixir.session.refresh( o )
                return row, o
        
            return refresh_entity
          
        post( create_refresh_entity( row ), self._revert_row )
    
    def _revert_row(self, row_and_entity ):
        row, entity = row_and_entity
        self.handleRowUpdate( row )
        self.rsh.sendEntityUpdate( self, entity )
    
    @gui_function
    def refresh( self ):
        post( self.getRowCount, self._refresh_content )
    
    @gui_function
    def _refresh_content(self, rows ):
        self.cache = {Qt.DisplayRole         : fifo( 10 * self.max_number_of_rows ),
                      Qt.EditRole            : fifo( 10 * self.max_number_of_rows ),
                      Qt.ToolTipRole         : fifo( 10 * self.max_number_of_rows ),
                      Qt.BackgroundColorRole : fifo( 10 * self.max_number_of_rows ),}
        self.setRowCount( rows )
    
    def set_collection_getter( self, collection_getter ):
        self.collection_getter = collection_getter
        self.refresh()
        
    def get_collection_getter( self ):
        return self.collection_getter
    
    def handleRowUpdate( self, row ):
        """Handles the update of a row when this row might be out of date"""
        self.cache[Qt.DisplayRole].delete_by_row( row )
        self.cache[Qt.EditRole].delete_by_row( row )
        self.cache[Qt.ToolTipRole].delete_by_row( row )
        self.cache[Qt.BackgroundColorRole].delete_by_row( row )
        sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
        self.emit( QtCore.SIGNAL( sig ),
                  self.index( row, 0 ),
                  self.index( row, self.column_count ) )
    
    def handleEntityUpdate( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of date"""
        self.logger.debug( '%s %s received entity update signal' % \
                     ( self.__class__.__name__, self.admin.get_verbose_name() ) )
        if sender != self:
            row = self.cache[Qt.DisplayRole].delete_by_entity( entity )
            row = self.cache[Qt.EditRole].delete_by_entity( entity )
            row = self.cache[Qt.ToolTipRole].delete_by_entity( entity )
            row = self.cache[Qt.BackgroundColorRole].delete_by_entity( entity )
            if row != None:
                self.logger.debug( 'updated row %i' % row )
                sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
                if not sip.isdeleted( self ):
                    self.emit( QtCore.SIGNAL( sig ),
                          self.index( row, 0 ),
                          self.index( row, self.column_count ) )
            else:
                self.logger.debug( 'entity not in cache' )
        else:
            self.logger.debug( 'duplicate update' )
      
    def handleEntityDelete( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of date"""
        self.logger.debug( 'received entity delete signal' )
        if sender != self:
            self.refresh()
      
    def handleEntityCreate( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of date"""
        self.logger.debug( 'received entity create signal' )
        if sender != self:
            self.refresh()
      
    def setRowCount( self, rows ):
        """Callback method to set the number of rows
        @param rows the new number of rows
        """
        self.rows = rows
        self.emit( QtCore.SIGNAL( 'layoutChanged()' ) )
    
    def getItemDelegate( self ):
        """:return: a DelegateManager for this model, or None if no DelegateManager yet available
        a DelegateManager will be available once the item_delegate_changed signal has been emitted"""
        self.logger.debug( 'getItemDelegate' )
        return self.delegate_manager
    
    def getColumns( self ):
        """@return: the columns as set by the setColumns method"""
        return self._columns
    
    @gui_function
    def setColumns( self, columns ):
        """Callback method to set the columns
    
        @param columns a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the getColumns method of the ElixirAdmin class
        """
        self.logger.debug( 'setColumns' )
        self.column_count = len( columns )
        self._columns = columns
    
        delegate_manager = delegates.DelegateManager()
        delegate_manager.set_columns_desc( columns )
    
        # set a delegate for the vertical header
        delegate_manager.insertColumnDelegate( -1, delegates.PlainTextDelegate(parent = delegate_manager) )
        
        for i, c in enumerate( columns ):
            field_name = c[0]
            self.logger.debug( 'creating delegate for %s' % field_name )
            if 'delegate' in c[1]:
                delegate = c[1]['delegate']( parent = delegate_manager, **c[1] )
                delegate_manager.insertColumnDelegate( i, delegate )
                continue
            elif c[1]['python_type'] == str:
                if c[1]['length']:
                    delegate = delegates.PlainTextDelegate( parent = delegate_manager, maxlength = c[1]['length'] )
                    delegate_manager.insertColumnDelegate( i, delegate )
                else:
                    delegate = delegates.TextEditDelegate( parent = delegate_manager, **c[1] )
                    delegate_manager.insertColumnDelegate( i, delegate )
            else:
                delegate = delegates.PlainTextDelegate(parent = delegate_manager)
                delegate_manager.insertColumnDelegate( i, delegate )
        # Only set the delegate manager when it is fully set up
        self.delegate_manager = delegate_manager
        if not sip.isdeleted( self ):
            self.emit( self.item_delegate_changed_signal )
            self.emit( QtCore.SIGNAL( 'layoutChanged()' ) )
      
    def rowCount( self, index = None ):
        return self.rows
    
    def columnCount( self, index = None ):
        return self.column_count
    
    @gui_function
    def headerData( self, section, orientation, role ):
        """In case the columns have not been set yet, don't even try to get
        information out of them
        """
        if orientation == Qt.Horizontal:
            if section >= self.column_count:
                return QtCore.QAbstractTableModel.headerData( self, section, orientation, role )
            c = self.getColumns()[section]
            
            if role == Qt.DisplayRole:
                return QtCore.QVariant( c[1]['name'] )
              
            elif role == Qt.FontRole:
                if ( 'nullable' in c[1] ) and \
                   ( c[1]['nullable'] == False ):
                    return QtCore.QVariant( self._header_font_required )
                else:
                    return QtCore.QVariant( self._header_font )
                  
            elif role == Qt.SizeHintRole:
                option = QtGui.QStyleOptionViewItem()
                if self.delegate_manager:
                    editor_size = self.delegate_manager.sizeHint( option, self.index( 0, section ) )
                else:
                    editor_size = 0
                if 'minimal_column_width' in c[1]:
                    minimal_column_width = QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, 'A' ).width()*c[1]['minimal_column_width']
                else:
                    minimal_column_width = 0
                editable = True
                if 'editable' in c[1]:
                    editable = c[1]['editable']
                label_size = QtGui.QFontMetrics( self._header_font_required ).size( Qt.TextSingleLine, unicode(c[1]['name']) + ' ' )
                size = max( minimal_column_width, label_size.width() + 10 )
                if editable:
                    size = max( size, editor_size.width() )
                return QtCore.QVariant( QtCore.QSize( size, label_size.height() + 10 ) )
        else:
            if role == Qt.SizeHintRole:
                return QtCore.QVariant( QtCore.QSize( self.iconSize.width() + 8, self.iconSize.height() + 5 ) )
            if role == Qt.DecorationRole:
                return self.form_icon
#      elif role == Qt.DisplayRole:
#        return QtCore.QVariant()
        return QtCore.QAbstractTableModel.headerData( self, section, orientation, role )
    
    @gui_function
    def data( self, index, role ):
        if not index.isValid() or \
           not ( 0 <= index.row() <= self.rowCount( index ) ) or \
           not ( 0 <= index.column() <= self.columnCount( index ) ):
            return QtCore.QVariant()
        if role in ( Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole,):
            data = self._get_row_data( index.row(), role )
            try:
                value = data[index.column()]
                if isinstance( value, DelayedProxy ):
                    value = value()
                    data[index.column()] = value
                if isinstance( value, datetime.datetime ):
                    # Putting a python datetime into a QVariant and returning it to a PyObject seems
                    # to be buggy, therefor we chop the microseconds
                    if value:
                        value = QtCore.QDateTime(value.year, value.month, value.day, value.hour, value.minute, value.second)
                self.logger.debug( 'get data for row %s;col %s; role %s : %s' % ( index.row(), index.column(), role, unicode( value ) ) )
            except KeyError:
                self.logger.error( 'Programming error, could not find data of column %s in %s' % ( index.column(), str( data ) ) )
                value = None
            return QtCore.QVariant( value )
        elif role == Qt.ForegroundRole:
            pass
        elif role == Qt.BackgroundRole:
            data = self._get_row_data( index.row(), role )
            try:
                value = data[index.column()]
            except:
                self.logger.error( 'Programming error, could not find data of column %s in %s' % ( index.column(), str( data ) ) )
                value = None
            if value in (None, ValueLoading):
                return QtCore.QVariant(QtGui.QColor('white'))
            else:
                return QtCore.QVariant(value)
        return QtCore.QVariant()
    
    def setData( self, index, value, role = Qt.EditRole ):
        """Value should be a function taking no arguments that returns the data to
        be set
        
        This function will then be called in the model_thread
        """
        if role == Qt.EditRole:
    
            flushed = ( index.row() not in self.unflushed_rows )
            self.unflushed_rows.add( index.row() )
      
            def make_update_function( row, column, value ):
      
                @model_function
                def update_model_and_cache():
                    attribute, field_attributes = self.getColumns()[column]
                    # if the field is not editable, don't waste any time and get out of here
                    if not field_attributes['editable']:
                        return False
                      
                    from sqlalchemy.exceptions import DatabaseError
                    from sqlalchemy import orm
                    new_value = value()
                    self.logger.debug( 'set data for row %s;col %s' % ( row, column ) )
          
                    if new_value == ValueLoading:
                        return None
                      
                    o = self._get_object( row )
                    if not o:
                        # the object might have been deleted from the collection while the editor
                        # was still open
                        self.logger.debug( 'this object is no longer in the collection' )
                        try:
                            self.unflushed_rows.remove( row )
                        except KeyError:
                            pass
                        return
                    
                    old_value = getattr( o, attribute )
                    changed = ( new_value != old_value )
                    #
                    # In case the attribute is a OneToMany or ManyToMany, we cannot simply compare the
                    # old and new value to know if the object was changed, so we'll
                    # consider it changed anyway
                    #
                    direction = field_attributes.get( 'direction', None )
                    if direction in ( orm.interfaces.MANYTOMANY, orm.interfaces.ONETOMANY ):
                        changed = True
                    if changed and field_attributes['editable'] == True:
                        # update the model
                        model_updated = False
                        try:
                            setattr( o, attribute, new_value )
                            model_updated = True
                        except AttributeError, e:
                            self.logger.error( u"Can't set attribute %s to %s" % ( attribute, unicode( new_value ) ), exc_info = e )
                        except TypeError:
                            # type error can be raised in case we try to set to a collection
                            pass
                        # update the cache
                        row_data = strip_data_from_object( o, self.getColumns() )
                        self.cache[Qt.EditRole].add_data( row, o, row_data )
                        self.cache[Qt.ToolTipRole].add_data( row, o, tool_tips_from_object( o, self.getColumns()) )
                        self.cache[Qt.BackgroundColorRole].add_data( row, o, background_colors_from_object( o, self.getColumns()) )
                        self.cache[Qt.DisplayRole].add_data( row, o, stripped_data_to_unicode( row_data, o, self.getColumns() ) )
                        if self.flush_changes and self.validator.isValid( row ):
                            # save the state before the update
                            try:
                                elixir.session.flush( [o] )
                            except DatabaseError, e:
                                #@todo: when flushing fails, the object should not be removed from the unflushed rows ??
                                self.logger.error( 'Programming Error, could not flush object', exc_info = e )
                            try:
                                self.unflushed_rows.remove( row )
                            except KeyError:
                                pass
                            #
                            # we can only track history if the model was updated, and it was
                            # flushed before, otherwise it has no primary key yet
                            #
                            if model_updated and hasattr(o, 'id') and o.id:
                                #
                                # in case of images or relations, we cannot pickle them
                                #
                                if ( not 'Imag' in old_value.__class__.__name__ ) and not direction:
                                    from camelot.model.memento import BeforeUpdate
                                    from camelot.model.authentication import getCurrentAuthentication
                                    history = BeforeUpdate( model = unicode( self.admin.entity.__name__ ),
                                                           primary_key = o.id,
                                                           previous_attributes = {attribute:old_value},
                                                           authentication = getCurrentAuthentication() )
                  
                                    try:
                                        elixir.session.flush( [history] )
                                    except DatabaseError, e:
                                        self.logger.error( 'Programming Error, could not flush history', exc_info = e )
                        #@todo: update should only be sent remotely when flush was done 
                        self.rsh.sendEntityUpdate( self, o )
                        return ( ( row, 0 ), ( row, len( self.getColumns() ) ) )
                    elif flushed:
                        self.logger.debug( 'old value equals new value, no need to flush this object' )
                        try:
                            self.unflushed_rows.remove( row )
                        except KeyError:
                            pass
              
                return update_model_and_cache
        
            post( make_update_function( index.row(), index.column(), value ), self._emit_changes )
      
        return True
    
    def _emit_changes( self, region ):
        if region:
            self.emit( QtCore.SIGNAL( 'dataChanged(const QModelIndex &, const QModelIndex &)' ),
                       self.index( region[0][0], region[0][1] ), self.index( region[1][0], region[1][1] ) )
      
    def flags( self, index ):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self.getColumns()[index.column()][1]['editable']:
            flags = flags | Qt.ItemIsEditable
        return flags
    
    @model_function
    def _extend_cache( self, offset, limit ):
        """Extend the cache around row"""
        #@TODO : also store the primary key, here we just saved the id
        columns = self.getColumns()
        offset = min( offset, self.rows )
        limit = min( limit, self.rows - offset )
        for i, o in enumerate( self.collection_getter()[offset:offset + limit + 1] ):
            row_data = strip_data_from_object( o, columns )
            self.cache[Qt.EditRole].add_data( i + offset, o, row_data )
            self.cache[Qt.ToolTipRole].add_data( i + offset, o, tool_tips_from_object( o, self.getColumns()) )
            self.cache[Qt.BackgroundColorRole].add_data( i + offset, o, background_colors_from_object( o, self.getColumns()) )
            self.cache[Qt.DisplayRole].add_data( i + offset, o, stripped_data_to_unicode( row_data, o, columns ) )
        return ( offset, limit )
    
    @model_function
    def _get_object( self, row ):
        """Get the object corresponding to row"""
        try:
            # first try to get the primary key out of the cache, if it's not
            # there, query the collection_getter
            return self.cache[Qt.EditRole].get_entity_at_row( row )
        except KeyError:
            pass
        return self.collection_getter()[row]
    
    def _cache_extended( self, interval ):
        offset, limit = interval
        self.rows_under_request.difference_update( set( range( offset, offset + limit ) ) )
        self.emit( QtCore.SIGNAL( 'dataChanged(const QModelIndex &, const QModelIndex &)' ),
                  self.index( offset, 0 ), self.index( offset + limit, self.column_count ) )
    
    def _get_row_data( self, row, role ):
        """Get the data which is to be visualized at a certain row of the
        table, if needed, post a refill request the cache to get the object
        and its neighbours in the cache, meanwhile, return an empty object
        @param role: Qt.EditRole or Qt.DisplayRole 
        """
        role_cache = self.cache[role]
        try:
            return role_cache.get_data_at_row( row )
        except KeyError:
            if row not in self.rows_under_request:
                offset = max( row - self.max_number_of_rows / 2, 0 )
                limit = self.max_number_of_rows
                self.rows_under_request.update( set( range( offset, offset + limit ) ) )
                post( lambda :self._extend_cache( offset, limit ), self._cache_extended )
            return empty_row_data
      
    @model_function
    def remove( self, o ):
        self.collection_getter().remove( o )
        self.rows -= 1
    
    @model_function
    def append( self, o ):
        self.collection_getter().append( o )
        self.rows += 1
    
    @model_function
    def removeEntityInstance( self, o, delete = True ):
        """Remove the entity instance o from this collection
        @param o: the object to be removed from this collection
        @param delete: delete the object after removing it from the collection 
        """
        self.logger.debug( 'remove entity instance')
        self.remove( o )
        # remove the entity from the cache
        self.cache[Qt.DisplayRole].delete_by_entity( o )
        self.cache[Qt.ToolTipRole].delete_by_entity( o )
        self.cache[Qt.BackgroundColorRole].delete_by_entity( o )
        self.cache[Qt.EditRole].delete_by_entity( o )
        if delete:
            self.rsh.sendEntityDelete( self, o )
            self.admin.delete( o )
        else:
            # even if the object is not deleted, it needs to be flushed to make
            # sure it's out of the collection
            self.admin.flush( o )
        post( self.getRowCount, self._refresh_content )
    
    @gui_function
    def removeRow( self, row, delete = True ):
        """Remove the entity associated with this row from this collection
        @param delete: delete the entity as well
        """
        self.logger.debug( 'remove row %s' % row )
    
        def create_delete_function( row ):
    
            def delete_function():
                o = self._get_object( row )
                self.removeEntityInstance( o, delete )
        
            return delete_function
      
        post( create_delete_function( row ) )
        return True
     
    @gui_function 
    def copy_row( self, row ):
        """Copy the entity associated with this row to the end of the collection
        :param row: the row number
        """
        
        def create_copy_function( row ):
            
            def copy_function():
                o = self._get_object(row)
                new_object = self.admin.entity()
                new_object.from_dict( o.to_dict(exclude=['id']) )
                self.insertEntityInstance(self.getRowCount(), new_object)
                
            return copy_function
                
        post( create_copy_function( row ) )
        return True
    
    @model_function
    def insertEntityInstance( self, row, o ):
        """Insert object o into this collection
        :param o: the object to be added to the collection
        :return: the row at which the object was inserted
        """
        self.append( o )
        row = self.getRowCount() - 1
        self.unflushed_rows.add( row )
        if self.flush_changes and not len( self.validator.objectValidity( o ) ):
            elixir.session.flush( [o] )
            try:
                self.unflushed_rows.remove( row )
            except KeyError:
                pass
# TODO : it's not because an object is added to this list, that it was created
# it might as well exist allready, eg. manytomany relation
#      from camelot.model.memento import Create
#      from camelot.model.authentication import getCurrentAuthentication
#      history = Create(model=unicode(self.admin.entity.__name__),
#                       primary_key=o.id,
#                       authentication = getCurrentAuthentication())
#      elixir.session.flush([history])
#      self.rsh.sendEntityCreate(self, o)
        post( self.getRowCount, self._refresh_content )
        return row
    
    @gui_function
    def insertRow( self, row, entity_instance_getter ):
  
        def create_insert_function( getter ):
    
            @model_function
            def insert_function():
                self.insertEntityInstance( row, getter() )
        
            return insert_function
      
        post( create_insert_function( entity_instance_getter ) )
    
    @model_function
    def getData( self ):
        """Generator for all the data queried by this proxy"""
        for _i, o in enumerate( self.collection_getter() ):
            yield strip_data_from_object( o, self.getColumns() )
            
    def get_admin( self ):
        """Get the admin object associated with this model"""
        return self.admin
      
