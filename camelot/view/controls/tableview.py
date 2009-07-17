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

"""Tableview"""

import os
import logging
logger = logging.getLogger('camelot.view.controls.tableview')

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import Qt

from camelot.view.proxy.queryproxy import QueryTableProxy
from camelot.view.art import Icon
import settings


class QueryTable(QtGui.QTableView):
  """the actual displayed table"""

  def __init__(self, parent=None):
    QtGui.QTableView.__init__(self, parent)
    logger.debug('create querytable')
    self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
    self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.horizontalHeader().setClickable(False)
    #self.setSortingEnabled(True)

class Header(QtGui.QWidget):
  """Header for a tableview, containing the title, the search widget,
  and the number of rows in the table"""
  
  _title_font = QtGui.QApplication.font()
  _title_font.setBold(True)
  _number_of_rows_font = QtGui.QApplication.font()
  
  def __init__(self, admin, parent):
    QtGui.QWidget.__init__(self, parent)
    from search import SimpleSearchControl
    widget_layout = QtGui.QHBoxLayout()
    self.search_control = SimpleSearchControl(self)
    title = QtGui.QLabel(admin.get_verbose_name_plural(), self)
    title.setFont(self._title_font)
    widget_layout.addWidget(title)
    widget_layout.addWidget(self.search_control)
    self.number_of_rows = QtGui.QLabel(self)
    self.number_of_rows.setFont(self._number_of_rows_font)
    widget_layout.addWidget(self.number_of_rows)
    self.setLayout(widget_layout)
    self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    self.setNumberOfRows(0)
    
  def setNumberOfRows(self, rows):
    self.number_of_rows.setText(u'(%i rows)'%rows)
    
class TableView(QtGui.QWidget):
  """emits the row_selected signal when a row has been selected"""

  #
  # The proxy class to use 
  #
  query_table_proxy = QueryTableProxy
  #
  # Format to use as the window title
  #
  title_format = '%s'
  
  def __init__(self, admin, search_text=None, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.setWindowTitle(self.title_format%(admin.get_verbose_name_plural()))
    widget_layout = QtGui.QVBoxLayout()
    self.header = Header(admin, self)
    widget_layout.addWidget(self.header)
    widget_layout.setSpacing(0)
    widget_layout.setMargin(0)
    self.splitter = QtGui.QSplitter(self)
    widget_layout.addWidget(self.splitter)
    table_widget = QtGui.QWidget(self)
    self.table_layout = QtGui.QVBoxLayout()
    self.table_layout.setSpacing(0)
    self.table_layout.setMargin(0)
    self.table = None
    self.filters = None
    self.admin = admin
    self.table_model = None
    table_widget.setLayout(self.table_layout)
    self.setSubclass(admin)
    self.splitter.insertWidget(0, table_widget)
    self.setLayout(widget_layout)
    self.closeAfterValidation = QtCore.SIGNAL('closeAfterValidation()')
    self.connect(self.header.search_control, SIGNAL('search'), self.startSearch)
    self.connect(self.header.search_control, SIGNAL('cancel'), self.cancelSearch)
    
    self.search_filter = lambda q: q
    self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    if search_text:
      self.header.search_control.search(search_text)
    admin.mt.post(lambda: self.admin.getSubclasses(),
                  lambda subclasses: self.setSubclassTree(subclasses))      

  def setSubclassTree(self, subclasses):
    if len(subclasses) > 1:
      from inheritance import SubclassTree
      class_tree = SubclassTree(self.admin, self)
      self.splitter.insertWidget(0, class_tree)
      self.connect(class_tree, SIGNAL('subclassClicked'), self.setSubclass)
      
  def sectionClicked(self, section):
    """emits a row_selected signal"""
    self.emit(SIGNAL('row_selected'), section)

  def setSubclass(self, admin):
    """Switch to a different subclass, where admin is the admin object of the
    subclass"""
    self.admin = admin
    if self.table:
      self.table.deleteLater()
      self.table_model.deleteLater()
    self.table = QueryTable(self)
      
    self.table_model = self.query_table_proxy(admin,
                                              lambda:admin.entity.query,
                                              admin.getColumns)
    self.table.setModel(self.table_model)
    self.connect(self.table.verticalHeader(),
                 SIGNAL('sectionClicked(int)'),
                 self.sectionClicked)
    self.connect(self.table_model, QtCore.SIGNAL('layoutChanged()'), self.tableLayoutChanged)
    self.table_layout.insertWidget(1, self.table)

    def update_delegates_and_column_width(*args):
      """update item delegate"""
      self.table.setItemDelegate(self.table_model.getItemDelegate())
      for i in range(self.table_model.columnCount()):
        self.table.setColumnWidth(i, max(self.table_model.headerData(i, Qt.Horizontal, Qt.SizeHintRole).toSize().width(), self.table.columnWidth(i)))
      

    admin.mt.post(lambda: None, update_delegates_and_column_width)
    admin.mt.post(lambda: admin.getFilters(),
                  lambda items: self.setFilters(items))
    admin.mt.post(lambda: admin.getListCharts(),
                  lambda charts: self.setCharts(charts))

  def tableLayoutChanged(self):
    self.header.setNumberOfRows(self.table_model.rowCount())
    
  def setCharts(self, charts):
    """creates and display charts"""
    if charts:

      from matplotlib.figure import Figure
      from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as \
                                                     FigureCanvas

      chart = charts[0]

      def getData():
        """fetches data for chart"""
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
        """set chart data"""

        class MyStaticMplCanvas(MyMplCanvas):
          """simple canvas with a sine plot"""

          def compute_initial_figure(self):
            """computes initial figure"""
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

  def deleteSelectedRows(self):
    """delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.table_model.removeRow(row)

  def newRow(self):
    """Create a new row in the tableview"""
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    form = self.admin.createNewView(workspace,
                                    oncreate=lambda o:self.table_model.insertEntityInstance(0,o), 
                                    onexpunge=lambda o:self.table_model.removeEntityInstance(o))
    workspace.addSubWindow(form)
    form.show()

  def selectTableRow(self, row):
    """selects the specified row"""
    self.table.selectRow(row)

  def selectedTableIndexes(self):
    """returns a list of selected rows indexes"""
    return self.table.selectedIndexes()

  def getColumns(self):
    """return the columns to be displayed in the table view"""
    return self.admin.getColumns()

  def getData(self):
    """generator for data queried by table model"""
    for d in self.table_model.getData():
      yield d

  def getTitle(self):
    """return the name of the entity managed by the admin attribute"""
    return self.admin.get_verbose_name()

  def viewFirst(self):
    """selects first row"""
    self.selectTableRow(0)

  def viewLast(self):
    """selects last row"""
    self.selectTableRow(self.table_model.rowCount()-1)

  def viewNext(self):
    """selects next row"""
    first = self.selectedTableIndexes()[0]
    next = (first.row()+1) % self.table_model.rowCount()
    self.selectTableRow(next)

  def viewPrevious(self):
    """selects previous row"""
    first = self.selectedTableIndexes()[0]
    prev = (first.row()-1) % self.table_model.rowCount()
    self.selectTableRow(prev)

  def rebuildQuery(self):
    """resets the table model query"""
    
    def rebuild_query():
      query = self.admin.entity.query
      if self.filters:
        query = self.filters.decorate_query(query)
      if self.search_filter:
        query = self.search_filter(query)
      self.table_model.setQuery(lambda:query)
      
    self.admin.mt.post(rebuild_query)

  def startSearch(self, text):
    """rebuilds query based on filtering text"""
    from camelot.view.search import create_entity_search_query_decorator
    logger.debug('search %s' % text)
    self.search_filter = create_entity_search_query_decorator(self.admin, text)
    self.rebuildQuery()

  def cancelSearch(self):
    """resets search filtering to default"""
    logger.debug('cancel search')
    self.search_filter = lambda q: q
    self.rebuildQuery()

  def setFilters(self, items):
    """sets filters for the tableview"""
    from filter import FilterList
    #logger.debug('setting filters with items : %s' % str(items))
    logger.debug('setting filters for tableview')
    if self.filters:
      self.filters.deleteLater()
      self.filters = None
    if items:
      self.filters = FilterList(items, self)
      self.splitter.insertWidget(2, self.filters)
      self.connect(self.filters, SIGNAL('filters_changed'), self.rebuildQuery)

  def toHtml(self):
    """generates html of the table"""
    table = [[getattr(row, col[0]) for col in self.admin.getColumns()]
             for row in self.admin.entity.query.all()]
    context = {
      'title': self.admin.get_verbose_name_plural(),
      'table': table,
      'columns': [c[0] for c in self.admin.getColumns()],
    }
    from camelot.view.templates import loader
    from jinja import Environment, FileSystemLoader
    env = Environment(loader=loader)
    tp = env.get_template('table_view.html')
    return tp.render(context)

  def closeEvent(self, event):
    """reimplements close event"""
    logger.debug('tableview closed')
    # remove all references we hold, to enable proper garbage collection
    del self.table_layout
    del self.table
    del self.filters
    del self.table_model
    event.accept()
    
  def __del__(self):
    """deletes the tableview object"""
    logger.debug('%s deleted' % self.__class__.__name__) 
    
  def importFromFile(self):
    """"import data : the data will be imported in the activeMdiChild """
    from camelot.view.wizard.import_data import ImportWizard
    logger.info('call import method')  
    importWizard = ImportWizard(self)
    importWizard.start()
    data = importWizard.getImportedData()
    for row in data:
        print row
        self.query_table_proxy.append(self.query_table_proxy, row)
    