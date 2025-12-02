from camelot.admin.admin_route import Route
from camelot.admin.icon import Icon
from camelot.core.item_model import (
    ObjectRole, PreviewRole,
    ActionRoutesRole, ActionStatesRole, CompletionsRole,
    ActionModeRole, FocusPolicyRole,
    VisibleRole, NullableRole, IsStatusRole
)
from camelot.core.qt import Qt, QtGui
from camelot.core.serializable import DataclassSerializable

from dataclasses import dataclass, field, InitVar
from typing import Any, Dict, List, Optional

@dataclass
class DataCell(DataclassSerializable):

    row: int = -1
    column: int = -1
    flags: int = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable

    roles: Dict[int, Any] = field(default_factory=dict)

    # used in camelot tests
    def get_standard_item(self):
        item = QtGui.QStandardItem()
        item.setFlags(self.flags)
        for role, value in self.roles.items():
            item.setData(value, role)
        return item


@dataclass
class DataRowHeader(DataclassSerializable):

    row: int = -1
    tool_tip: Optional[str] = None
    icon_name: Optional[str] = None
    object: int = 0
    verbose_identifier: str = ''
    valid: bool = True
    message: str = ''
    decoration: Optional[Icon] = None
    display: Optional[str] = None


@dataclass
class DataUpdate(DataclassSerializable):

    changed_ranges: InitVar

    header_items: List[DataRowHeader] = field(default_factory=list)
    cells: List[DataCell] = field(default_factory=list)

    def __post_init__(self, changed_ranges):
        for row, header_item, items in changed_ranges:
            self.header_items.append(header_item)
            self.cells.extend(items)


invalid_item = DataCell()
invalid_item.flags = Qt.ItemFlag.NoItemFlags
invalid_item.roles[Qt.ItemDataRole.EditRole] = None
invalid_item.roles[PreviewRole] = None
invalid_item.roles[ObjectRole] = None
invalid_item.roles[CompletionsRole] = None
invalid_item.roles[ActionRoutesRole] = '[]'
invalid_item.roles[ActionStatesRole] = '[]'
invalid_item.roles[ActionModeRole] = None
invalid_item.roles[FocusPolicyRole] = Qt.FocusPolicy.NoFocus
invalid_item.roles[VisibleRole] = True
invalid_item.roles[NullableRole] = True
invalid_item.roles[IsStatusRole] = False



@dataclass
class CrudActions(DataclassSerializable):
    """
    A data class which contains the routes to crud actions available
    to the gui to invoke.
    """

    admin: InitVar
    set_columns: Route = field(init=False, default=('crud_action', 'set_columns'))
    row_count: Route = field(init=False, default=('crud_action', 'row_count'))
    row_data: Route = field(init=False, default=('crud_action', 'row_data'))
    set_data: Route = field(init=False, default=('crud_action', 'set_data'))
    change_selection: Route = field(init=False, default=('crud_action', 'change_selection'))
    update: Route = field(init=False, default=('crud_action', 'update'))
    deleted: Route = field(init=False, default=('crud_action', 'deleted'))
    created: Route = field(init=False, default=('crud_action', 'created'))
    sort: Route = field(init=False, default=('crud_action', 'sort'))
    field_action: Route = field(init=False, default=('crud_action', 'field_action'))
    completion: Route = field(init=False, default=('crud_action', 'completion'))
    refresh: Route = field(init=False, default=('crud_action', 'refresh'))
