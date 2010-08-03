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
from PyQt4.QtCore import Qt, QThread
from PyQt4 import QtGui, QtCore
import sip

from camelot.view.art import Icon
from camelot.view.fifo import Fifo
from camelot.view.controls import delegates
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import gui_function, \
                                      model_function, post

class ProxyDict(dict):
    """Subclass of dictionary to fool the QVariant object and prevent
    it from converting dictionary keys to whatever Qt object, but keep
    everything python"""
    pass

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
        try:
            getter = field_attributes['getter']
            if field_attributes['python_type'] == list:
                row_data.append( DelayedProxy( field_attributes['admin'],
                                create_collection_getter( obj, col[0] ),
                                field_attributes['admin'].get_columns ) )
            else:
                row_data.append( getter( obj ) )
        except Exception, e:
            logger.error('ProgrammingError : could not get attribute %s of object of type %s'%(col[0], obj.__class__.__name__),
                         exc_info=e)
            row_data.append( None )
    return row_data

@model_function
def stripped_data_to_unicode( stripped_data, obj, static_field_attributes, dynamic_field_attributes ):
    """Extract for each field in the row data a 'visible' form of
    data"""

    row_data = []

    for field_data, static_attributes, dynamic_attributes in zip( stripped_data, static_field_attributes, dynamic_field_attributes ):
        unicode_data = u''
        choices = dynamic_attributes.get( 'choices', static_attributes.get('choices', None))
        if 'unicode_format' in static_attributes:
            unicode_format = static_attributes['unicode_format']
            if field_data != None:
                unicode_data = unicode_format( field_data )
        elif choices:
            unicode_data = field_data
            for key, value in choices:
                if key == field_data:
                    unicode_data = value
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

empty_row_data = EmptyRowData()

class SortingRowMapper( dict ):
    """Class mapping rows of a collection 1:1 without sorting
    and filtering, unless a mapping has been defined explicitly"""

    def __getitem__(self, row):
        try:
            return super(SortingRowMapper, self).__getitem__(row)
        except KeyError:
            return row

class CollectionProxy( QtCore.QAbstractTableModel ):
    """The CollectionProxy contains a limited copy of the data in the actual
    collection, usable for fast visualisation in a QTableView

    the CollectionProxy has some class attributes that can be overwritten when
    subclassing it :

    * header_icon : the icon to be used in the vertical header

    """

    _header_font = QtGui.QApplication.font()
    _header_font_required = QtGui.QApplication.font()
    _header_font_required.setBold( True )

    header_icon = Icon( 'tango/16x16/places/folder.png' )

    item_delegate_changed_signal = QtCore.SIGNAL('itemDelegateChanged')
    rows_removed_signal = QtCore.SIGNAL('rowsRemoved(const QModelIndex&,int,int)')

    @gui_function
    def __init__( self, admin, collection_getter, columns_getter,
                 max_number_of_rows = 10, edits = None, flush_changes = True ):
        """@param admin: the admin interface for the items in the collection

        @param collection_getter: a function that takes no arguments and returns
        the collection that will be visualized. This function will be called inside
        the model thread, to prevent delays when this function causes the database
        to be hit.  If the collection is a list, it should not contain any duplicate
        elements.

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
        if self.header_icon:
            self.form_icon = QtCore.QVariant( self.header_icon.getQIcon().pixmap( self.iconSize ) )
        else:
            self.form_icon = QtCore.QVariant()
        self.validator = admin.create_validator( self )
        self.collection_getter = collection_getter
        self.column_count = 0
        self.flush_changes = flush_changes
        self.delegate_manager = None
        self.mt = get_model_thread()
        # Set database connection and load data
        self._rows = 0
        self._columns = []
        self._static_field_attributes = []
        self.max_number_of_rows = max_number_of_rows
        self.display_cache = Fifo( 10 * self.max_number_of_rows )
        self.edit_cache = Fifo( 10 * self.max_number_of_rows )
        self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        # The rows in the table for which a cache refill is under request
        self.rows_under_request = set()
        # The rows that have unflushed changes
        self.unflushed_rows = set()
        self._sort_and_filter = SortingRowMapper()
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
            self._static_field_attributes = list(self.admin.get_static_field_attributes([c[0] for c in self._columns]))
            return self._columns

        post( get_columns, self.setColumns )
#    # the initial collection might contain unflushed rows
        post( self.updateUnflushedRows )
#    # in that way the number of rows is requested as well
        post( self.getRowCount, self.setRowCount )
        self.logger.debug( 'initialization finished' )

    def get_validator(self):
        return self.validator

    def map_to_source(self, sorted_row_number):
        """Converts a sorted row number to a row number of the source
        collection"""
        return self._sort_and_filter[sorted_row_number]

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
        # make sure we don't count an object twice if it is twice
        # in the list, since this will drive the cache nuts
        rows = len( set( self.collection_getter() ) )
        return rows

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
        self.display_cache = Fifo( 10 * self.max_number_of_rows )
        self.edit_cache = Fifo( 10 * self.max_number_of_rows )
        self.attributes_cache = Fifo( 10 * self.max_number_of_rows )
        self.rows_under_request = set()
        self.unflushed_rows = set()
        self.setRowCount( rows )

    def set_collection_getter( self, collection_getter ):
        self.logger.debug('set collection getter')
        self.collection_getter = collection_getter
        self.refresh()

    def get_collection_getter( self ):
        return self.collection_getter

    def handleRowUpdate( self, row ):
        """Handles the update of a row when this row might be out of date"""
        self.display_cache.delete_by_row( row )
        self.edit_cache.delete_by_row( row )
        self.attributes_cache.delete_by_row( row )
        sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
        self.emit( QtCore.SIGNAL( sig ),
                  self.index( row, 0 ),
                  self.index( row, self.column_count ) )

    def handleEntityUpdate( self, sender, entity ):
        """Handles the entity signal, indicating that the model is out of date"""
        self.logger.debug( '%s %s received entity update signal' % \
                     ( self.__class__.__name__, self.admin.get_verbose_name() ) )
        if sender != self:
            try:
                row = self.display_cache.get_row_by_entity(entity)
            except KeyError:
                self.logger.debug( 'entity not in cache' )
                return
            #
            # Because the entity is updated, it might no longer be in our
            # collection, therefore, make sure we don't access the collection
            # to strip data of the entity
            #
            def create_entity_update(row, entity):

                def entity_update():
                    columns = self.getColumns()
                    self._add_data(columns, row, entity)
                    return ((row,0), (row,self.column_count))

                return entity_update

            post(create_entity_update(row, entity), self._emit_changes)
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
        self._rows = rows
        if not sip.isdeleted(self):
            self.emit( QtCore.SIGNAL( 'layoutChanged()' ) )

    def getItemDelegate( self ):
        """:return: a DelegateManager for this model, or None if no DelegateManager yet available
        a DelegateManager will be available once the item_delegate_changed signal has been emitted"""
        self.logger.debug( 'getItemDelegate' )
        return self.delegate_manager

    def getColumns( self ):
        """:return: the columns as set by the setColumns method"""
        return self._columns

    @gui_function
    def setColumns( self, columns ):
        """Callback method to set the columns

        :param columns: a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
        returned by the getColumns method of the ElixirAdmin class
        """
        self.logger.debug( 'setColumns' )
        self.column_count = len( columns )
        self._columns = columns

        delegate_manager = delegates.DelegateManager()
        delegate_manager.set_columns_desc( columns )

        # set a delegate for the vertical header
        delegate_manager.insertColumnDelegate( -1, delegates.PlainTextDelegate(parent = delegate_manager) )

        #
        # this loop can take a while to complete, so processEvents is called regulary
        #
        for i, c in enumerate( columns ):
#            if i%10==0:
#                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeSocketNotifiers, 100)
            field_name = c[0]
            self.logger.debug( 'creating delegate for %s' % field_name )
            if 'delegate' in c[1]:
                try:
                    delegate = c[1]['delegate']( parent = delegate_manager, **c[1] )
                except Exception, e:
                    logger.error('ProgrammingError : could not create delegate for field %s'%field_name, exc_info=e)
                    delegate = delegates.PlainTextDelegate( parent = delegate_manager, **c[1] )
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
        return self._rows

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
                return QtCore.QVariant( unicode(c[1]['name']) )

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
                    editor_size = QtCore.QSize(0, 0)
                if 'minimal_column_width' in c[1]:
                    minimal_column_width = QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, 'A' ).width()*c[1]['minimal_column_width']
                else:
                    minimal_column_width = 100
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
                height = self.iconSize.height() + 5
                if self.header_icon:
                    return QtCore.QVariant( QtCore.QSize( self.iconSize.width() + 10, height ) )
                else:
                    # if there is no icon, the line numbers will be displayed, so create some space for those
                    return QtCore.QVariant( QtCore.QSize( QtGui.QFontMetrics( self._header_font ).size( Qt.TextSingleLine, str(self._rows) ).width() + 10, height) )
            if role == Qt.DecorationRole:
                return self.form_icon
#      elif role == Qt.DisplayRole:
#        return QtCore.QVariant()
        return QtCore.QAbstractTableModel.headerData( self, section, orientation, role )

    @gui_function
    def sort( self, column, order ):
        """reimplementation of the QAbstractItemModel its sort function"""

        def create_sort(column, order):

            def sort():
                unsorted_collection = [(i,o) for i,o in enumerate(self.collection_getter())]
                key = lambda item:getattr(item[1], self._columns[column][0])
                unsorted_collection.sort(key=key, reverse=order)
                for j,(i,_o) in enumerate(unsorted_collection):
                    self._sort_and_filter[j] = i
                return len(unsorted_collection)

            return sort

        post(create_sort(column, order), self._refresh_content)

    @gui_function
    def data( self, index, role ):
        """:return: the data at index for the specified role
        This function will return ValueLoading when the data has not
        yet been fetched from the underlying model.  It will then send
        a request to the model thread to fetch this data.  Once the data
        is readily available, the dataChanged signal will be emitted

        Using Qt.UserRole as a role will return all the field attributes
        of the index.
        """
        if not index.isValid() or \
           not ( 0 <= index.row() <= self.rowCount( index ) ) or \
           not ( 0 <= index.column() <= self.columnCount( index ) ):
            return QtCore.QVariant()
        if role in (Qt.EditRole, Qt.DisplayRole):
            if role == Qt.EditRole:
                cache = self.edit_cache
            else:
                cache = self.display_cache
            data = self._get_row_data( index.row(), cache )
            value = data[index.column()]
            if isinstance( value, DelayedProxy ):
                value = value()
                data[index.column()] = value
            if isinstance( value, datetime.datetime ):
                # Putting a python datetime into a QVariant and returning
                # it to a PyObject seems to be buggy, therefor we chop the
                # microseconds
                if value:
                    value = QtCore.QDateTime(value.year, value.month,
                                             value.day, value.hour,
                                             value.minute, value.second)
            return QtCore.QVariant( value )
        elif role == Qt.ToolTipRole:
            return QtCore.QVariant(self._get_field_attribute_value(index, 'tooltip'))
        elif role == Qt.BackgroundRole:
            return QtCore.QVariant(self._get_field_attribute_value(index, 'background_color') or QtGui.QColor('white'))
        elif role == Qt.UserRole:
            field_attributes = ProxyDict(self._static_field_attributes[index.column()])
            dynamic_field_attributes = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if dynamic_field_attributes != ValueLoading:
                field_attributes.update( dynamic_field_attributes )
            return QtCore.QVariant(field_attributes)
        return QtCore.QVariant()

    def _get_field_attribute_value(self, index, field_attribute):
        """Get the values for the static and the dynamic field attributes at once
        :return: the value of the field attribute"""
        try:
            return self._static_field_attributes[index.column()][field_attribute]
        except KeyError:
            value = self._get_row_data( index.row(), self.attributes_cache )[index.column()]
            if value == ValueLoading:
                return None
            return value.get(field_attribute, None)

    def setData( self, index, value, role = Qt.EditRole ):
        """Value should be a function taking no arguments that returns the data to
        be set

        This function will then be called in the model_thread
        """
        if role == Qt.EditRole:

            # if the field is not editable, don't waste any time and get out of here
            if not self._get_field_attribute_value(index, 'editable'):
                return

            flushed = ( index.row() not in self.unflushed_rows )
            self.unflushed_rows.add( index.row() )

            def make_update_function( row, column, value ):

                @model_function
                def update_model_and_cache():
                    attribute, field_attributes = self.getColumns()[column]

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
                    if changed:
                        # update the model
                        model_updated = False
                        try:
                            setattr( o, attribute, new_value )
                            #
                            # setting this attribute, might trigger a default function to return a value,
                            # that was not returned before
                            #
                            self.admin.set_defaults( o, include_nullable_fields=False )
                            model_updated = True
                        except AttributeError, e:
                            self.logger.error( u"Can't set attribute %s to %s" % ( attribute, unicode( new_value ) ), exc_info = e )
                        except TypeError:
                            # type error can be raised in case we try to set to a collection
                            pass
                        if self.flush_changes and self.validator.isValid( row ):
                            # save the state before the update
                            try:
                                self.admin.flush( o )
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
                        # update the cache
                        self._add_data(self.getColumns(), row, o)
                        #@todo: update should only be sent remotely when flush was done
                        self.rsh.sendEntityUpdate( self, o )
                        for depending_obj in self.admin.get_depending_objects( o ):
                            self.rsh.sendEntityUpdate( self, depending_obj )
                        return ( ( row, 0 ), ( row, len( self.getColumns() ) ) )
                    elif flushed:
                        self.logger.debug( 'old value equals new value, no need to flush this object' )
                        try:
                            self.unflushed_rows.remove( row )
                        except KeyError:
                            pass

                return update_model_and_cache

            post( make_update_function( index.row(), index.column(), value ) )

        return True

    def _emit_changes( self, region ):
        if region:
            self.emit( QtCore.SIGNAL( 'dataChanged(const QModelIndex &, const QModelIndex &)' ),
                       self.index( region[0][0], region[0][1] ), self.index( region[1][0], region[1][1] ) )

    def flags( self, index ):
        """Returns the item flags for the given index"""
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self._get_field_attribute_value(index, 'editable'):
            flags = flags | Qt.ItemIsEditable
        return flags

    def _add_data(self, columns, row, obj):
        """Add data from object o at a row in the cache
        :param columns: the columns of which to strip data
        :param row: the row in the cache into which to add data
        :param obj: the object from which to strip the data
        """
        row_data = strip_data_from_object( obj, columns )

        dynamic_field_attributes = list(self.admin.get_dynamic_field_attributes( obj, (c[0] for c in columns)))
        static_field_attributes = self.admin.get_static_field_attributes( (c[0] for c in columns) )
        self.edit_cache.add_data( row, obj, row_data )
        self.display_cache.add_data( row, obj, stripped_data_to_unicode( row_data, obj, static_field_attributes, dynamic_field_attributes ) )
        self.attributes_cache.add_data(row, obj, dynamic_field_attributes )
        self.emit( QtCore.SIGNAL( 'dataChanged(const QModelIndex &, const QModelIndex &)' ),
                  self.index( row, 0 ), self.index( row, self.column_count ) )

    def _skip_row(self, row, obj):
        """:return: True if the object obj is allready in the cache, but at a
        different row then row.  If this is the case, this object should not
        be put in the cache at row, and this row should be skipped alltogether.
        """
        try:
            return self.edit_cache.get_row_by_entity(obj)!=row
        except KeyError:
            pass
        return False

    def _offset_and_limit_rows_to_get( self ):
        """From the current set of rows to get, find the first
        continuous range of rows that should be fetched.
        :return: (offset, limit)
        """
        offset, limit, previous_length, i = 0, 0, 0, 0
        #
        # wait for a while until the rows under request don't change any
        # more
        #
        while previous_length != len(self.rows_under_request):
            previous_length = len(self.rows_under_request)
            QThread.msleep(5)
        #
        # now filter out all rows that have been put in the cache
        # the gui thread didn't know about
        #
        rows_to_get = self.rows_under_request
        rows_allready_there = set()
        for row in rows_to_get:
            if self.edit_cache.has_data_at_row(row):
                rows_allready_there.add(row)
        rows_to_get.difference_update( rows_allready_there )
        #
        # see if there is anything left to do
        #
        if rows_to_get:
            rows_to_get = list(rows_to_get)
            rows_to_get.sort()
            offset = rows_to_get[0]
            #
            # find first discontinuity
            #
            for i in range(offset, rows_to_get[-1]+1):
                if rows_to_get[i-offset] != i:
                    break
            limit = i - offset + 1
        return (offset, limit)

    @model_function
    def _extend_cache( self ):
        """Extend the cache around the rows under request"""
        offset, limit = self._offset_and_limit_rows_to_get()
        if limit:
            columns = self.getColumns()
            collection = self.collection_getter()
            skipped_rows = 0
            for i in range(offset, min(offset + limit + 1, self._rows)):
                object_found = False
                while not object_found:
                    unsorted_row = self._sort_and_filter[i]
                    obj = collection[unsorted_row+skipped_rows]
                    if self._skip_row(i, obj):
                        skipped_rows = skipped_rows + 1
                    else:
                        self._add_data(columns, i, obj)
                        object_found = True
        return ( offset, limit )

    @model_function
    def _get_object( self, sorted_row_number ):
        """Get the object corresponding to row
        :return: the object at row row or None if the row index is invalid
        """
        try:
            # first try to get the primary key out of the cache, if it's not
            # there, query the collection_getter
            return self.edit_cache.get_entity_at_row( sorted_row_number )
        except KeyError:
            pass
        try:
            return self.collection_getter()[self.map_to_source(sorted_row_number)]
        except IndexError:
            pass
        return None

    def _cache_extended( self, interval ):
        offset, limit = interval
        self.rows_under_request.difference_update( set( range( offset, offset + limit + 1) ) )

    def _get_row_data( self, row, cache ):
        """Get the data which is to be visualized at a certain row of the
        table, if needed, post a refill request the cache to get the object
        and its neighbours in the cache, meanwhile, return an empty object
        :param row: the row of the table for which to get the data
        :param cache: the cache out of which to get row data
        :return: row_data
        """
        try:
            return cache.get_data_at_row( row )
        except KeyError:
            if row not in self.rows_under_request:
                self.rows_under_request.add( row )
                post( self._extend_cache, self._cache_extended )
            return empty_row_data

    @model_function
    def remove( self, o ):
        self.collection_getter().remove( o )
        self._rows -= 1

    @model_function
    def append( self, o ):
        self.collection_getter().append( o )
        self._rows += 1

    @model_function
    def removeEntityInstance( self, o, delete = True ):
        """Remove the entity instance o from this collection
        @param o: the object to be removed from this collection
        @param delete: delete the object after removing it from the collection
        """
        self.logger.debug( 'remove entity instance')
        #
        # it might be impossible to determine the depending objects once
        # the object has been removed from the collection
        #
        depending_objects = list( self.admin.get_depending_objects( o ) )
        self.remove( o )
        # remove the entity from the cache
        self.display_cache.delete_by_entity( o )
        self.attributes_cache.delete_by_entity( o )
        self.edit_cache.delete_by_entity( o )
        if delete:
            self.rsh.sendEntityDelete( self, o )
            self.admin.delete( o )
        else:
            # even if the object is not deleted, it needs to be flushed to make
            # sure it's out of the collection
            self.admin.flush( o )
        for depending_obj in depending_objects:
            self.rsh.sendEntityUpdate( self, depending_obj )
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
                if o:
                    self.removeEntityInstance( o, delete )
                else:
                    # The object is not in this collection, maybe
                    # it was allready deleted, issue a refresh anyway
                    post( self.getRowCount, self._refresh_content )

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
                new_object = self.admin.copy( o )
                self.insertEntityInstance(self.getRowCount(), new_object)

            return copy_function

        post( create_copy_function( row ) )
        return True

    @model_function
    def insertEntityInstance( self, row, o ):
        """Insert object o into this collection, set the possible defaults and flush
        the object if possible/needed
        :param o: the object to be added to the collection
        :return: the row at which the object was inserted
        """
        self.append( o )
        # defaults might depend on object being part of a collection
        self.admin.set_defaults( o )
        row = self.getRowCount() - 1
        self.unflushed_rows.add( row )
        for depending_obj in self.admin.get_depending_objects( o ):
            self.rsh.sendEntityUpdate( self, depending_obj )
        if self.flush_changes and not len( self.validator.objectValidity( o ) ):
            self.admin.flush( o )
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

