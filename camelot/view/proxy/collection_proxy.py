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

"""
Proxy representing a collection of entities that live in the model thread.

The proxy represents them in the gui thread and provides access to the data
with zero delay.  If the data is not yet present in the proxy, dummy data is
returned and an update signal is emitted when the correct data is available.
"""
import logging

logger = logging.getLogger('proxy.collection_proxy')
logger.setLevel(logging.DEBUG)

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from camelot.view.remote_signals import get_signal_handler
from camelot.view import art
from camelot.view.model_thread import model_function
   
@model_function
def RowDataFromObject(obj, columns):
  """Create row data from an object, by fetching its attributes"""
  row_data = []
  
  def create_collection_getter(o,attr):
    return lambda:getattr(o,attr)
  
  for col in columns:
    field_attributes = col[1]
    if field_attributes['python_type']==list:
      row_data.append( CollectionProxy(field_attributes['admin'], create_collection_getter(obj,col[0]),
                                       field_attributes['admin'].getColumns) )
    else:
      row_data.append(getattr(obj,col[0]))
  return row_data
  
def RowDataAsUnicode(row_data):
  import datetime

  def unicode_or_none(data):
    if data:
      if isinstance(data, list):
        return '.'.join(data)
      elif isinstance(data, datetime.date):
        if data.year>=1900:
          return data.strftime('%d/%m/%Y')
      return unicode(data)
    return data
  
  return [unicode_or_none(col) for col in row_data]

class EmptyRowData(object):
  def __getitem__(self, column):
    return None
  
empty_row_data = EmptyRowData()
form_icon = QtCore.QVariant(QtGui.QIcon(art.icon16('places/folder')))

class fifo(object):
  """fifo, is the actual cache containing a limited set of copies of row data
  so the data in fifo, is always immediately accessible to the gui thread,
  with zero delay as you scroll down the table view, fifo is filled and
  refilled with data queried from the database
  
  the cache can be queried either by the row number or by the primary key
  of the object represented by the row data.
  """
  def __init__(self, max_entries):
    self.max_entries = max_entries
    self.primary_keys = []
    self.data_by_rows = dict()
    self.rows_by_primary_keys = dict()
  def add_data(self, row, primary_key, value):
    try:
      row = self.delete_by_primary_key(primary_key)
    except KeyError:
      pass   
    self.data_by_rows[row] = (primary_key, value)
    self.rows_by_primary_keys[primary_key] = row
    self.primary_keys.append(primary_key)
    if len(self.primary_keys)>self.max_entries:
      primary_key = self.primary_keys.pop(0)
      row = self.rows_by_primary_keys[primary_key]
      del self.data_by_rows[row]
      del self.rows_by_primary_keys[primary_key]
  def delete_by_primary_key(self, primary_key):
    row = self.rows_by_primary_keys[primary_key]
    self.primary_keys.remove(primary_key)
    del self.data_by_rows[row]
    del self.rows_by_primary_keys[primary_key]
    return row    
  def get_data_at_row(self, row):
    return self.data_by_rows[row][1]
  def get_row_by_primary_key(self, primary_key):
    return self.rows_by_primary_keys[primary_key]
  def get_primary_key_at_row(self, row):
    return self.data_by_rows[row][0]
      
class CollectionProxy(QtCore.QAbstractTableModel):
  """The CollectionProxy contains a limited copy of the data in the actual collection,
  usable for fast visualisation in a QTableView 
  """
  
  def __init__(self, admin, collection_getter, columns_getter, max_number_of_rows=10, edits=None, flush_changes=True):
    """"
    @param admin: the admin interface for the items in the collection
    @param collection_getter: a function that takes no arguments and returns the collection
    that will be visualized.  This function will be called inside the model thread, to prevent
    delays when this function causes the database to be hit.
    @param columns_getter: a function that takes no arguments and returns the columns that will
    be cached in the proxy.  This function will be called inside the model thread.
    """
    self.logger = logger
    logger.debug('initialize query table for %s'%(admin.getName()))
    QtCore.QAbstractTableModel.__init__(self)
    self.admin = admin
    self.validator = admin.createValidator(self)
    self.collection_getter = collection_getter
    self.column_count = 0
    self.flush_changes = flush_changes
    self.mt = admin.getModelThread()
    # Set database connection and load data
    self.rows = 0
    self.columns_getter = columns_getter
    self.max_number_of_rows = max_number_of_rows
    self.cache = {Qt.DisplayRole:fifo(10*self.max_number_of_rows), Qt.EditRole:fifo(10*self.max_number_of_rows)}
    # The rows in the table for which a cache refill is under request
    self.rows_under_request = set()
    # The rows that have unflushed changes
    self.unflushed_rows = set()
    # Set edits
    self.edits = edits or []
    self.rsh = get_signal_handler()
    self.rsh.connect(self.rsh, self.rsh.entity_update_signal, self.handleEntityUpdate)
    self.rsh.connect(self.rsh, self.rsh.entity_delete_signal, self.handleEntityDelete)
    self.rsh.connect(self.rsh, self.rsh.entity_create_signal, self.handleEntityCreate)
    self.mt.post(columns_getter, lambda columns:self.setColumns(columns))
    # in that way the number of rows is requested as well
    self.mt.post(self._getRowCount,  self.setRowCount)
    logger.debug('initialization finished')
    self.item_delegate = None
    
  def hasUnflushedRows(self):
    """The model has rows that have not been flushed to the database yet, because the row
    is invalid"""
    return len(self.unflushed_rows)>0
  
  @model_function
  def _getRowCount(self):
    return len(self.collection_getter())
  
  def refresh(self):
    
    def refresh_content(rows):
      self.cache = {Qt.DisplayRole:fifo(10*self.max_number_of_rows), Qt.EditRole:fifo(10*self.max_number_of_rows)}
      self.setRowCount(rows)
      
    self.mt.post(self._getRowCount, refresh_content )
    
  def setCollectionGetter(self, collection_getter):
    self.collection_getter = collection_getter
    self.refresh()
    
  def handleEntityUpdate(self, entity, primary_keys):
    """Handles the entity signal, indicating that the model is out of date"""
    if entity is self.admin.entity:
      logger.debug('received entity update signal for %s : %s'%(entity.__name__, str(primary_keys)))
      for pk in primary_keys:
        try:
          row = self.cache[Qt.DisplayRole].delete_by_primary_key(pk)
          row = self.cache[Qt.EditRole].delete_by_primary_key(pk)
          logger.debug('update row %i'%row)
          self.emit(QtCore.SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.index(row,0), self.index(row,self.column_count))
        except KeyError:
          pass

  def handleEntityDelete(self, entity, primary_keys):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('received entity delete signal')
    self.refresh()
                 
  def handleEntityCreate(self, entity, primary_keys):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('received entity create signal')
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
      raise Exception('Item delegate not yet available')
    return self.item_delegate 
    
  def getColumns(self):
    return self.columns_getter()
  
  def setColumns(self, columns):
    """
    Callback method to set the columns
    @param columns a list with fields to be displayed
    """

    self.column_count = len(columns)
    logger.debug('setting up custom delegates')
    
    from camelot.view.controls import delegates
    import datetime
    
    self.item_delegate = delegates.GenericDelegate()
    self.item_delegate.set_columns_desc(columns)

    for i, c in enumerate(columns):
      
      field_name = c[0]
      type_ = c[1]['python_type']
      widget_ = c[1]['widget']

      logger.debug('%s : creating delegate for type %s, using widget %s' % \
                   (field_name, type_, widget_))
      
      if widget_ == 'code':
        delegate = delegates.CodeColumnDelegate(c[1]['parts'])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue        
      if widget_ == 'image':
        delegate = delegates. ImageColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue   
      if widget_ == 'many2one':
        entity_admin = c[1]['admin']
        delegate = delegates.Many2OneColumnDelegate(entity_admin)
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif widget_ == 'one2many':
        entity_admin = c[1]['admin']
        delegate = delegates.One2ManyColumnDelegate(entity_admin, field_name)
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == str:
        delegate = delegates.PlainTextColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == int:
        delegate = delegates.IntegerColumnDelegate(0, 100000)
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == datetime.date:
        delegate = delegates.DateColumnDelegate(format='dd/MM/yyyy',
                                                default=c[1].get('default', None),
                                                nullable=c[1].get('nullable', False))
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == float:
        delegate = delegates.FloatColumnDelegate(-100000.0, 100000.0)
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
  
  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole:
      if orientation == Qt.Horizontal:
        return QtCore.QVariant(self.columns_getter()[section][1]['name'])
      elif orientation == Qt.Vertical:
        #return QtCore.QVariant(int(section+1))
        # we don't want anything to be displayed
        return QtCore.QVariant()
    if role == Qt.FontRole:
      if orientation == Qt.Horizontal:
        font = QtGui.QApplication.font()
        if ('nullable' in self.columns_getter()[section][1]) and \
           (self.columns_getter()[section][1]['nullable']==False):
          font.setBold(True)
          return QtCore.QVariant(font)
        else:
          font.setBold(False)
          return QtCore.QVariant(font)
    if role == Qt.DecorationRole:
      if orientation == Qt.Vertical:
        return form_icon 
    return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
  
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
      except KeyError:
        logger.error('Programming error, could not find data of column %s in %s'%(index.column(), str(data)))
        value = None
      return QtCore.QVariant(value)
    elif role == Qt.SizeHintRole:
      c = self.columns_getter()[index.column()] 
      type_ = c[1]['python_type'] 
      widget_ = c[1]['widget'] 
      if type_ == datetime.date:
        from camelot.view.controls.editors import DateEditor
        editor = DateEditor()
        return QtCore.QVariant(editor.sizeHint())
      elif widget_ == 'one2many':
        from camelot.view.controls.editors import One2ManyEditor
        entity_name = c[0] 
        entity_admin = c[1]['admin']
        editor = One2ManyEditor(entity_admin, entity_name)
        sh = editor.sizeHint()
        return QtCore.QVariant(sh)
      elif widget_ == 'many2one':
        from camelot.view.controls import delegates
        from camelot.view.controls.editors import Many2OneEditor
        entity_admin = c[1]['admin']
        delegate = delegates.Many2OneColumnDelegate(entity_admin)
        editor = Many2OneEditor(entity_admin, delegate)
        sh = editor.sizeHint()
        return QtCore.QVariant(sh)
    elif role == Qt.ForegroundRole:
      #if not self.columns_getter()[index.column()][1]['nullable']:
      #  return QtCore.QVariant(QtGui.QColor(Qt.red))
      pass
    elif role == Qt.BackgroundRole:
      #if not self.columns_getter()[index.column()][1]['editable']:
      #  logger.debug('Setting background for non-editable column')
      #  return QtCore.QVariant(QtGui.QColor(Qt.lightGray))
      pass
    return QtCore.QVariant()

  def setData(self, index, value, role=Qt.EditRole):
    """Value should be a function taking no arguments that returns the data to be set
    This function will then be called in the model_thread
    """
    from elixir import session
    import datetime
    if role==Qt.EditRole:
      
      flushed = (index.row() not in self.unflushed_rows)
      self.unflushed_rows.add(index.row())
      
      def make_update_function(row, column, value):
        
        @model_function
        def update_model_and_cache():
          new_value = value()
          logger.debug('set data col %s, row %s to %s'%(row, column, new_value))
            
          from camelot.model.memento import BeforeUpdate
          from camelot.model.authentication import getCurrentPerson
          o = self._get_object(row)
          attribute = self.columns_getter()[column][0]
          old_value = getattr(o, attribute)
          if new_value!=old_value:
            # update the model
            try:
              setattr(o, attribute, new_value)
            except AttributeError:
              logger.error("Can't set attribute %s to %s"%(attribute, str(value)))
            # update the cache
            row_data = RowDataFromObject(o, self.columns_getter())
            self.cache[Qt.EditRole].add_data(row, o.id, row_data)
            self.cache[Qt.DisplayRole].add_data(row, o.id, RowDataAsUnicode(row_data))
            if self.flush_changes and self.validator.isValid(row):
              # save the state before the update
              session.flush([o])
              try:
                self.unflushed_rows.remove(row)
              except KeyError:
                pass
              history = BeforeUpdate(model=self.admin.entity.__name__, 
                                     primary_key=o.id, 
                                     previous_attributes={attribute:old_value},
                                     person = getCurrentPerson())
              session.flush([history])              
              self.rsh.sendEntityUpdate(o)
            return ((row,0), (row,len(self.columns_getter())))
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
    if self.columns_getter()[index.column()][1]['editable']:
     flags = flags | Qt.ItemIsEditable
    return flags

  @model_function
  def _extend_cache(self, offset, limit):
    """Extend the cache around row"""
    #@TODO : also store the primary key, here we just saved the id
    columns = self.columns_getter()
    for i,o in enumerate(self.collection_getter()[offset:offset+limit+1]):
      row_data = RowDataFromObject(o, columns)
      self.cache[Qt.EditRole].add_data(i+offset, o.id, row_data)
      self.cache[Qt.DisplayRole].add_data(i+offset, o.id, RowDataAsUnicode(row_data))
    return (offset, limit)
        
  @model_function
  def _get_object(self, row):
    """Get the object corresponding to row"""
    try:
      # first try to get the primary key out of the cache, if it's not
      # there, query the collection_getter
      pk = self.cache[Qt.EditRole].get_primary_key_at_row(row)
      if pk:
        return self.admin.entity.get(pk)
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
    
  @model_function
  def append(self, o):
    self.collection_getter().append(o)
 
  def removeRow(self, row, parent):
    logger.debug('remove row %s'%row)
    
    def make_delete_function():
      
      def delete_function():
        from elixir import session
        from camelot.model.memento import BeforeDelete
        from camelot.model.authentication import getCurrentPerson
        o = self._get_object(row)
        pk = o.id
        self.remove(o)
        # save the state before the update
        history = BeforeDelete(model=self.admin.entity.__name__, 
                               primary_key=pk, 
                               previous_attributes={},
                               person = getCurrentPerson() )
        self.rsh.sendEntityDelete(o)        
        o.delete()
        session.flush([history, o])   
      
      return delete_function
    
    def emit_changes(*args):
      self.refresh()
  
    self.mt.post(make_delete_function(), emit_changes)
    return True
    
  def insertRow(self, row, entity_instance_getter):
    
    def create_insert_function(getter):
      
      @model_function
      def insert_function():
        from elixir import session
        from camelot.model.memento import Create
        from camelot.model.authentication import getCurrentPerson
        o = getter()
        self.append(o)
        if self.flush_changes:
          session.flush([o])
          history = Create(model=self.admin.entity.__name__, 
                           primary_key=o.id,
                           person = getCurrentPerson() )
          session.flush([history])
          self.rsh.sendEntityCreate(o)
          
      return insert_function
      
    def emit_changes(*args):
      self.refresh()
  
    self.mt.post(create_insert_function(entity_instance_getter), emit_changes)
        
  def __del__(self):
    logger.warn('delete CollectionProxy')
