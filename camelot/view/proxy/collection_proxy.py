"""Proxy representing a collection of entities that live in the model thread.

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
   
def RowDataFromObject(obj, attrs):
  """Create row data from an object, by fetching its attributes"""
  return [getattr(obj,attr) for (k,attr) in enumerate(attrs)]
  
def RowDataAsUnicode(row_data):
  
  def unicode_or_none(data):
    if data:
      return unicode(data)
    return data
  
  return [unicode_or_none(col) for col in row_data]

class EmptyRowData(object):
  def __getitem__(self, column):
    return None
  
empty_row_data = EmptyRowData()
form_icon = QtCore.QVariant(QtGui.QIcon(art.icon16('places/folder')))

class fifo(dict):
  """fifo, is the actual cache containing a limited set of copies of row data
  so the data in fifo, is always immediately accessible to the gui thread,
  with zero delay as you scroll down the table view, fifo is filled and
  refilled with data queried from the database
  """
  def __init__(self, max_entries):
    self.max_entries = max_entries
    self.keys = []
  def __setitem__(self, key, value):
    if key in self:
      self.keys.remove(key)
    dict.__setitem__(self, key, value)
    self.keys.append(key)
    if len(self.keys)>self.max_entries:
      del self[self.keys.pop(0)] 
      
class CollectionProxy(QtCore.QAbstractTableModel):
  """The CollectionProxy contains a limited copy of the data in the actual collection,
  usable for fast visualisation in a QTableView 
  """
  
  def __init__(self, admin, collection_getter, columns_getter, max_number_of_rows=10, edits=None):
    """"
    @param admin: the admin interface for the items in the collection
    @param collection_getter: a function that takes no arguments and returns the collection
    that will be visualized.  This function will be called inside the model thread, to prevent
    delays when this function causes the database to be hit.
    @param columns_getter: a function that takes no arguments and returns the columns that will
    be cached in the proxy.  This function will be called inside the model thread.   
    """
    self.logger = logger
    logger.debug('initialize query table')
    QtCore.QAbstractTableModel.__init__(self)
    self.admin = admin
    self.collection_getter = collection_getter
    self.column_count = 0
    self.mt = admin.getModelThread()
    # Set database connection and load data
    self.rows = 0
    self.columns_getter = columns_getter
    self.limit = 50
    self.max_number_of_rows = max_number_of_rows
    self.cache = {Qt.DisplayRole:fifo(10*self.limit), Qt.EditRole:fifo(10*self.limit)}
    # The rows in the table for which a cache refill is under request
    self.rows_under_request = set()
    # Set edits
    self.edits = edits or []
    self.rsh = get_signal_handler()
    self.rsh.connect(self.rsh, self.rsh.entity_signal, self.handleEntitySignal)
    self.mt.post(columns_getter, lambda columns:self.setColumns(columns))
    # in that way the number of rows is requested as well
    self.mt.post(self._getRowCount,  self.setRowCount)
    logger.debug('initialization finished')
    self.item_delegate = None
    
  def _getRowCount(self):
    return len(self.collection_getter())
  
  def refresh(self):
    
    def refresh_content(rows):
      self.cache = {Qt.DisplayRole:fifo(10*self.limit), Qt.EditRole:fifo(10*self.limit)}
      self.setRowCount(rows)
      
    self.mt.post(self._getRowCount, refresh_content )
    
  def setCollectionGetter(self, collection_getter):
    self.collection_getter = collection_getter
    self.refresh()
    
  def handleEntitySignal(self):
    """Handles the entity signal, indicating that the model is out of date"""
    logger.debug('received entity signal')
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
    
  def setColumns(self, columns):
    """Callback method to set the columns
    @param columns a list with fields to be displayed
    """
    """Set custom delegates"""
    self.column_count = len(columns)
    logger.debug('setting up custom delegates')
    from camelot.view.controls import delegates
    import datetime
    self.item_delegate = delegates.GenericDelegate(self)
    for i, c in enumerate(columns):
      field_name = c[0]
      type_ = c[1]['python_type']
      widget_ = c[1]['widget']
      logger.debug('%s : creating delegate for type %s, using widget %s'%(field_name, type_, widget_))
      if widget_ == 'code':
        delegate = delegates.CodeColumnDelegate(c[1]['parts'])
        self.item_delegate.insertColumnDelegate(i, delegate)
        continue        
      if widget_ == 'image':
        delegate =delegates. ImageColumnDelegate()
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
        delegate =delegates. DateColumnDelegate(datetime.date.min, datetime.date.max, 'dd/MM/yyyy')
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == float:
        delegate = delegates.FloatColumnDelegate(-100000.0, 100000.0)
        self.item_delegate.insertColumnDelegate(i, delegate)
      elif type_ == bool:
        delegate = delegates.BoolColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
      else:
        delegate =delegates.PlainTextColumnDelegate()
        self.item_delegate.insertColumnDelegate(i, delegate)
    self.emit(QtCore.SIGNAL('layoutChanged()'))
           
  def unset_max_number_of_rows(self):
    if self.max_number_of_rows:
      if self.max_number_of_rows < self.rows:
        #msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, self.rows-self.max_number_of_rows)
        self.max_number_of_rows = None
        #self.grid.ProcessTableMessage(msg)
      self.max_number_of_rows = None

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
    if role == Qt.DecorationRole:
      if orientation == Qt.Vertical:
        return form_icon 
    return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
  
  def data(self, index, role):
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
    elif role == Qt.BackgroundColorRole:
      pass
      #return QtCore.QVariant(QueryTableModel.COLORS[index.row() % 2])
    return QtCore.QVariant()

  def setData(self, index, value, role=Qt.EditRole):
    from elixir import session
    import datetime
    logger.debug('set data col %s, row %s to %s'%(index.row(), index.column(), value))
    if role==Qt.EditRole:
      
      if self.columns_getter()[index.column()][1]['widget']=='many2one':
        return True
      
      def make_update_function(row, column, value):
        
        def update_model_and_cache():
          type = value.type()
          if type==QtCore.QMetaType.Bool:
            new_value = bool(value.toBool())
          elif type==QtCore.QMetaType.QString:
            new_value = unicode(value.toString())
          elif type in (QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.ULongLong,):
            new_value = int(value.toInt()[0])
          elif type in (QtCore.QMetaType.Short, QtCore.QMetaType.UShort,):
            new_value = int(value.toShort()[0])
          elif type in (QtCore.QMetaType.Long, QtCore.QMetaType.ULong,):
            new_value = int(value.toLong()[0])
          elif type==QtCore.QMetaType.Double:
            new_value = float(value.toDouble()[0])          
          elif type==QtCore.QMetaType.QDate:
            new_value = value.toDate()
            new_value = datetime.date(new_value.year(), new_value.month(), new_value.day())
          elif type==QtCore.QMetaType.QDateTime:
            new_value = value.toDateTime()
            new_value = datetime.datetime(year=new_value.date().year(), month=new_value.date().month(), day=new_value.date().day(), 
                                          hour=new_value.time().hour(), minute=new_value.time().minute(), second=new_value.time().second())            
          else:
            new_value = value.toPyObject()
            
          from camelot.model.memento import BeforeUpdate
          from camelot.model.authentication import getCurrentPerson
          o = self._get_object(row)
          attribute = self.columns_getter()[column][0]
          old_value = getattr(o, attribute)
          if new_value!=old_value:
            # save the state before the update
            history = BeforeUpdate(model=self.admin.entity.__name__, 
                                   primary_key=o.id, 
                                   previous_attributes={attribute:old_value},
                                   person = getCurrentPerson())
            # update the model
            setattr(o, attribute, new_value)
            # update the cache
            columns = [c[0] for c in self.columns_getter()] + ['id']
            row_data = RowDataFromObject(o, columns)
            self.cache[Qt.EditRole][row] = row_data
            self.cache[Qt.DisplayRole][row] = RowDataAsUnicode(row_data)
            session.flush([o, history])
            self.rsh.sendEntityUpdate(o)
            return ((row,0), (row,len(self.columns_getter())))
        
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

  def _extend_cache(self, offset, limit):
    """Extend the cache around row"""
    #@TODO : also store the primary key, here we just saved the id
    columns = [c[0] for c in self.columns_getter()] + ['id']
    for i,o in enumerate(self.collection_getter()[offset:offset+limit+1]):
      row_data = RowDataFromObject(o, columns)
      self.cache[Qt.EditRole][i+offset] = row_data
      self.cache[Qt.DisplayRole][i+offset] = RowDataAsUnicode(row_data)
    return (offset, limit)
        
  def _get_object(self, row):
    """Get the object corresponding to row"""
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
      return role_cache[row]
    except KeyError:
      if row not in self.rows_under_request:
        offset = max(row-self.limit/2,0)
        limit = self.limit
        self.rows_under_request.update(set(range(offset, offset+limit)))
        self.mt.post(lambda :self._extend_cache(offset, limit),
                     lambda interval:self._cache_extended(*interval))
      return empty_row_data

  def remove(self, o):
    self.collection_getter().remove(o)
    
  def append(self, o):
    self.collection_getter().append(o)
 
  def removeRow(self, row, parent):
    logger.debug('remove row %s'%row)
    pk = self.cache[Qt.EditRole][row][len(self.columns_getter())]
    
    def make_delete_function(pk):
      
      def delete_function():
        from elixir import session
        from camelot.model.memento import BeforeDelete
        from camelot.model.authentication import getCurrentPerson
        o = self._get_object(row)
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
  
    self.mt.post(make_delete_function(pk), emit_changes)
    return True
       
  def insertRow(self, row, parent):
    
    def create_function():
      from elixir import session
      from camelot.model.memento import Create
      from camelot.model.authentication import getCurrentPerson
      o = self.admin.entity()
      self.append(o)
      session.flush([o])
      history = Create(model=self.admin.entity.__name__, 
                       primary_key=o.id,
                       person = getCurrentPerson() )
      session.flush([history])
      self.rsh.sendEntityCreate(o)
      
    def emit_changes(*args):
      self.refresh()
  
    self.mt.post(create_function, emit_changes)
        
  def __del__(self):
    logger.debug('delete CollectionProxy')
