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
logger = logging.getLogger('camelot.view.proxy.collection_proxy')
verbose = False 

import pickle
import elixir
import datetime
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore

from sqlalchemy.orm.session import Session
from camelot.view.art import Icon
from camelot.view.fifo import fifo
from camelot.view.controls import delegates
from camelot.view.remote_signals import get_signal_handler
from camelot.view.model_thread import gui_function, \
                                      model_function, \
                                      get_model_thread


class DelayedProxy(object):
  """A proxy object needs to be constructed within the GUI thread. Construct
  a delayed proxy when the construction of a proxy is needed within the Model
  thread.  On first occasion the delayed proxy will be converted to a real
  proxy within the GUI thread
  """
  
  @model_function
  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    
  @gui_function
  def __call__(self):
    return CollectionProxy(*self.args, **self.kwargs)
  
@model_function
def RowDataFromObject(obj, columns):
  """Create row data from an object, by fetching its attributes"""
  row_data = []
  mt = get_model_thread()
  
  def create_collection_getter(o, attr):
    return lambda: getattr(o, attr)
  
  for i,col in enumerate(columns):
    field_attributes = col[1]
    if field_attributes['python_type'] == list:
      row_data.append(DelayedProxy(field_attributes['admin'],
                      create_collection_getter(obj, col[0]), 
                      field_attributes['admin'].getColumns))
    else:
      row_data.append(getattr(obj, col[0]))
  return row_data
  
@model_function
def RowDataAsUnicode(obj, columns):
  """Extract for each field in the row data a 'visible' form of 
  data"""
  
  row_data = []
  
  for i,(field_name,field_attributes) in enumerate(columns):
    field_data = getattr(obj, field_name)
    if 'unicode_format' in field_attributes:
        unicode_format = field_attributes['unicode_format']
        if field_data != None:
            row_data.append(unicode_format(field_data))
            continue
    if 'choices' in field_attributes:
      for key,value in field_attributes['choices'](obj):
        if key==field_data:
          row_data.append(value)
          continue
    if isinstance(field_data, list):
      row_data.append(u'.'.join([unicode(e) for e in field_data]))
    elif isinstance(field_data, datetime.datetime):
      # datetime should come before date since datetime is a subtype of date
      if field_data.year >= 1900:
        row_data.append( field_data.strftime('%d/%m/%Y %H:%M') )   
    elif isinstance(field_data, datetime.date):
      if field_data.year >= 1900:
        row_data.append( field_data.strftime('%d/%m/%Y') )
    elif field_data!=None:
      row_data.append(unicode(field_data))
    else:
      row_data.append('')
  
  return row_data

class EmptyRowData(object):
  def __getitem__(self, column):
    return None
  
empty_row_data = EmptyRowData()


class CollectionProxy(QtCore.QAbstractTableModel):
  """The CollectionProxy contains a limited copy of the data in the actual
  collection, usable for fast visualisation in a QTableView 
  """
  
  _header_font = QtGui.QApplication.font()
  _header_font_required = QtGui.QApplication.font()
  _header_font_required.setBold(True)
  header_icon = Icon('tango/16x16/places/folder.png').getQIcon()
  
  @gui_function
  def __init__(self, admin, collection_getter, columns_getter,
               max_number_of_rows=10, edits=None, flush_changes=True):
    """@param admin: the admin interface for the items in the collection

    @param collection_getter: a function that takes no arguments and returns
    the collection that will be visualized. This function will be called inside
    the model thread, to prevent delays when this function causes the database
    to be hit.

    @param columns_getter: a function that takes no arguments and returns the
    columns that will be cached in the proxy. This function will be called
    inside the model thread.
    """
    logger.debug('initialize query table for %s' % (admin.getName()))
    self.logger = logger
    QtCore.QAbstractTableModel.__init__(self)
    self.admin = admin
    self.form_icon = QtCore.QVariant(self.header_icon)
    self.validator = admin.createValidator(self)
    self.collection_getter = collection_getter
    self.column_count = 0
    self.flush_changes = flush_changes
    self.mt = admin.getModelThread()
    # Set database connection and load data
    self.rows = 0
    self._columns = []
    self.max_number_of_rows = max_number_of_rows
    self.cache = {Qt.DisplayRole:fifo(10*self.max_number_of_rows),
                  Qt.EditRole:fifo(10*self.max_number_of_rows)}
    # The rows in the table for which a cache refill is under request
    self.rows_under_request = set()
    # The rows that have unflushed changes
    self.unflushed_rows = set()
    # Set edits
    self.edits = edits or []
    self.rsh = get_signal_handler()
    self.rsh.connect(self.rsh,
                     self.rsh.entity_update_signal,
                     self.handleEntityUpdate)
    self.rsh.connect(self.rsh,
                     self.rsh.entity_delete_signal,
                     self.handleEntityDelete)
    self.rsh.connect(self.rsh,
                     self.rsh.entity_create_signal,
                     self.handleEntityCreate)
    
    def get_columns():
      self._columns = columns_getter()
      return self._columns
    
    self.mt.post(get_columns, lambda columns:self.setColumns(columns))
    # in that way the number of rows is requested as well
    self.mt.post(self.getRowCount,  self.setRowCount)
    logger.debug('initialization finished')
    self.item_delegate = None
    
  def hasUnflushedRows(self):
    """The model has rows that have not been flushed to the database yet,
    because the row is invalid
    """
    return len(self.unflushed_rows) > 0
  
  @model_function
  def getRowCount(self):
    return len(self.collection_getter())
  
  @gui_function
  def revertRow(self, row):
    def create_refresh_entity(row):
      
      @model_function
      def refresh_entity():
        o = self._get_object(row)
        elixir.session.refresh(o)
        return row, o
      
      return refresh_entity

    def refresh(row_and_entity):
      row, entity = row_and_entity
      self.handleRowUpdate(row)
      self.rsh.sendEntityUpdate(self, entity)
      
    self.mt.post(create_refresh_entity(row), refresh)
              
  def refresh(self):
    def refresh_content(rows):
      self.cache = {Qt.DisplayRole: fifo(10*self.max_number_of_rows),
                    Qt.EditRole: fifo(10*self.max_number_of_rows)}
      self.setRowCount(rows)
      
    self.mt.post(self.getRowCount, refresh_content)
    
  def setCollectionGetter(self, collection_getter):
    self.collection_getter = collection_getter
    self.refresh()
    
  def handleRowUpdate(self, row):
    """Handles the update of a row when this row might be out of date"""
    self.cache[Qt.DisplayRole].delete_by_row(row)
    self.cache[Qt.EditRole].delete_by_row(row) 
    sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
    self.emit(QtCore.SIGNAL(sig),
              self.index(row, 0),
              self.index(row, self.column_count))
    
  def handleEntityUpdate(self, sender, entity):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('%s %s received entity update signal' % \
                 (self.__class__.__name__, self.admin.getName()))
    if sender != self:
      row = self.cache[Qt.DisplayRole].delete_by_entity(entity)
      row = self.cache[Qt.EditRole].delete_by_entity(entity)
      if row!=None:
        logger.debug('updated row %i' % row)
        sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
        self.emit(QtCore.SIGNAL(sig),
                  self.index(row, 0),
                  self.index(row, self.column_count))
      else:
        logger.debug('entity not in cache')
    else:
      logger.debug('duplicate update')

  def handleEntityDelete(self, sender, entity, primary_keys):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('received entity delete signal')
    if sender != self:
      self.refresh()
                 
  def handleEntityCreate(self, entity, primary_keys):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('received entity create signal')
    if sender != self:
      self.refresh()
                 
  def setRowCount(self, rows):
    """Callback method to set the number of rows
    @param rows the new number of rows
    """ 
    self.rows = rows
    self.emit(QtCore.SIGNAL('layoutChanged()'))
    
  def getItemDelegate(self):
    logger.debug('getItemDelegate')
    if not self.item_delegate:
      raise Exception('item delegate not yet available')
    return self.item_delegate 
    
  def getColumns(self):
    """@return: the columns as set by the setColumns method"""
    return self._columns
  
  def setColumns(self, columns):
    """Callback method to set the columns

    @param columns a list with fields to be displayed of the form [('field_name', field_attributes), ...] as
    returned by the getColumns method of the ElixirAdmin class
    """

    self.column_count = len(columns)
    self._columns = columns
    
    self.item_delegate = delegates.GenericDelegate()
    self.item_delegate.set_columns_desc(columns)

    for i, c in enumerate(columns):
      field_name = c[0]
      type_ = c[1]['python_type']
      widget_ = c[1]['widget']

      if verbose:
        logger.debug("creating delegate for %s \ntype: %s\nwidget: %s\n" \
                     "arguments: %s" % (field_name, type_, widget_, str(c[1])))
      else:
        logger.debug('creating delegate for %s' % field_name)
      
      if 'delegate' in c[1]:
        delegate = c[1]['delegate'](parent=None, **c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue       
      if 'choices' in c[1]:
        delegate = delegates.ComboBoxColumnDelegate(**c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue
      if widget_ == 'code':
        delegate = delegates.CodeColumnDelegate(c[1]['parts'])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue
      elif widget_ == 'datetime':
        delegate = delegates.DateTimeColumnDelegate(parent=None, **c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif widget_ == 'virtual_address':
        delegate = delegates.VirtualAddressColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue      
      elif widget_ == 'image':
        delegate = delegates. ImageColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue
      elif widget_ == 'richtext':
        delegate = delegates.RichTextColumnDelegate(**c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue  
      elif widget_ == 'many2one':
        entity_admin = c[1]['admin']
        delegate = delegates.Many2OneColumnDelegate(**c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif widget_ == 'one2many':
        delegate = delegates.One2ManyColumnDelegate(**c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == str:
        if c[1]['length']:
          delegate = delegates.PlainTextColumnDelegate(maxlength=c[1]['length'])
          self.item_delegate.insertColumnDelegate(i, delegate)
        else:
          delegate = delegates.TextEditColumnDelegate(**c[1])
          self.item_delegate.insertColumnDelegate(i, delegate)          
      elif type_ == int:
        delegate = delegates.IntegerColumnDelegate(parent=None, **c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == datetime.date:
        delegate = delegates.DateColumnDelegate(format='dd/MM/yyyy',
                                                default=c[1].get('default', None),
                                                nullable=c[1].get('nullable', False))
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == float:
        delegate = delegates.FloatColumnDelegate(-100000.0, 100000.0, **c[1])
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == bool:
        delegate = delegates.BoolColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
      else:
        delegate = delegates.PlainTextColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
    self.emit(QtCore.SIGNAL('layoutChanged()'))

  def rowCount(self, index=None):
    return self.rows
  
  def columnCount(self, index=None):
    return self.column_count
  
  @gui_function
  def headerData(self, section, orientation, role):
    """In case the columns have not been set yet, don't even try to get
    information out of them
    """
    if orientation == Qt.Horizontal:
      if section >= self.column_count:
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
      c = self.getColumns()[section]
      if role == Qt.DisplayRole:
        return QtCore.QVariant(c[1]['name'])
      elif role == Qt.FontRole:
        if ('nullable' in c[1]) and \
           (c[1]['nullable']==False):
          return QtCore.QVariant(self._header_font_required)
        else:
          return QtCore.QVariant(self._header_font)
      elif role == Qt.SizeHintRole:
        option = QtGui.QStyleOptionViewItem()
        editor_size = self.item_delegate.sizeHint(option, self.index(0, section))
        if 'minimal_column_width' in c[1]:
          minimal_column_width = QtGui.QFontMetrics(self._header_font).size(Qt.TextSingleLine, ' ').width()*c[1]['minimal_column_width']
        else:
          minimal_column_width = 0
        label_size = QtGui.QFontMetrics(self._header_font_required).size(Qt.TextSingleLine, c[1]['name']+' ')
        return QtCore.QVariant(QtCore.QSize(max(minimal_column_width, editor_size.width(),label_size.width()+10), label_size.height()+10))
    else:
      if role == Qt.DecorationRole:
        return self.form_icon
      elif role == Qt.DisplayRole:
        return QtCore.QVariant()
    return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
  
  @gui_function
  def data(self, index, role):
    import datetime
    if not index.isValid() or \
       not (0 <= index.row() <= self.rowCount(index)) or \
       not (0 <= index.column() <= self.columnCount(index)):
      return QtCore.QVariant()
    if role in (Qt.DisplayRole, Qt.EditRole):
      data = self._get_row_data(index.row(), role)
      try:
        value = data[index.column()]
        if isinstance(value, DelayedProxy):
          value = value()
          data[index.column()] = value
        if isinstance(value, datetime.datetime):
          # Putting a python datetime into a QVariant and returning it to a PyObject seems
          # to be buggy, therefor we convert it here to a tuple of date and time
          if role==Qt.EditRole and value:
            return QtCore.QVariant((value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond))
      except KeyError:
        logger.error('Programming error, could not find data of column %s in %s'%(index.column(), str(data)))
        value = None
      return QtCore.QVariant(value)
    elif role == Qt.ForegroundRole:
      pass
    elif role == Qt.BackgroundRole:
      pass
    return QtCore.QVariant()

  def setData(self, index, value, role=Qt.EditRole):
    """Value should be a function taking no arguments that returns the data to
    be set
    
    This function will then be called in the model_thread
    """
    if role == Qt.EditRole:
      
      flushed = (index.row() not in self.unflushed_rows)
      self.unflushed_rows.add(index.row())
      
      def make_update_function(row, column, value):
        
        @model_function
        def update_model_and_cache():
          from sqlalchemy.exceptions import OperationalError
          new_value = value()
          if verbose:
            logger.debug('set data for col %s;row %s to %s' % (row, column, new_value))
          else:
            logger.debug('set data for col %s;row %s' % (row, column))
            
          o = self._get_object(row)
          if not o:
            # the object might have been deleted from the collection while the editor
            # was still open
            try:
              self.unflushed_rows.remove(row)
            except KeyError:
              pass
            return            
          attribute, field_attributes = self.getColumns()[column]
          old_value = getattr(o, attribute)
          if new_value!=old_value and field_attributes['editable']==True:
            # update the model
            model_updated = False
            try:
              setattr(o, attribute, new_value)
              model_updated = True
            except AttributeError:
              logger.error("Can't set attribute %s to %s"%(attribute, str(value)))
            except TypeError:
              # type error can be raised in case we try to set to a collection
              pass
            # update the cache
            row_data = RowDataFromObject(o, self.getColumns())
            self.cache[Qt.EditRole].add_data(row, o, row_data)
            self.cache[Qt.DisplayRole].add_data(row, o, RowDataAsUnicode(o, self.getColumns()))
            if self.flush_changes and self.validator.isValid(row):
              # save the state before the update
              try:
                elixir.session.flush([o])
              except OperationalError, e:
                logger.error('Programming Error, could not flush object', exc_info=e)
              try:
                self.unflushed_rows.remove(row)
              except KeyError:
                pass
              if model_updated:
                #
                # in case of images, we cannot pickle them
                #
                if not 'Imag' in old_value.__class__.__name__:
                  from camelot.model.memento import BeforeUpdate
                  from camelot.model.authentication import getCurrentAuthentication
                  history = BeforeUpdate(model=unicode(self.admin.entity.__name__), 
                                         primary_key=o.id, 
                                         previous_attributes={attribute:old_value},
                                         authentication = getCurrentAuthentication())
                  
                  try:
                    elixir.session.flush([history])
                  except OperationalError, e:
                    logger.error('Programming Error, could not flush history', exc_info=e)                  
            #@todo: update should only be sent remotely when flush was done 
            self.rsh.sendEntityUpdate(self, o)
            return ((row,0), (row,len(self.getColumns())))
          elif flushed:
            try:
              self.unflushed_rows.remove(row)
            except KeyError:
              pass
        
        return update_model_and_cache
      
      def emit_changes(region):
        if region:
          self.emit(QtCore.SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), 
                    self.index(region[0][0],region[0][1]), self.index(region[1][0],region[1][1]))
      
      self.mt.post(make_update_function(index.row(), index.column(), value), emit_changes)
    
    return True
  
  def flags(self, index):
    flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
    if self.getColumns()[index.column()][1]['editable']:
     flags = flags | Qt.ItemIsEditable
    return flags

  @model_function
  def _extend_cache(self, offset, limit):
    """Extend the cache around row"""
    #@TODO : also store the primary key, here we just saved the id
    columns = self.getColumns()
    offset = min(offset, self.rows)
    limit = min(limit, self.rows-offset)
    for i,o in enumerate(self.collection_getter()[offset:offset+limit+1]):
      row_data = RowDataFromObject(o, columns)
      self.cache[Qt.EditRole].add_data(i+offset, o, row_data)
      self.cache[Qt.DisplayRole].add_data(i+offset, o, RowDataAsUnicode(o, columns))
    return (offset, limit)
        
  @model_function
  def _get_object(self, row):
    """Get the object corresponding to row"""
    try:
      # first try to get the primary key out of the cache, if it's not
      # there, query the collection_getter
      return self.cache[Qt.EditRole].get_entity_at_row(row)
    except KeyError:
      pass
    return self.collection_getter()[row]
  
  def _cache_extended(self, offset, limit):
    self.rows_under_request.difference_update(set(range(offset, offset+limit)))
    self.emit(QtCore.SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
              self.index(offset,0), self.index(offset+limit,self.column_count))
    
  def _get_row_data(self, row, role):
    """Get the data which is to be visualized at a certain row of the
    table, if needed, post a refill request the cache to get the object
    and its neighbours in the cache, meanwhile, return an empty object
    @param role: Qt.EditRole or Qt.DisplayRole 
    """
    role_cache = self.cache[role]
    try:
      return role_cache.get_data_at_row(row)
    except KeyError:
      if row not in self.rows_under_request:
        offset = max(row-self.max_number_of_rows/2,0)
        limit = self.max_number_of_rows
        self.rows_under_request.update(set(range(offset, offset+limit)))
        self.mt.post(lambda :self._extend_cache(offset, limit),
                     lambda interval:self._cache_extended(*interval))
      return empty_row_data

  @model_function
  def remove(self, o):
    self.collection_getter().remove(o)
    self.rows -= 1
    
  @model_function
  def append(self, o):
    self.collection_getter().append(o)
    self.rows += 1
 
  @model_function
  def removeEntityInstance(self, o):
    logger.debug('remove entity instance with id %s' % o.id)
    self.remove(o)
    # remove the entity from the cache
    self.cache[Qt.DisplayRole].delete_by_entity(o)
    self.cache[Qt.EditRole].delete_by_entity(o)
    self.rsh.sendEntityDelete(self, o)
    if o.id:
      pk = o.id
      # save the state before the update
      from camelot.model.memento import BeforeDelete
      from camelot.model.authentication import getCurrentAuthentication
      history = BeforeDelete(model=unicode(self.admin.entity.__name__), 
                             primary_key=pk, 
                             previous_attributes={},
                             authentication = getCurrentAuthentication())
      logger.debug('delete the object')
      o.delete()
      Session.object_session(o).flush([o])
      Session.object_session(history).flush([history])
    self.mt.post(lambda:None, lambda *args:self.refresh())  
    
  @gui_function
  def removeRow(self, row):
    logger.debug('remove row %s' % row)
    
    def create_delete_function(row):
      
      def delete_function():
        o = self._get_object(row)
        self.removeEntityInstance(o)
      
      return delete_function
  
    self.mt.post(create_delete_function(row))
    return True
    
  @model_function
  def insertEntityInstance(self, row, o):
    self.append(o)
    row = self.getRowCount()-1
    self.unflushed_rows.add(row)
    if self.flush_changes and not len(self.validator.objectValidity(o)):
      elixir.session.flush([o])
      try:
        self.unflushed_rows.remove(row)
      except KeyError:
        pass
      from camelot.model.memento import Create
      from camelot.model.authentication import getCurrentAuthentication
      history = Create(model=unicode(self.admin.entity.__name__),
                       primary_key=o.id,
                       authentication = getCurrentAuthentication())
      elixir.session.flush([history])
      self.rsh.sendEntityCreate(self, o)
    self.mt.post(lambda:None, lambda *args:self.refresh())
              
  @gui_function
  def insertRow(self, row, entity_instance_getter):
    
    def create_insert_function(getter):
      
      @model_function
      def insert_function():
        self.insertEntityInstance(row, getter())
          
      return insert_function
  
    self.mt.post(create_insert_function(entity_instance_getter))
        
  def __del__(self):
    logger.warn('delete CollectionProxy')
