import logging
import typing

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field, InitVar
from typing import List, Dict, Tuple, ClassVar, Any

from ...admin.admin_route import Route
from ...admin.action.base import ActionStep, State
from ...admin.icon import CompletionValue
from ...core.serializable import DataclassSerializable
from ..crud_action import CrudActions
from ...view.crud_action import DataUpdate
from ...view.utils import get_settings_group


def filter_attributes(attributes, keys):
    filtered = {}
    for key in keys:
        if key in attributes:
            filtered[key] = attributes[key]
    return filtered


@dataclass
class RowCount(ActionStep, DataclassSerializable):

    blocking: ClassVar[bool] = False

    rows: typing.Optional[int] = None


@dataclass
class DataColumn(ActionStep, DataclassSerializable):

    field_name: str
    verbose_name: str
    nullable: bool
    width: int
    delegate_type: str
    delegate_state: Dict[str, Any]
    default_visible: bool # TableView


@dataclass
class SetColumns(ActionStep, DataclassSerializable):

    blocking: ClassVar[bool] = False

    admin: InitVar[Any]
    static_field_attributes: InitVar[Any]

    columns: List[DataColumn] = field(default_factory=list)

    def __post_init__(self, admin, static_field_attributes):
        columns = admin.get_columns()
        for fa in static_field_attributes:
            field_name = fa['field_name']
            self.columns.append(DataColumn(
                field_name = field_name,
                verbose_name = str(fa['name']),
                nullable = fa.get('nullable', True),
                width = fa['column_width'],
                delegate_type = fa['delegate'].__name__,
                delegate_state = self.get_delegate_state(fa),
                default_visible = field_name in columns
            ))

    def get_delegate_state(self, static_field_attributes):
        fa = static_field_attributes
        delegate_type = fa['delegate'].__name__
        attrs = {}
        if delegate_type == 'EnumDelegate':
            attrs = filter_attributes(fa, ['action_routes'])
            # TODO: no specifics about the delegate implementation should leak here, to be reworked.
            attrs['choices'] = fa['delegate'].get_choices_data(
                fa['types'].get_choices()
            )
        elif delegate_type == 'ComboBoxDelegate':
            attrs = filter_attributes(fa, ['action_routes'])
        elif delegate_type in ('Many2OneDelegate', 'FileDelegate'):
            attrs = filter_attributes(fa, ['action_routes'])
        elif delegate_type in ('DateDelegate', 'DateTimeDelegate'):
            attrs = filter_attributes(fa, ['nullable'])
            if delegate_type == 'DateTimeDelegate':
                if 'editable' in fa:
                    attrs['editable'] = fa['editable']
        elif delegate_type == 'DbImageDelegate':
            attrs = filter_attributes(fa, ['preview_width', 'preview_height', 'max_size'])
        elif delegate_type == 'FloatDelegate':
            attrs = filter_attributes(fa, ['calculator', 'decimal', 'action_routes'])
        elif delegate_type == 'IntegerDelegate':
            attrs = filter_attributes(fa, ['calculator', 'decimal'])
        elif delegate_type == 'LabelDelegate':
            attrs = filter_attributes(fa, ['text', 'field_name'])
        elif delegate_type == 'LocalFileDelegate':
            attrs = filter_attributes(fa, ['directory', 'save_as', 'file_filter'])
        elif delegate_type == 'MonthsDelegate':
            attrs = filter_attributes(fa, ['minimum', 'maximum', 'forever', 'action_routes'])
        elif delegate_type == 'One2ManyDelegate':
            attrs = filter_attributes(fa, ['admin_route', 'column_width', 'columns', 'rows',
                                                'action_routes', 'list_actions', 'list_action',
                                                'drop_action_route'])
            attrs['group'] = get_settings_group(attrs['admin_route'])
            attrs['crud_actions'] = CrudActions(None) # FIXME: admin arg
            # define default states for actions when the model itself is not yet known
            list_actions_states = []
            for list_action in attrs.get('list_actions', []):
                list_actions_states.append((
                    list_action.route, State()
                ))
            attrs['list_actions_states'] = list_actions_states
        elif delegate_type == 'PlainTextDelegate':
            attrs = filter_attributes(fa, ['length', 'echo_mode', 'column_width', 'action_routes', 'validator_type', 'completer_type'])
        elif delegate_type == 'TextEditDelegate':
            attrs = filter_attributes(fa, ['length', 'editable'])
        return attrs

@dataclass
class Completion(ActionStep, DataclassSerializable):

    blocking: ClassVar[bool] = False

    row: int
    column: int
    prefix: str
    completions: typing.List[CompletionValue]

@dataclass
class Created(ActionStep, DataUpdate):

    blocking: ClassVar[bool] = False

@dataclass
class Update(ActionStep, DataUpdate):

    blocking: ClassVar[bool] = False

@dataclass
class ChangeSelection(ActionStep, DataclassSerializable):

    blocking: ClassVar[bool] = False

    action_states: List[Tuple[Route, State]] = field(default_factory=list)
