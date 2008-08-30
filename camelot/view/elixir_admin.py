"""
Admin classes, specify how objects should be rendered in the gui

An admin class has class attributes like 'list_display' which contains the
columns that should be displayed in a list view (again, see Django)

So this 'list_display' attribute can be overwritten in the Admin class for each
model.

But for the gui generation itself, we don't use the class attributes, but we
use methods, like 'getColumns', that way, we can make the gui very specific, on
the context
"""

import os
import sys
import logging

import settings

_ = lambda x:x

logger = logging.getLogger('entity_admin')
logger.setLevel(logging.DEBUG)

import sqlalchemy.types
import datetime

_sqlalchemy_to_python_type_ = {
  sqlalchemy.types.Boolean : lambda f:{'python_type':bool, 'editable':True, 'widget':'bool'},
  sqlalchemy.types.BOOLEAN : lambda f:{'python_type':bool, 'editable':True, 'widget':'bool'},
  sqlalchemy.types.Date : lambda f:{'python_type':datetime.date, 'format':'dd-mm-YYYY', 'editable':True, 'min':None, 'max':None, 'widget':'date'},
  sqlalchemy.types.Float : lambda f:{'python_type':float, 'precision':f.precision, 'editable':True, 'min':None, 'max':None, 'widget':'float'},
  sqlalchemy.types.Integer : lambda f:{'python_type':int, 'editable':True, 'min':None, 'max':None, 'widget':'int'},
  sqlalchemy.types.INT : lambda f:{'python_type':int, 'editable':True, 'min':None, 'max':None, 'widget':'int'},
  sqlalchemy.types.String : lambda f:{'python_type':str, 'length':f.length, 'editable':True, 'widget':'str'},
  sqlalchemy.types.TEXT : lambda f:{'python_type':str, 'length':f.length, 'editable':True, 'widget':'str'},
  sqlalchemy.types.Unicode : lambda f:{'python_type':str, 'length':f.length, 'editable':True, 'widget':'str'},
}
 
class EntityAdmin(object):
  
  name = None
  list_display = []
  fields = []
  list_filter = []
  list_charts = []
  list_actions = []
  form_actions = []
  
  def __init__(self, app_admin, entity):
    """
    @param app_admin: the application admin object for this application
    @param entity: the entity class for which this admin instance is to be used
    """ 
    self.app_admin = app_admin
    if entity:
      from model_thread import get_model_thread
      self.entity = entity
      self.mt = get_model_thread()
  
  def getName(self):
    return (self.name or self.entity.__name__)
  
  def getModelThread(self):
    return self.mt
  
  def getFormActions(self, entity):
    return self.form_actions
  
  def getRelatedEntityAdmin(self, entity):
    return self.app_admin.getEntityAdmin(entity)
  
  def getSubclasses(self):
    """Return admin objects for the subclasses of the Entity represented by
    this admin object"""
    from elixir import entities
    return [e.Admin(self.app_admin, e) for e in entities if issubclass(e, (self.entity,)) if hasattr(e,'Admin')]
    
  def getFieldAttributes(self, field_name):
    """Get the attributes needed to visualize the field field_name
    @param field_name : the name of the field
    @return: a dictionary of attributes needed to visualize the field, those
    attributes can be:
     * python_type : the corresponding python type of the object
     * editable : bool specifying wether the user can edit this field
     * widget : which widget to be used to render the field
     * ...
    """
    from sqlalchemy import orm
    from sqlalchemy.exceptions import InvalidRequestError
    default = lambda x:dict(python_type=str, length=None, editable=False, widget='str')
    attributes = default(field_name)
    mapper = orm.class_mapper(self.entity)
    try:
      property = mapper.get_property(field_name, resolve_synonyms=True)
      if isinstance(property, orm.properties.ColumnProperty):
        type = property.columns[0].type
        attributes = _sqlalchemy_to_python_type_.get(type.__class__, default)(type)
      elif isinstance(property, orm.properties.PropertyLoader):
        target = property._get_target_class()
        if property.direction == orm.sync.ONETOMANY:
          attributes = dict(python_type=str, length=None, editable=True, widget='one2many', admin=self.getRelatedEntityAdmin(target))
        elif property.direction == orm.sync.MANYTOONE:
          attributes = dict(python_type=str, length=None, editable=True, widget='many2one', admin=self.getRelatedEntityAdmin(target))
        elif property.direction == orm.sync.MANYTOMANY:
          attributes = dict(python_type=str, length=None, editable=True, widget='many2many', admin=self.getRelatedEntityAdmin(target))
        else:
          raise Exception('PropertyLoader has unknown direction')
    except InvalidRequestError, e:
      """If the field name is not a property of the mapper, then use the default stuff"""
      pass
    attributes.update(dict(blank=True, validator_list=[], name=field_name.replace('_',' ').capitalize()))
    return attributes
  
  def getColumns(self):
    """The columns to be displayed in the list view, returns a list of pairs of
    the name of the field and its attributes needed to display it properly
    
    @return: [(field_name, 
                {'widget': widget_type, 'editable': True or False,
                 'blank': True or False, 'validator_list':[...], 'name':'Field name'}
              ), ...]
    """
    return [(field,self.getFieldAttributes(field)) for field in self.list_display]
  
  def getFields(self):
    if self.fields:
      return [(field,self.getFieldAttributes(field)) for field in self.fields]
    else:
      return [(field,self.getFieldAttributes(field)) for field in self.list_display]
    
  def getListCharts(self):
    return self.list_charts
  
  def getFilters(self):
    """Return the filters applicable for these entities each filter is a tuple
    of the name of the filter and a list of options that can be selected. Each
    option is a tuple of the name of the option, and a filter function to
    decorate a query
     
    @return: [(filter_name, [(option_name, query_decorator), ...), ... ]
    """

    def getOptions(attr):
      from sqlalchemy.sql import select
      from elixir import session
      col = getattr(self.entity, attr)
      session.bind = self.entity.table.metadata.bind
      query = select([col], distinct=True, order_by=col.asc())
      
      def decorator(col, value):
        return lambda q:q.filter(col==value)
      
      options = [(value[0], decorator(col, value[0])) for value in session.execute(query)]
      return [('All', lambda q:q)] + options 
      
    return [(attr, getOptions(attr)) for attr in self.list_filter]

  def createFormView(admin, title, model, index, parent):
    """Creates a Qt widget containing a form view, for a specific row of the 
    passed query; uses the Admin class
    """
    
    logger.debug('creating form view')

    from PyQt4 import QtCore
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt

    class FormView(QtGui.QWidget):
      
      def __init__(self):
        super(FormView, self).__init__(None)
        self.setWindowTitle(title)
        
        self.widget_layout = QtGui.QHBoxLayout()
        self.widgets = model.widgets
        self.widget_mapper = QtGui.QDataWidgetMapper()
        self.widget_mapper.setModel(model)

        form_layout = QtGui.QFormLayout()
        for i, (name, functor) in enumerate(self.widgets):
          parent = None # layout manager will set the parent
          option = None # we won't use any option
          widget = functor(parent, option, model.index(index,0))
          form_layout.addRow(name, widget)
          self.widget_mapper.addMapping(widget, i)

        self.widget_mapper.setCurrentIndex(index)
        self.widget_layout.insertLayout(0, form_layout)
        self.setLayout(self.widget_layout)
        
        def getEntityAndActions():
          entity = model._get_object(index)
          actions = admin.getFormActions(entity)
          return entity, actions
        
        admin.mt.post(getEntityAndActions, self.setEntityAndActions)

      def closeEvent(self, event):
        # remove from parent mapping
        logger.debug('removing form view %s from parent mapping' % title)
        key = 'Form View: %s' % str(title)
        parent.childwindows.pop(key)
        event.accept()
      
      def setEntityAndActions(self, result):
        entity, actions = result
        if actions:
          from controls.actions import ActionsBox
          logger.debug('setting Actions')
          self.actions_widget = ActionsBox(self, admin.mt)
          self.actions_widget.setActions(actions)
          self.actions_widget.setEntity(entity)
          self.widget_layout.insertWidget(1, self.actions_widget)        

      def __del__(self):
        logger.debug('deleting form view')

    return FormView()

  def createSelectView(admin, query, parent=None):
    """returns a QT widget that can be used to select an element form a query,
    
    @param query: sqlalchemy query object
    @param parent: the widget that will contain this select view
    """
    return admin.createTableView(query, parent)
    
  def createTableView(admin, query, parent=None):
    """returns a QT widget containing a table view, for a certain query, using
    this Admin class; the table widget contains a model QueryTableModel

    @param query: sqlalchemy query object
    @param parent: the workspace widget that will contain the table view
    """
    
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore import Qt

    class QueryTable(QtGui.QTableView):
      def __init__(self):
        QtGui.QTableView.__init__(self)
        logger.debug('create querytable')
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)

        self.connect(self.verticalHeader(),
                     QtCore.SIGNAL('sectionClicked(int)'),
                     self.createFormForIndex)

      def createFormForIndex(self, index):
        title = 'Row %s - %s' % (index, admin.getName()) 
        
        existing = parent.findMdiChild(title)
        if existing is not None:
          parent.workspace.setActiveWindow(existing)
          return

        model = self.model()
        form = admin.createFormView(title, model, index, parent)

        width = int(parent.width() / 2)
        height = int(parent.height() / 2)
        form.resize(width, height)
        
        parent.workspace.addWindow(form)
        
        key = 'Form View: %s' % str(title)
        parent.childwindows[key] = form

        form.show()

      def __del__(self):
        logger.debug('delete querytable')
                               
    class TableView(QtGui.QWidget):
      def __init__(self, admin, parent):
        from controls.search import SimpleSearchControl
        from controls.inheritance import SubclassTree
        
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle(admin.getName())
        self.widget_layout = QtGui.QHBoxLayout()
        self.widget_layout.setSpacing(0)
        self.widget_layout.setMargin(0)
        self.table_layout = QtGui.QVBoxLayout()
        self.table_layout.setSpacing(0)
        self.table_layout.setMargin(0)
        self.search_control = SimpleSearchControl()
        self.table = None
        self.filters = None
        self.admin = admin
        self.table_layout.insertWidget(0, self.search_control)
        
        self.setSubclass(admin)
        self.class_tree = SubclassTree(admin, self)
        self.widget_layout.insertWidget(0, self.class_tree )
        self.widget_layout.insertLayout(1, self.table_layout)
        self.connect(self.search_control, QtCore.SIGNAL('search'), self.startSearch)
        self.connect(self.search_control, QtCore.SIGNAL('cancel'), self.cancelSearch)
        self.connect(self.class_tree, QtCore.SIGNAL('subclasssClicked'), self.setSubclass)
        self.search_filter = lambda q:q
        self.setLayout(self.widget_layout)

        # should occupy 1/4 of parent space
        if parent:
          width = int(parent.width() / 2)
          height = int(parent.height() / 2)
          self.resize(width, height)

      def setSubclass(self, admin):
        """Switch to a different subclass, where admin is the admin object of the
        subclass"""
        from proxy.queryproxy import QueryTableProxy
        self.admin = admin
        if self.table:
          #self.table_layout.removeWidget(self.table)
          #self.table.setModel(None)
          self.table_model.setTable(None)
          self.table.deleteLater()
          self.table_model.deleteLater()
        self.table = QueryTable()
        # We create the table first with only 10 rows, to be able resize the columns to
        # the contents without much processing
        self.table_model = QueryTableProxy(admin, self.table, admin.entity.query.limit(10))
        self.table.setModel(self.table_model)
        self.table_layout.insertWidget(1, self.table)
        # Once those are loaded, rebuild the query to get the actual number of rows
        admin.mt.post(lambda:self.table_model._extend_cache(0, 10), lambda x:self.resizeColumnsAndRebuildQuery())
        admin.mt.post(lambda:admin.getFilters(), lambda items:self.setFilters(items))
        admin.mt.post(lambda:admin.getListCharts(), lambda charts:self.setCharts(charts))
                
      def setCharts(self, charts):
        if charts:
          
          from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
          from matplotlib.figure import Figure
          
          chart = charts[0]
          
          def getData():
            from sqlalchemy.sql import select, func
            from elixir import session
            xcol = getattr(self.admin.entity, chart['x'])
            ycol = getattr(self.admin.entity, chart['y'])
            session.bind = self.admin.entity.table.metadata.bind
            summary = session.execute(select([xcol, func.sum(ycol)]).group_by(xcol)).fetchall()
            return [s[0] for s in summary],[s[1] for s in summary]
      
          class MyMplCanvas(FigureCanvas):
              """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
              def __init__(self, parent=None, width=5, height=4, dpi=100):
                  fig = Figure(figsize=(width, height), dpi=dpi, facecolor='w')
                  self.axes = fig.add_subplot(111, axisbg='w')
                  # We want the axes cleared every time plot() is called
                  self.axes.hold(False)
                  self.compute_initial_figure()
                  FigureCanvas.__init__(self, fig)
                  self.setParent(parent)
          
                  FigureCanvas.setSizePolicy(self,
                                             QtGui.QSizePolicy.Expanding,
                                             QtGui.QSizePolicy.Expanding)
                  FigureCanvas.updateGeometry(self)
          
              def compute_initial_figure(self):
                  pass
          
          def setData(data):
            
            class MyStaticMplCanvas(MyMplCanvas):
                """Simple canvas with a sine plot."""
                def compute_initial_figure(self):
                    x, y = data
                    bar_positions = [i-0.25 for i in range(1,len(x)+1)]
                    width = 0.5
                    self.axes.bar(bar_positions, y, width, color='b')
                    self.axes.set_xlabel('Year')
                    self.axes.set_ylabel('Sales')
                    self.axes.set_xticks(range(len(x)+1))
                    self.axes.set_xticklabels(['']+[str(d) for d in x])
                  
            sc = MyStaticMplCanvas(self, width=5, height=4, dpi=100)
            self.table_layout.addWidget( sc )
            
          admin.mt.post(getData, setData)
      
      def resizeColumnsAndRebuildQuery(self):
        logger.debug('resizeColumnsAndRebuildQuery')
        self.table.resizeColumnsToContents()
        self.rebuildQuery()
        
      def deleteSelectedRows(self):
        """Delete the selected rows in this tableview"""
        logger.debug('delete selected rows called')
        for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
          self.table_model.removeRow(row, None)
          
      def newRow(self):
        """Create a new row in the tableview"""
        self.table_model.insertRow(0, None)
                
      def getColumns(self):
        return self.admin.getColumns()
        
      def getData(self):
        for d in self.table_model.getData():
          yield d
        
      def getTitle(self):
        return self.admin.getName()
        
      def rebuildQuery(self):
        query = self.admin.entity.query
        if self.filters:
          query = self.filters.decorate_query(query)
        self.table_model.setQuery( self.search_filter(query) )
        
      def startSearch(self, text):
        logger.debug('search %s' % text)
          
        def create_search_filter():
          if len(text.strip()):
            from sqlalchemy import Unicode, or_
            args = []
            for c in self.admin.entity.table._columns:
                if isinstance(c.type, Unicode):
                    logger.debug('look in column : %s'%c.name)
                    args.append( c.like('%'+text+'%') )
            if len(args):
                if len(args)>1:
                    return lambda q:q.filter(or_(*args))
                else:
                    return lambda q:q.filter(args[0])
          return lambda q:q

        self.search_filter = create_search_filter()
        self.rebuildQuery()
  
      def cancelSearch(self):
        logger.debug('cancel search')
        self.search_filter = lambda q:q
        self.rebuildQuery()

      def setFilters(self, items):
        from controls.filter import FilterList
        logger.debug('setFilters %s'%str(items))
        if self.filters:
          self.filters.deleteLater()
          self.filters = None
        if items:
          self.filters = FilterList(items, self)
          self.widget_layout.insertWidget(2, self.filters)
          self.connect(self.filters, QtCore.SIGNAL('filters_changed'), self.rebuildQuery)
      
      def toHtml(self):
        table = [[getattr(row,col[0]) for col in admin.getColumns()] for row in self.admin.entity.query.all()]
        context = {
          'title': admin.getName(),
          'table': table,
          'columns': [c[0] for c in admin.getColumns()],
        }
        from jinja import Environment, FileSystemLoader
        e = Environment(loader=FileSystemLoader(settings.CAMELOT_TEMPLATES_DIRECTORY))
        t = e.get_template('table_view.html')
        return t.render(context)
      
      def closeEvent(self, event):
        # remove from parent mapping
        logger.debug('removing table view %s from parent mapping' % str(admin))
        key = 'Table View: %s' % str(admin)
        parent.childwindows.pop(key)
        event.accept()

      def __del__(self):
        logger.debug('delete TableView')
                
    return TableView(admin, parent)
  
  def __str__(self):
    return 'Admin %s'%str(self.entity.__name__)

