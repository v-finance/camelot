import logging
import typing

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field, InitVar
from enum import Enum
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


class DelegateType(str, Enum):

    ENUM = "EnumDelegate"
    COMBO_BOX = "ComboBoxDelegate"
    MANY2ONE = "Many2OneDelegate"
    FILE = "FileDelegate"
    DATE = "DateDelegate"
    DATETIME = "DateTimeDelegate"
    DB_IMAGE = "DbImageDelegate"
    FLOAT = "FloatDelegate"
    INTEGER = "IntegerDelegate"
    LABEL = "LabelDelegate"
    LOCAL_FILE = "LocalFileDelegate"
    MONTHS = "MonthsDelegate"
    ONE2MANY = "One2ManyDelegate"
    PLAIN_TEXT = "PlainTextDelegate"
    TEXT_EDIT = "TextEditDelegate"
    BOOL = "BoolDelegate"
    COLOR = "ColorDelegate"
    LANGUAGE = "LanguageDelegate"
    RICH_TEXT = "RichTextDelegate"
    STATUS = "StatusDelegate"
    NOTE = "NoteDelegate"

    def __str__(self) -> str:
        return self.value

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
        delegate_type = fa['delegate'].delegate_type
        attrs = {}
        if delegate_type in (DelegateType.ENUM, DelegateType.STATUS):
            attrs = filter_attributes(fa, ['action_routes'])
            # TODO: no specifics about the delegate implementation should leak here, to be reworked.
            attrs['choices'] = fa['delegate'].get_choices_data(
                fa['types'].get_choices()
            )
        elif delegate_type == DelegateType.COMBO_BOX:
            attrs = filter_attributes(fa, ['action_routes'])
        elif delegate_type in (DelegateType.MANY2ONE, DelegateType.FILE):
            attrs = filter_attributes(fa, ['action_routes'])
        elif delegate_type in (DelegateType.DATE, DelegateType.DATETIME):
            attrs = filter_attributes(fa, ['nullable'])
            if delegate_type == DelegateType.DATETIME:
                if 'editable' in fa:
                    attrs['editable'] = fa['editable']
        elif delegate_type == DelegateType.DB_IMAGE:
            attrs = filter_attributes(fa, ['preview_width', 'preview_height', 'max_size'])
        elif delegate_type == DelegateType.FLOAT:
            attrs = filter_attributes(fa, ['calculator', 'decimal', 'action_routes'])
        elif delegate_type == DelegateType.INTEGER:
            attrs = filter_attributes(fa, ['calculator', 'decimal'])
        elif delegate_type == DelegateType.LABEL:
            attrs = filter_attributes(fa, ['text', 'field_name'])
        elif delegate_type == DelegateType.LOCAL_FILE:
            attrs = filter_attributes(fa, ['directory', 'save_as', 'file_filter'])
        elif delegate_type == DelegateType.MONTHS:
            attrs = filter_attributes(fa, ['minimum', 'maximum', 'forever', 'action_routes'])
        elif delegate_type == DelegateType.ONE2MANY:
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
        elif delegate_type in (DelegateType.PLAIN_TEXT, DelegateType.LANGUAGE):
            attrs = filter_attributes(fa, ['length', 'echo_mode', 'column_width', 'action_routes', 'validator_type', 'completer_type'])
        elif delegate_type in (DelegateType.TEXT_EDIT, DelegateType.NOTE):
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
