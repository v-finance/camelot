import logging
import settings

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import Qt, SIGNAL
from camelot.view.proxy.queryproxy import QueryTableProxy

logger = logging.getLogger('view.controls.tableview')
logger.setLevel(logging.DEBUG)

class QueryTable(QtGui.QTableView):

  def __init__(self):
    QtGui.QTableView.__init__(self)
    logger.debug('create querytable')
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.horizontalHeader().setClickable(False)

class TableView(QtGui.QWidget):

  def __init__(self, admin, parent=None):
    from search import SimpleSearchControl
    from inheritance import SubclassTree
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
    self.table_model = None
    self.table_layout.insertWidget(0, self.search_control)
    self.setSubclass(admin)
    self.class_tree = SubclassTree(admin, self)
    self.widget_layout.insertWidget(0, self.class_tree)
    self.widget_layout.insertLayout(1, self.table_layout)
    self.connect(self.search_control, SIGNAL('search'), self.startSearch)
    self.connect(self.search_control, SIGNAL('cancel'), self.cancelSearch)
    self.connect(self.class_tree, SIGNAL('subclasssClicked'), self.setSubclass)
    self.search_filter = lambda q: q
    self.setLayout(self.widget_layout)
    self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

  def setSubclass(self, admin):
    """Switch to a different subclass, where admin is the admin object of the
    subclass"""
    self.admin = admin
#    if self.table:
#      self.table.deleteLater()
#      self.table_model.deleteLater()
    self.table = QueryTable()
    # We create the table first with only 10 rows, to be able resize
    # the columns to the contents without much processing
    self.table_model = QueryTableProxy(admin,
                                       admin.entity.query.limit(10),
                                       admin.getColumns)
    self.table.setModel(self.table_model)
    self.table_layout.insertWidget(1, self.table)

    def update_delegates(*args):
      self.table.setItemDelegate(self.table_model.getItemDelegate())

    admin.mt.post(lambda: None, update_delegates)
    # Once those are loaded, rebuild the query to get the actual number of rows
    admin.mt.post(lambda: self.table_model._extend_cache(0, 10),
                  lambda x: self.resizeColumnsAndRebuildQuery())
    admin.mt.post(lambda: admin.getFilters(),
                  lambda items: self.setFilters(items))
    admin.mt.post(lambda: admin.getListCharts(),
                  lambda charts: self.setCharts(charts))

  def setCharts(self, charts):
    if charts:

      from matplotlib.figure import Figure
      from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as \
                                                     FigureCanvas

      chart = charts[0]

      def getData():
        from sqlalchemy.sql import select, func
        from elixir import session
        xcol = getattr(self.admin.entity, chart['x'])
        ycol = getattr(self.admin.entity, chart['y'])
        session.bind = self.admin.entity.table.metadata.bind
        result = session.execute(select([xcol, func.sum(ycol)]).group_by(xcol))
        summary = result.fetchall()
        return [s[0] for s in summary], [s[1] for s in summary]

      class MyMplCanvas(FigureCanvas):
          """Ultimately, this is a QWidget (as well as a FigureCanvasAgg)"""

          def __init__(self, parent=None, width=5, height=4, dpi=100):
              fig = Figure(figsize=(width, height), dpi=dpi, facecolor='w')
              self.axes = fig.add_subplot(111, axisbg='w')
              # We want the axes cleared every time plot() is called
              self.axes.hold(False)
              self.compute_initial_figure()
              FigureCanvas.__init__(self, fig)
              self.setParent(parent)
              FigureCanvas.setSizePolicy(self,
                                         QSizePolicy.Expanding,
                                         QSizePolicy.Expanding)
              FigureCanvas.updateGeometry(self)

          def compute_initial_figure(self):
              pass

      def setData(data):

        class MyStaticMplCanvas(MyMplCanvas):
            """Simple canvas with a sine plot."""

            def compute_initial_figure(self):
                x, y = data
                bar_positions = [i-0.25 for i in range(1, len(x)+1)]
                width = 0.5
                self.axes.bar(bar_positions, y, width, color='b')
                self.axes.set_xlabel('Year')
                self.axes.set_ylabel('Sales')
                self.axes.set_xticks(range(len(x)+1))
                self.axes.set_xticklabels(['']+[str(d) for d in x])

        sc = MyStaticMplCanvas(self, width=5, height=4, dpi=100)
        self.table_layout.addWidget(sc)

      self.admin.mt.post(getData, setData)

  def resizeColumnsAndRebuildQuery(self):
    logger.debug('resizeColumnsAndRebuildQuery')
    self.table.resizeColumnsToContents()
    self.rebuildQuery()

    logger.debug('Selecting first row in table')
    self.table.selectRow(0)

  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.table_model.removeRow(row, None)

  def newRow(self):
    """Create a new row in the tableview"""
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    form = self.admin.createNewView(workspace)
    workspace.addWindow('new', form)
    self.connect(form, form.entity_created_signal, lambda entity_instance_getter:self.table_model.insertRow(0, entity_instance_getter))
    form.show()

  def selectTableRow(self, row):
    self.table.selectRow(row)

  def selectedTableIndexes(self):
    return self.table.selectedIndexes()

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
    self.table_model.setQuery(self.search_filter(query))

  def startSearch(self, text):
    logger.debug('search %s' % text)
    import camelot.types

    def create_search_filter():
      if len(text.strip()):
        from sqlalchemy import Unicode, or_
        args = []
        for c in self.admin.entity.table._columns:
            if issubclass(c.type.__class__, camelot.types.Code):
              codes = text.split('.')
              args.append(c.like(['%'] + codes + ['%']))
              args.append(c.like(['%'] + codes))
              args.append(c.like(codes + ['%']))
            elif issubclass(c.type.__class__, (Unicode, )) or \
                            (hasattr(c.type, 'impl') and \
                             issubclass(c.type.impl.__class__, (Unicode, ))):
              logger.debug('look in column : %s'%c.name)
              args.append(c.like('%'+text+'%'))
        if len(args):
            if len(args)>1:
                return lambda q: q.filter(or_(*args))
            else:
                return lambda q: q.filter(args[0])
      return lambda q: q

    self.search_filter = create_search_filter()
    self.rebuildQuery()

  def cancelSearch(self):
    logger.debug('cancel search')
    self.search_filter = lambda q: q
    self.rebuildQuery()

  def setFilters(self, items):
    from filter import FilterList
    logger.debug('setFilters %s'%str(items))
    if self.filters:
      self.filters.deleteLater()
      self.filters = None
    if items:
      self.filters = FilterList(items, self)
      self.widget_layout.insertWidget(2, self.filters)
      self.connect(self.filters, SIGNAL('filters_changed'), self.rebuildQuery)

  def toHtml(self):
    table = [[getattr(row, col[0]) for col in self.admin.getColumns()]
             for row in self.admin.entity.query.all()]
    context = {
      'title': self.admin.getName(),
      'table': table,
      'columns': [c[0] for c in self.admin.getColumns()],
    }
    from jinja import Environment, FileSystemLoader
    ld = FileSystemLoader(settings.CAMELOT_TEMPLATES_DIRECTORY)
    env = Environment(loader=ld)
    tp = env.get_template('table_view.html')
    return tp.render(context)

  def closeEvent(self, event):
    logger.debug('tableview closed')
    # remove all references we hold, to enable proper garbage collection
    del self.widget_layout
    del self.table_layout
    del self.search_control
    del self.table
    del self.filters
    del self.class_tree
    del self.table_model
    event.accept()
    
  def __del__(self):
    logger.debug('tableview deleted')