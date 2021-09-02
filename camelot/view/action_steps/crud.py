import logging

logger = logging.getLogger(__name__)
    
from ...admin.action.base import ActionStep
from ...core.qt import Qt, QtGui, QtCore, py_to_variant, variant_to_py, is_deleted
from ...core.item_model import FieldAttributesRole, CompletionPrefixRole, CompletionsRole

class UpdateMixin(object):
    
    def update_item_model(self, item_model):
        root_item = item_model.invisibleRootItem()
        if is_deleted(root_item):
            return
        logger.debug('begin gui update {0} rows'.format(len(self.changed_ranges)))
        row_range = (item_model.rowCount(), -1)
        column_range = (item_model.columnCount(), -1)
        for row, header_item, items in self.changed_ranges:
            row_range = (min(row, row_range[0]), max(row, row_range[1]))
            # Setting the vertical header item causes the table to scroll
            # back to its open editor.  However setting the header item every
            # time data has changed is needed to signal other parts of the
            # gui that the object itself has changed.
            item_model.setVerticalHeaderItem(row, header_item)
            for column, item in items:
                column_range = (min(column, column_range[0]), max(column, column_range[1]))
                root_item.setChild(row, column, item)
        
        logger.debug('end gui update rows {0}, columns {1}'.format(row_range, column_range))    


class RowCount(ActionStep):
    
    def __init__(self, rows):
        self.rows = rows   
    
    def gui_run(self, item_model):
        if self.rows is not None:
            item_model._refresh_content(self.rows)    

class SetColumns(ActionStep):
    
    def __init__(self, static_field_attributes):
        self.static_field_attributes = static_field_attributes
        
    def gui_run(self, item_model):
        item_model.beginResetModel()
        item_model.settings.beginGroup( 'column_width' )
        item_model.settings.beginGroup( '0' )
        #
        # this loop can take a while to complete
        #
        font_metrics = QtGui.QFontMetrics(item_model._header_font_required)
        char_width = font_metrics.averageCharWidth()
        #
        # increase the number of columns at once, since this is slow, and
        # setHorizontalHeaderItem will increase the number of columns one by one
        #
        item_model.setColumnCount(len(self.static_field_attributes))
        for i, fa in enumerate(self.static_field_attributes):
            verbose_name = str(fa['name'])
            field_name = fa['field_name']
            header_item = QtGui.QStandardItem()
            set_header_data = header_item.setData
            #
            # Set the header data
            #
            fa_copy = fa.copy()
            fa_copy.setdefault('editable', True)
            set_header_data(py_to_variant(field_name), Qt.UserRole)
            set_header_data(py_to_variant(verbose_name), Qt.DisplayRole)
            set_header_data(fa_copy, FieldAttributesRole)
            if fa.get( 'nullable', True ) == False:
                set_header_data(item_model._header_font_required, Qt.FontRole)
            else:
                set_header_data(item_model._header_font, Qt.FontRole)

            settings_width = int( variant_to_py( item_model.settings.value( field_name, 0 ) ) )
            if settings_width > 0:
                width = settings_width
            else:
                width = fa['column_width'] * char_width
            header_item.setData( py_to_variant( QtCore.QSize( width, item_model._horizontal_header_height ) ),
                                 Qt.SizeHintRole )
            item_model.setHorizontalHeaderItem( i, header_item )
        item_model.settings.endGroup()
        item_model.settings.endGroup()
        item_model.endResetModel()    
 

class Completion(ActionStep):
    
    def __init__(self, row, column, prefix, completion):
        self.row = row
        self.column = column
        self.prefix = prefix
        self.completions = completion        
        
    def gui_run(self, item_model):
        root_item = item_model.invisibleRootItem()
        if is_deleted(root_item):
            return
        logger.debug('begin gui update {0} completions'.format(len(self.completions)))
        child = root_item.child(self.row, self.column)
        if child is not None:
            child.setData(self.prefix, CompletionPrefixRole)
            child.setData(self.completions, CompletionsRole)
        logger.debug('end gui update rows {0.row}, column {0.column}'.format(self))


class Created(ActionStep, UpdateMixin):
    
    def __init__(self, changed_ranges):
        self.changed_ranges = changed_ranges
        
    def gui_run(self, item_model):
        # appending new items to the model will increase the rowcount, so
        # there is no need to set the rowcount explicitly
        self.update_item_model(item_model)    