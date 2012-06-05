#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

"""Tableview"""

import logging
logger = logging.getLogger( 'camelot.view.controls.tableview' )

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QSizePolicy

from camelot.admin.action.list_action import ListActionGuiContext
from camelot.core.utils import variant_to_pyobject, ugettext as _
from camelot.view.proxy.queryproxy import QueryTableProxy
from camelot.view.controls.view import AbstractView
from camelot.view.controls.user_translatable_label import UserTranslatableLabel
from camelot.view.controls.progress_dialog import ProgressDialog
from camelot.view.model_thread import post
from camelot.view.model_thread import object_thread
from camelot.view.model_thread import model_function
from camelot.view import register

from search import SimpleSearchControl

class FrozenTableWidget( QtGui.QTableView ):
    """A table widget to be used as the frozen table widget inside a table
    widget."""

    def __init__(self, parent, columns_frozen):
        super(FrozenTableWidget, self).__init__(parent)
        assert object_thread( self )
        self.setSelectionBehavior( QtGui.QAbstractItemView.SelectRows )
        self.setEditTriggers( QtGui.QAbstractItemView.SelectedClicked |
                              QtGui.QAbstractItemView.DoubleClicked |
                              QtGui.QAbstractItemView.CurrentChanged )
        self._columns_frozen = columns_frozen

    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def currentChanged(self, current, previous):
        """When the current index has changed, prevent it to jump to
        a column that is not frozen"""
        assert object_thread( self )
        if current.column() >= self._columns_frozen:
            current = self.model().index( current.row(), -1 )
        if previous.column() >= self._columns_frozen:
            previous = self.model().index( previous.row(), -1 )
        super(FrozenTableWidget, self).currentChanged(current, previous)
        
class ColumnGroupsWidget( QtGui.QTabBar ):
    """A tabbar the user can use to select a group of columns within an
    item view.
    
    :param table: a :class:`camelot.admin.table.Table` object, describing the 
       column groups.
    :param table_widget: a :class:`QtGui.QTableView` widget of which columns will
       be hidden and shown depending on the selected tab.
    :param parent: a :class:`QtGui.QWidget`
    """
    
    def __init__( self, table, table_widget, parent = None ):
        from camelot.admin.table import ColumnGroup
        super( ColumnGroupsWidget, self ).__init__( parent )
        assert object_thread( self )
        self.setShape( QtGui.QTabBar.RoundedSouth )
        self.groups = dict()
        self.table_widget = table_widget
        column_index = 0
        tab_index = 0
        for column in table.columns:
            if isinstance( column, ColumnGroup ):
                self.addTab( unicode( column.verbose_name ) )
                previous_column_index = column_index
                column_index = column_index + len( column.get_fields() )
                self.groups[ tab_index ] = ( previous_column_index,
                                             column_index )
                tab_index += 1
            else:
                column_index += 1
        self.currentChanged.connect( self._current_index_changed )
        
    @QtCore.pyqtSlot( QtCore.QModelIndex, int, int )
    def columns_changed( self, index, first_column, last_column ):
        assert object_thread( self )
        self._current_index_changed( self.currentIndex() )
        
    @QtCore.pyqtSlot()
    def model_reset( self ):
        assert object_thread( self )
        self._current_index_changed( self.currentIndex() )
        
    @QtCore.pyqtSlot( int )
    def _current_index_changed( self, current_index ):
        assert object_thread( self )
        for tab_index, (first_column, last_column) in self.groups.items():
            for column_index in range( first_column, last_column ):
                self.table_widget.setColumnHidden( column_index,
                                                   tab_index != current_index )

class TableWidget( QtGui.QTableView ):
    """A widget displaying a table, to be used within a TableView.  This is a
pumped up version of the QTableView widget providing extra functions such as
frozen columns.  But it does not rely on the model being Camelot specific, or
a Collection Proxy.

.. attribute:: margin

margin, specified as a number of pixels, used to calculate the height of a row
in the table, the minimum row height will allow for this number of pixels below
and above the text.

"""

    margin = 5
    keyboard_selection_signal = QtCore.pyqtSignal()

    def __init__( self, parent = None, columns_frozen = 0, lines_per_row = 1 ):
        """
:param columns_frozen: the number of columns on the left that don't scroll
:param lines_per_row: the number of lines of text that should be viewable in a single row.
        """
        QtGui.QTableView.__init__( self, parent )
        logger.debug( 'create TableWidget' )
        assert object_thread( self )
        self._columns_frozen = columns_frozen
        self._columns_changed = dict()
        self.setSelectionBehavior( QtGui.QAbstractItemView.SelectRows )
        self.setEditTriggers( QtGui.QAbstractItemView.SelectedClicked |
                              QtGui.QAbstractItemView.DoubleClicked |
                              QtGui.QAbstractItemView.CurrentChanged )
        self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        self.horizontalHeader().setClickable( True )
        self._header_font_required = QtGui.QApplication.font()
        self._header_font_required.setBold( True )
        line_height = QtGui.QFontMetrics(QtGui.QApplication.font()).lineSpacing()
        self._minimal_row_height = line_height * lines_per_row + 2*self.margin
        self.verticalHeader().setDefaultSectionSize( self._minimal_row_height )
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.horizontalHeader().sectionClicked.connect(
            self.horizontal_section_clicked )
        self.horizontalHeader().sectionResized.connect( self._save_section_width )
        if columns_frozen:
            frozen_table_view = FrozenTableWidget(self, columns_frozen)
            frozen_table_view.setObjectName( 'frozen_table_view' )
            frozen_table_view.verticalHeader().setDefaultSectionSize( self._minimal_row_height )
            frozen_table_view.verticalHeader().hide()
            frozen_table_view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
            frozen_table_view.horizontalHeader().sectionClicked.connect(
                self.horizontal_section_clicked )
            self.horizontalHeader().sectionResized.connect( self._update_section_width )
            self.verticalHeader().sectionResized.connect( self._update_section_height )
            frozen_table_view.verticalScrollBar().valueChanged.connect( self.verticalScrollBar().setValue )
            self.verticalScrollBar().valueChanged.connect( frozen_table_view.verticalScrollBar().setValue )
            self.viewport().stackUnder(frozen_table_view)
            frozen_table_view.setStyleSheet("QTableView { border: none;}")
            frozen_table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            frozen_table_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            frozen_table_view.show()
            frozen_table_view.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

    @QtCore.pyqtSlot(int, int, int)
    def _update_section_width(self, logical_index, _old_size, new_size):
        assert object_thread( self )
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if logical_index < self._columns_frozen and frozen_table_view:
            frozen_table_view.setColumnWidth( logical_index, new_size)
            self._update_frozen_table()
            
    def timerEvent( self, event ):
        """On timer event, save changed column widths to the model
        """
        assert object_thread( self )
        for logical_index, new_width in self._columns_changed.items():
            if self.horizontalHeader().isSectionHidden( logical_index ):
                # don't save the width of a hidden section, since this will
                # result in setting the width to 0
                continue
            old_size = variant_to_pyobject( self.model().headerData( logical_index, 
                                                                     Qt.Horizontal, 
                                                                     Qt.SizeHintRole ) )
            # when the size is different from the one from the model, the
            # user changed it
            if old_size.width() != new_width:
                new_size = QtCore.QSize( new_width, old_size.height() )
                self.model().setHeaderData( logical_index, 
                                            Qt.Horizontal,
                                            new_size,
                                            Qt.SizeHintRole )
        self._columns_changed = dict()
        super( TableWidget, self ).timerEvent( event )
        
    @QtCore.pyqtSlot(int, int, int)
    def _save_section_width(self, logical_index, _old_size, new_width ):
        # instead of storing the width immediately, a timer is started to store
        # the width when all event processing is done.  because at this time
        # we cannot yet determine if the section at logical_index is hidden
        # or not
        #
        # there is no need to start the timer, since this is done by the 
        # QAbstractItemView itself for doing the layout, here we only store
        # which column needs to be saved.
        assert object_thread( self )
        self._columns_changed[ logical_index ] = new_width

    @QtCore.pyqtSlot(int, int, int)
    def _update_section_height(self, logical_index, _int, new_size):
        assert object_thread( self )
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if frozen_table_view:
            frozen_table_view.setRowHeight(logical_index, new_size)

    def setItemDelegate(self, item_delegate):
        assert object_thread( self )
        super(TableWidget, self).setItemDelegate(item_delegate)
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if frozen_table_view:
            frozen_table_view.setItemDelegate(item_delegate)

    def resizeEvent(self, event):
        assert object_thread( self )
        super(TableWidget, self).resizeEvent(event)
        self._update_frozen_table()

    def moveCursor(self, cursorAction, modifiers):
        assert object_thread( self )
        current = super(TableWidget, self).moveCursor(cursorAction, modifiers)
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if frozen_table_view:
            frozen_width = 0
            last_frozen =  min(self._columns_frozen, self.model().columnCount())
            for column in range(0, last_frozen):
                frozen_width += self.columnWidth(column)
            if cursorAction == QtGui.QAbstractItemView.MoveLeft and current.column() >= last_frozen and \
               self.visualRect(current).topLeft().x() < frozen_width:
                new_value = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - frozen_width
                self.horizontalScrollBar().setValue(new_value)
        return current

    def scrollTo(self, index, hint):
        assert object_thread( self )
        if(index.column()>=self._columns_frozen):
            super(TableWidget, self).scrollTo(index, hint)

    def edit(self, index, trigger=None, event=None):
        assert object_thread( self )
        #
        # columns in the frozen part should never be edited, because this might result
        # in an editor opening below the frozen column that contains the old value
        # which will be committed again when closed
        #
        if index.column() >= self._columns_frozen:
            if trigger==None and event==None:
                return super( TableWidget, self ).edit( index )
            return super( TableWidget, self ).edit( index, trigger, event )
        return False

    @QtCore.pyqtSlot()
    def _update_frozen_table(self):
        assert object_thread( self )
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if frozen_table_view:
            selection_model = self.selectionModel()
            if selection_model != None: 
                # explicitly check if there is a selection model, because
                # setting the selection model to None will cause an assertion
                # failure in Qt
                frozen_table_view.setSelectionModel( selection_model )
            last_frozen =  min(self._columns_frozen, self.model().columnCount())
            frozen_width = 0
            for column in range(0, last_frozen):
                frozen_width += self.columnWidth( column )
                frozen_table_view.setColumnWidth( column,
                                                  self.columnWidth(column) )
            for column in range(last_frozen, self.model().columnCount()):
                frozen_table_view.setColumnHidden(column, True)
            frozen_table_view.setGeometry( self.verticalHeader().width() + self.frameWidth(),
                                           self.frameWidth(),
                                           frozen_width,
                                           self.viewport().height() + self.horizontalHeader().height() )

    @QtCore.pyqtSlot( int )
    def horizontal_section_clicked( self, logical_index ):
        """Update the sorting of the model and the header"""
        assert object_thread( self )
        header = self.horizontalHeader()
        order = Qt.AscendingOrder
        if not header.isSortIndicatorShown():
            header.setSortIndicatorShown( True )
        elif header.sortIndicatorSection()==logical_index:
            # apparently, the sort order on the header is already switched
            # when the section was clicked, so there is no need to reverse it
            order = header.sortIndicatorOrder()
        header.setSortIndicator( logical_index, order )
        self.model().sort( logical_index, order )

    def close_editor(self):
        """Close the active editor, this method is used to prevent assertion
        failures in QT when an editor is still open in the view for a cell
        that no longer exists in the model
        
        those assertion failures only exist in QT debug builds.
        """
        assert object_thread( self )
        current_index = self.currentIndex()
        if not current_index:
            return
        if(current_index.column()>=self._columns_frozen):
            table_widget = self
        else:
            table_widget = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if table_widget:
            table_widget.closePersistentEditor( current_index )
                
    def setModel( self, model ):
        assert object_thread( self )
        #
        # An editor might be open that is no longer available for the new
        # model.  Not closing this editor, results in assertion failures
        # in qt, resulting in segfaults in the debug build.
        #
        self.close_editor()
        #
        # Editor, closed. it should be safe to change the model
        #
        QtGui.QTableView.setModel( self, model )
        frozen_table_view = self.findChild(QtGui.QWidget, 'frozen_table_view' )
        if frozen_table_view:
            model.layoutChanged.connect( self._update_frozen_table )
            frozen_table_view.setModel( model )
            self._update_frozen_table()
        register.register( model, self )
        self.selectionModel().currentChanged.connect( self.activated )
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def activated( self, selectedIndex, previousSelectedIndex ):
        assert object_thread( self )
        option = QtGui.QStyleOptionViewItem()
        new_size = self.itemDelegate( selectedIndex ).sizeHint( option,
                                                                selectedIndex )
        row = selectedIndex.row()
        if previousSelectedIndex.row() >= 0:
            previous_row = previousSelectedIndex.row()
            self.setRowHeight( previous_row, self._minimal_row_height )
        self.setRowHeight( row, max( new_size.height(),
                                     self._minimal_row_height ) )
                                     
    def keyPressEvent(self, e):
        assert object_thread( self )
        if self.hasFocus() and e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.keyboard_selection_signal.emit()
        else:
            super(TableWidget, self).keyPressEvent(e) 

class AdminTableWidget( QtGui.QWidget ):
    """A table widget that inspects the admin class and changes the behavior
    of the table as specified in the admin class"""
    
    def __init__(self, admin, parent=None):
        super( AdminTableWidget, self ).__init__( parent )
        assert object_thread( self )
        self._admin = admin
        table_widget = TableWidget( columns_frozen = admin.list_columns_frozen,
                                    lines_per_row = admin.lines_per_row,
                                    parent = self )
        table_widget.setObjectName( 'table_widget' )
        column_groups = ColumnGroupsWidget( admin.get_table(), table_widget )
        column_groups.setObjectName( 'column_groups' )
        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 0 )
        layout.setMargin( 0 )
        layout.addWidget( table_widget )
        layout.addWidget( column_groups )
        self.setLayout( layout )
        if admin.drop_action != None:
            table_widget.setDragDropMode( QtGui.QAbstractItemView.DragDrop )
            table_widget.setDropIndicatorShown( True )
                        
    def __getattr__( self, name ):
        table_widget = self.findChild( QtGui.QWidget, 'table_widget' )
        if table_widget != None:
            return getattr( table_widget, name )
        
    def setModel( self, model ):
        assert object_thread( self )
        table_widget = self.findChild( QtGui.QWidget, 'table_widget' )
        column_groups = self.findChild( QtGui.QWidget, 'column_groups' )
        if table_widget != None:
            model.columnsInserted.connect( column_groups.columns_changed )
            model.columnsRemoved.connect( column_groups.columns_changed )
            model.layoutChanged.connect( column_groups.model_reset )
            model.modelReset.connect( column_groups.model_reset )
            table_widget.setModel( model )
            column_groups.model_reset()
            
    @QtCore.pyqtSlot()
    def delete_selected_rows(self):
        assert object_thread( self )
        logger.debug( 'delete selected rows called' )
        confirmed = True
        rows = set( index.row() for index in self.selectedIndexes() )
        if not rows:
            return
        if self._admin.get_delete_mode()=='on_confirm':
            if QtGui.QMessageBox.question(self,
                                          _('Please confirm'),
                                          unicode(self._admin.get_delete_message(None)),
                                          QtGui.QMessageBox.Yes,
                                          QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                confirmed = False
        if confirmed:
            #
            # if there is an open editor on a row that will be deleted, there
            # might be an assertion failure in QT, or the data of the editor 
            # might be pushed to the row that replaces the deleted one
            #
            progress_dialog = ProgressDialog(_('Removing'))
            self.model().rows_removed_signal.connect( progress_dialog.finished )
            self.model().exception_signal.connect( progress_dialog.exception )
            self.close_editor()
            self.model().remove_rows( set( rows ) )
            progress_dialog.exec_()

    @QtCore.pyqtSlot()
    def copy_selected_rows(self):
        assert object_thread( self )
        for row in set( map( lambda x: x.row(), self.selectedIndexes() ) ):
            self.model().copy_row( row )
        
class RowsWidget( QtGui.QLabel ):
    """Widget that is part of the header widget, displaying the number of rows
    in the table view"""

    _number_of_rows_font = QtGui.QApplication.font()

    def __init__( self, parent ):
        QtGui.QLabel.__init__( self, parent )
        assert object_thread( self )
        self.setFont( self._number_of_rows_font )

    def setNumberOfRows( self, rows ):
        assert object_thread( self )
        self.setText( _('(%i rows)')%rows )

class HeaderWidget( QtGui.QWidget ):
    """HeaderWidget for a tableview, containing the title, the search widget,
    and the number of rows in the table"""

    search_widget = SimpleSearchControl
    rows_widget = RowsWidget

    filters_changed_signal = QtCore.pyqtSignal()

    _title_font = QtGui.QApplication.font()
    _title_font.setBold( True )

    def __init__( self, parent, admin ):
        QtGui.QWidget.__init__( self, parent )
        assert object_thread( self )
        self._admin = admin
        layout = QtGui.QVBoxLayout()
        widget_layout = QtGui.QHBoxLayout()
        search = self.search_widget( self )
        search.expand_search_options_signal.connect(
            self.expand_search_options )
        title = UserTranslatableLabel( admin.get_verbose_name_plural(),
                                       self )
        title.setFont( self._title_font )
        widget_layout.addWidget( title )
        widget_layout.addWidget( search )
        if self.rows_widget:
            self.number_of_rows = self.rows_widget( self )
            widget_layout.addWidget( self.number_of_rows )
        else:
            self.number_of_rows = None
        layout.addLayout( widget_layout, 0 )
        self._expanded_filters_created = False
        self._expanded_search = QtGui.QWidget()
        self._expanded_search.hide()
        layout.addWidget( self._expanded_search, 1 )
        self.setLayout( layout )
        self.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed )
        self.setNumberOfRows( 0 )
        self.search = search

    def _fill_expanded_search_options(self, columns):
        """Given the columns in the table view, present the user
        with more options to filter rows in the table
        :param columns: a list of tuples with field names and attributes
        """
        assert object_thread( self )
        from camelot.view.controls.filter_operator import FilterOperator
        from camelot.view.flowlayout import FlowLayout
        layout = FlowLayout()
        layout.setSpacing( 2 )
        layout.setContentsMargins( 0, 0, 0, 0 )
        for i, (field, attributes) in enumerate(columns):
            if 'operators' in attributes and attributes['operators']:
                box = QtGui.QGroupBox()
                box_layout = QtGui.QVBoxLayout()
                box_layout.setContentsMargins( 1, 1, 1, 1 )
                widget = FilterOperator( self._admin.entity,
                                         field, attributes,
                                         box )
                box_layout.addWidget( widget )
                box.setLayout( box_layout )
                widget.filter_changed_signal.connect( self._filter_changed )
                layout.addWidget( box )
        #layout.addStretch()
        self._expanded_search.setLayout( layout )
        self._expanded_filters_created = True

    def _filter_changed(self):
        assert object_thread( self )
        self.filters_changed_signal.emit()

    def decorate_query(self, query):
        """Apply expanded filters on the query"""
        if self._expanded_filters_created:
            for i in range(self._expanded_search.layout().count()):
                box = self._expanded_search.layout().itemAt(i).widget()
                if box:
                    widget = box.layout().itemAt(0).widget()
                    if widget:
                        query = widget.decorate_query(query)
        return query

    @QtCore.pyqtSlot()
    def expand_search_options(self):
        assert object_thread( self )
        if self._expanded_search.isHidden():
            if not self._expanded_filters_created:
                post( self._admin.get_expanded_search_fields, 
                      self._fill_expanded_search_options )
            self._expanded_search.show()
        else:
            self._expanded_search.hide()

    def setNumberOfRows( self, rows ):
        assert object_thread( self )
        if self.number_of_rows:
            self.number_of_rows.setNumberOfRows( rows )

class SplitterHandle( QtGui.QSplitterHandle ):
    """Custom implementation of QSplitterHandle to provide more functions, 
    such as hiding a widget by clicking the handle"""
    
    def __init__ (self, orientation, splitter, widget_to_hide = None):
        super(SplitterHandle, self).__init__ (orientation, splitter)
        assert object_thread( self )
        self.setToolTip('Click to close')
        self._widget_to_hide = widget_to_hide
        
    def mousePressEvent(self, event):
        assert object_thread( self )
        splitter = self.splitter()
        splitter.widget( splitter.count() - 1 ).hide()
        
class Splitter(QtGui.QSplitter):
    """Custom implementation of QSplitter to use the custom SplitterHandle"""
    
    def createHandle(self):
        assert object_thread( self )
        return SplitterHandle( self.orientation(), self, self._widget_to_hide )
    
class TableView( AbstractView  ):
    """
  :param gui_context: a :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`
      object.
  :param admin: an :class:`camelot.admin.entity_admin.EntityAdmin` object
  :param search_text: a predefined search text to put in the search widget
  :param parent: a :class:`QtGui.QWidget` object
  
  A generic tableview widget that puts together some other widgets.  The behaviour of this class and
  the resulting interface can be tuned by specifying specific class attributes which define the underlying
  widgets used ::

    class MovieRentalTableView(TableView):
      title_format = 'Grand overview of recent movie rentals'

  The attributes that can be specified are :

  .. attribute:: header_widget

  The widget class to be used as a header in the table view::

    header_widget = HeaderWidget

  .. attribute:: table_widget

  The widget class used to display a table within the table view ::

  table_widget = TableWidget

  .. attribute:: title_format

  A string used to format the title of the view ::

  title_format = '%(verbose_name_plural)s'

  .. attribute:: table_model

  A class implementing QAbstractTableModel that will be used as a model for the table view ::

    table_model = QueryTableProxy

  - emits the row_selected signal when a row has been selected
  """

    header_widget = HeaderWidget
    AdminTableWidget = AdminTableWidget

    #
    # The proxy class to use
    #
    table_model = QueryTableProxy
    #
    # Format to use as the window title
    #
    title_format = '%(verbose_name_plural)s'

    row_selected_signal = QtCore.pyqtSignal(int)

    def __init__( self, 
                  gui_context, 
                  admin, 
                  search_text = None, 
                  parent = None ):
        super(TableView, self).__init__( parent )
        assert object_thread( self )
        self.admin = admin
        self.application_gui_context = gui_context
        self.gui_context = gui_context
        post( self.get_title, self.change_title )
        widget_layout = QtGui.QVBoxLayout()
        if self.header_widget:
            self.header = self.header_widget( self, admin )
            widget_layout.addWidget( self.header )
            self.header.search.search_signal.connect( self.startSearch )
            self.header.search.cancel_signal.connect( self.cancelSearch )
            self.header.search.on_arrow_down_signal.connect(self.focusTable)
            if search_text:
                self.header.search.search( search_text )
        else:
            self.header = None
        widget_layout.setSpacing( 0 )
        widget_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QtGui.QSplitter( self )
        splitter.setObjectName('splitter')
        widget_layout.addWidget( splitter )
        table_widget = QtGui.QWidget( self )
        filters_widget = QtGui.QWidget( self )
        self.table_layout = QtGui.QVBoxLayout()
        self.table_layout.setSpacing( 0 )
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = None
        self.filters_layout = QtGui.QVBoxLayout()
        self.filters_layout.setSpacing( 0 )
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.actions = None
        table_widget.setLayout( self.table_layout )
        filters_widget.setLayout( self.filters_layout )
        #filters_widget.hide()
        self.set_admin( admin )
        splitter.addWidget( table_widget )
        splitter.addWidget( filters_widget )
        self.setLayout( widget_layout )
        self.search_filter = lambda q: q
        shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Find), self)
        shortcut.activated.connect( self.activate_search )
        if self.header_widget:
            self.header.filters_changed_signal.connect( self.rebuild_query )
        # give the table widget focus to prevent the header and its search control to
        # receive default focus, as this would prevent the displaying of 'Search...' in the
        # search control, but this conflicts with the MDI, resulting in the window not
        # being active and the menus not to work properly
        #table_widget.setFocus( QtCore.Qt.OtherFocusReason )
        #self.setFocusProxy(table_widget)
        #self.setFocus( QtCore.Qt.OtherFocusReason )
        post( self.admin.get_subclass_tree, self.setSubclassTree )

    @QtCore.pyqtSlot()
    def activate_search(self):
        assert object_thread( self )
        self.header.search.setFocus(QtCore.Qt.ShortcutFocusReason)

    @model_function
    def get_title( self ):
        return self.title_format % {'verbose_name_plural':self.admin.get_verbose_name_plural()}

    @QtCore.pyqtSlot(object)
    def setSubclassTree( self, subclasses ):
        assert object_thread( self )
        if len( subclasses ) > 0:
            from inheritance import SubclassTree
            splitter = self.findChild(QtGui.QWidget, 'splitter' )
            class_tree = SubclassTree( self.admin, splitter )
            splitter.insertWidget( 0, class_tree )
            class_tree.subclass_clicked_signal.connect( self.set_admin )

    @QtCore.pyqtSlot(int)
    def sectionClicked( self, section ):
        """emits a row_selected signal"""
        assert object_thread( self )
        #
        # close the table editor before opening a form or such
        #
        # Qt seems to crash in certain cases when the editor is open and the
        # underlying model is changed
        #
        if self.table:
            self.table.close_editor()
        self.admin.list_action.gui_run( self.gui_context )

    def create_table_model( self, admin ):
        """Create a table model for the given admin interface"""
        return self.table_model( admin,
                                 None,
                                 admin.get_columns )

    def get_admin(self):
        return self.admin

    def get_model(self):
        return self.table.model()

    @QtCore.pyqtSlot( object )
    def set_admin( self, admin ):
        """Switch to a different subclass, where admin is the admin object of the
        subclass"""
        assert object_thread( self )
        logger.debug('set_admin called')
        self.admin = admin
        if self.table:
            self.table.model().layoutChanged.disconnect( self.tableLayoutChanged )
            self.table_layout.removeWidget(self.table)
            self.table.deleteLater()
            self.table.model().deleteLater()
        splitter = self.findChild( QtGui.QWidget, 'splitter' )
        self.table = self.AdminTableWidget( self.admin, splitter )
        self.table.setObjectName('AdminTableWidget')
        new_model = self.create_table_model( admin )
        self.table.setModel( new_model )
        self.table.verticalHeader().sectionClicked.connect( self.sectionClicked )
        self.table.keyboard_selection_signal.connect(self.on_keyboard_selection_signal)
        self.table.model().layoutChanged.connect( self.tableLayoutChanged )
        self.tableLayoutChanged()
        self.table_layout.insertWidget( 1, self.table )
        self.gui_context = self.application_gui_context.copy( ListActionGuiContext )
        self.gui_context.view = self
        self.gui_context.admin = self.admin
        self.gui_context.item_view = self.table

        def get_filters_and_actions():
            return ( admin.get_filters(), admin.get_list_actions() )

        post( get_filters_and_actions,  self.set_filters_and_actions )

    @QtCore.pyqtSlot()
    def on_keyboard_selection_signal(self):
        assert object_thread( self )
        self.sectionClicked( self.table.currentIndex().row() )

    @QtCore.pyqtSlot()
    def tableLayoutChanged( self ):
        assert object_thread( self )
        logger.debug('tableLayoutChanged')
        model = self.table.model()
        if self.header:
            self.header.setNumberOfRows( model.rowCount() )
        item_delegate = model.getItemDelegate()
        if item_delegate:
            self.table.setItemDelegate( item_delegate )
        for i in range( model.columnCount() ):
            self.table.setColumnWidth( i, model.headerData( i, Qt.Horizontal, Qt.SizeHintRole ).toSize().width() )

    def closeEvent( self, event ):
        """reimplements close event"""
        assert object_thread( self )
        logger.debug( 'tableview closed' )
        event.accept()

    def selectTableRow( self, row ):
        """selects the specified row"""
        assert object_thread( self )
        self.table.selectRow( row )

    def getColumns( self ):
        """return the columns to be displayed in the table view"""
        assert object_thread( self )
        return self.admin.get_columns()

    def getTitle( self ):
        """return the name of the entity managed by the admin attribute"""
        return self.admin.get_verbose_name()

    @QtCore.pyqtSlot(object)
    def _set_query(self, query_getter):
        assert object_thread( self )
        if isinstance(self.table.model(), QueryTableProxy):
            self.table.model().setQuery(query_getter)
        self.table.clearSelection()

    @QtCore.pyqtSlot()
    def refresh(self):
        """Refresh the whole view"""
        assert object_thread( self )
        post( self.get_admin, self.set_admin )

    @QtCore.pyqtSlot()
    def rebuild_query( self ):
        """resets the table model query"""
        from filterlist import FilterList

        def rebuild_query():
            query = self.admin.get_query()
            # a table view is not required to have a header
            if self.header:
                query = self.header.decorate_query(query)
            filters = self.findChild(FilterList, 'filters')
            if filters:
                query = filters.decorate_query( query )
            if self.search_filter:
                query = self.search_filter( query )
            query_getter = lambda:query
            return query_getter

        post( rebuild_query, self._set_query )

    @QtCore.pyqtSlot(str)
    def startSearch( self, text ):
        """rebuilds query based on filtering text"""
        assert object_thread( self )
        from camelot.view.search import create_entity_search_query_decorator
        logger.debug( 'search %s' % text )
        self.search_filter = create_entity_search_query_decorator( self.admin, unicode(text) )
        self.rebuild_query()

    @QtCore.pyqtSlot()
    def cancelSearch( self ):
        """resets search filtering to default"""
        assert object_thread( self )
        logger.debug( 'cancel search' )
        self.search_filter = lambda q: q
        self.rebuild_query()

    @QtCore.pyqtSlot(object)
    def set_filters_and_actions( self, filters_and_actions ):
        """sets filters for the tableview"""
        assert object_thread( self )
        filters, actions = filters_and_actions
        from camelot.view.controls.filterlist import FilterList
        from camelot.view.controls.actionsbox import ActionsBox
        logger.debug( 'setting filters for tableview' )
        filters_widget = self.findChild(FilterList, 'filters')
        actions_widget = self.findChild(ActionsBox, 'actions')
        if filters_widget:
            filters_widget.filters_changed_signal.disconnect( self.rebuild_query )
            self.filters_layout.removeWidget(filters_widget)
            filters_widget.deleteLater()
        if actions_widget:
            self.filters_layout.removeWidget(actions_widget)
            actions_widget.deleteLater()
        if filters:
            splitter = self.findChild( QtGui.QWidget, 'splitter' )
            filters_widget = FilterList( filters, parent=splitter )
            filters_widget.setObjectName('filters')
            self.filters_layout.addWidget( filters_widget )
            filters_widget.filters_changed_signal.connect( self.rebuild_query )
        #
        # filters might have default values, so we can only build the queries now
        #
        self.rebuild_query()
        if actions:
            actions_widget = ActionsBox( parent = self,
                                         gui_context = self.gui_context )
            actions_widget.setObjectName( 'actions' )
            actions_widget.set_actions( actions )
            self.filters_layout.addWidget( actions_widget )

    @QtCore.pyqtSlot()
    def focusTable(self):
        assert object_thread( self )
        if self.table and self.table.model().rowCount() > 0:
            self.table.setFocus()
            self.table.selectRow(0)

