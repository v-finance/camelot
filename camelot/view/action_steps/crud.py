import logging

logger = logging.getLogger(__name__)
    
from ...admin.action.base import ActionStep
from ...core.qt import Qt, QtGui, QtCore, py_to_variant, variant_to_py, is_deleted
from ...core.item_model import FieldAttributesRole, CompletionPrefixRole, CompletionsRole

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
    