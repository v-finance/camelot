import json
import logging
import typing

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field
from typing import List, Tuple

from ...admin.admin_route import Route
from ...admin.action.base import ActionStep, State
from ...admin.icon import CompletionValue
from ...core.naming import NameNotFoundException
from ...core.qt import Qt, QtGui, QtCore, is_deleted
from ...core.serializable import DataclassSerializable, json_encoder
from ...core.item_model import (
    CompletionsRole, ColumnAttributesRole,
)
from .. import gui_naming_context
from ..controls import delegates
from camelot.view.crud_action import DataUpdate

def filter_attributes(attributes, keys):
    filtered = {}
    for key in keys:
        if key in attributes:
            filtered[key] = attributes[key]
    return filtered


class CrudActionStep(ActionStep, DataclassSerializable):
    """Helper class to implement ActionSteps that require access to the item model"""

    @classmethod
    def gui_run(cls, gui_context_name, serialized_step):
        try:
            item_model = gui_naming_context.resolve(gui_context_name)
        except NameNotFoundException:
            return
        if is_deleted(item_model):
            return
        return cls._update_item_model(item_model, json.loads(serialized_step))

@dataclass
class RowCount(CrudActionStep):

    blocking = False
    rows: typing.Optional[int] = None

    @classmethod
    def _update_item_model(cls, item_model, step):
        if step["rows"] is not None:
            item_model._refresh_content(step["rows"])

class SetColumns(ActionStep):
    
    blocking = False
    
    def __init__(self, static_field_attributes):
        self.static_field_attributes = static_field_attributes
        self.column_attributes = []
        for fa in static_field_attributes:
            attrs = {}
            if issubclass(fa['delegate'], (delegates.ComboBoxDelegate, delegates.Many2OneDelegate,
                                           delegates.FileDelegate)):
                attrs = filter_attributes(fa, ['action_routes'])
            elif issubclass(fa['delegate'], delegates.DateDelegate):
                attrs = filter_attributes(fa, ['nullable'])
                if issubclass(fa['delegate'], delegates.DateTimeDelegate):
                    if 'editable' in fa:
                        attrs['editable'] = fa['editable']
            elif issubclass(fa['delegate'], delegates.DbImageDelegate):
                attrs = filter_attributes(fa, ['preview_width', 'preview_height', 'max_size'])
            elif issubclass(fa['delegate'], delegates.FloatDelegate):
                attrs = filter_attributes(fa, ['calculator', 'decimal', 'action_routes'])
            elif issubclass(fa['delegate'], delegates.IntegerDelegate):
                attrs = filter_attributes(fa, ['calculator', 'decimal'])
            elif issubclass(fa['delegate'], delegates.LabelDelegate):
                attrs = filter_attributes(fa, ['text'])
            elif issubclass(fa['delegate'], delegates.LocalFileDelegate):
                attrs = filter_attributes(fa, ['directory', 'save_as', 'file_filter'])
            elif issubclass(fa['delegate'], delegates.MonthsDelegate):
                attrs = filter_attributes(fa, ['minimum', 'maximum'])
            elif issubclass(fa['delegate'], delegates.One2ManyDelegate):
                attrs = filter_attributes(fa, ['admin_route', 'column_width', 'columns', 'rows',
                                                    'action_routes', 'list_actions', 'list_action'])
            elif issubclass(fa['delegate'], delegates.PlainTextDelegate):
                attrs = filter_attributes(fa, ['length', 'echo_mode', 'column_width', 'action_routes', 'validator_type', 'completer_type'])
            elif issubclass(fa['delegate'], delegates.TextEditDelegate):
                attrs = filter_attributes(fa, ['length', 'editable'])
            elif issubclass(fa['delegate'], delegates.VirtualAddressDelegate):
                attrs = filter_attributes(fa, ['address_type'])
            self.column_attributes.append(attrs)

    def _to_dict(self):
        columns = []
        for i, fa in enumerate(self.static_field_attributes):
            columns.append({
                'verbose_name': str(fa['name']),
                'field_name': fa['field_name'],
                'width': fa['column_width'],
                'delegate': [fa['delegate'].__name__, self.column_attributes[i]],
                'nullable': fa.get('nullable', True)
            })
        return {
            'columns': columns,
        }

    def gui_run(self, gui_context_name):
        item_model = gui_naming_context.resolve(gui_context_name)
        if is_deleted(item_model):
            return
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
            set_header_data(field_name, Qt.ItemDataRole.UserRole)
            set_header_data(verbose_name, Qt.ItemDataRole.DisplayRole)
            set_header_data([fa['delegate'].__name__, self.column_attributes[i]], ColumnAttributesRole)
            if fa.get( 'nullable', True ) == False:
                set_header_data(item_model._header_font_required, Qt.ItemDataRole.FontRole)
            else:
                set_header_data(item_model._header_font, Qt.ItemDataRole.FontRole)

            # the value returned from settings might be a string representing a
            # float (on Winblows)
            settings_width = int(float(item_model.settings.value(field_name, 0)))
            if settings_width > 0:
                width = settings_width
            else:
                width = fa['column_width'] * char_width
            header_item.setData( QtCore.QSize( width, item_model._horizontal_header_height ),
                                 Qt.ItemDataRole.SizeHintRole )
            item_model.setHorizontalHeaderItem( i, header_item )
        item_model.settings.endGroup()
        item_model.settings.endGroup()
        item_model.endResetModel()

@dataclass
class Completion(CrudActionStep):
    
    blocking = False
    row: int
    column: int
    prefix: str
    completions: typing.List[CompletionValue]

    @classmethod
    def _update_item_model(cls, item_model, step):
        root_item = item_model.invisibleRootItem()
        if is_deleted(root_item):
            return
        logger.debug('begin gui update {0} completions'.format(len(step['completions'])))
        child = root_item.child(step['row'], step['column'])
        if child is not None:
            # calling setData twice triggers dataChanged twice, resulting in
            # the editors state being updated twice
            #child.setData(self.prefix, CompletionPrefixRole)
            completions = [{
                # Use user role for object to avoid display role / edit role confusion
                Qt.ItemDataRole.UserRole: completion['value'],
                Qt.ItemDataRole.DisplayRole: completion['verbose_name'],
                Qt.ItemDataRole.ToolTipRole: completion['tooltip']} for completion in step['completions']]
            child.setData(completions, CompletionsRole)
        logger.debug('end gui update rows {0}, column {1}'.format(step['row'], step['column']))

@dataclass
class Created(ActionStep, DataUpdate):
    
    blocking = False
        
@dataclass
class Update(ActionStep, DataUpdate):
        
    blocking = False

@dataclass
class ChangeSelection(CrudActionStep):

    blocking = False

    action_states: List[Tuple[Route, State]] = field(default_factory=list)

    @classmethod
    def _update_item_model(cls, item_model, step):
        for route, state in step["action_states"]:
            item_model.action_state_changed_cpp_signal.emit(
                route, json_encoder.encode(state).encode('utf-8')
            )

crud_action_steps = (
    RowCount, SetColumns, Completion, Created, Update, ChangeSelection
)
