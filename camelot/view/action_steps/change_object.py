#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
import typing

from dataclasses import dataclass, field
import json
from typing import List, Union

from camelot.admin.action.base import GuiContext
from camelot.admin.icon import Icon
from camelot.core.exception import CancelRequest
from camelot.core.item_model import ValidRole, ValidMessageRole
from camelot.core.naming import initial_naming_context
from camelot.core.utils import ugettext, ugettext_lazy, ugettext_lazy as _
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.art import from_admin_icon
from camelot.view.controls import editors
from camelot.view.controls.formview import FormWidget
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage
from camelot.view.qml_view import get_qml_root_backend
from camelot.view.utils import get_settings_group

from .form_view import OpenFormView
from .item_view import UpdateTableView
from .. import gui_naming_context
from ..controls.view import ViewWithActionsMixin
from ..workspace import apply_form_state
from ...admin.action import RenderHint
from ...admin.admin_route import AdminRoute, RouteWithRenderHint
from ...core.qt import QtCore, QtWidgets, Qt


class ChangeObjectDialog(StandaloneWizardPage, ViewWithActionsMixin, GuiContext):
    """A dialog to change an object.  This differs from a FormView in that
    it does not contains Actions, and has an OK button that is enabled when
    the object is valid.

    :param obj: The object to change
    :param admin: The admin class used to create a form

    .. image:: /_static/actionsteps/change_object.png
    """

    def __init__( self,
                  proxy_route,
                  admin_route,
                  title,
                  form_display,
                  fields,
                  form_actions,
                  action_states,
                  accept,
                  reject,
                  icon = Icon('cog'), # 'tango/22x22/categories/preferences-system.png'
                  parent=None,
                  flags=QtCore.Qt.WindowType.Dialog ):
        super(ChangeObjectDialog, self).__init__( '', parent, flags )
        self.setWindowTitle( title )
        self.set_banner_logo_pixmap( from_admin_icon(icon).getQPixmap() )
        self.banner_widget().setStyleSheet('background-color: white;')

        layout = QtWidgets.QHBoxLayout()
        layout.setObjectName( 'form_and_actions_layout' )
        form_widget = FormWidget(
            admin_route=admin_route, model=None, form_display=form_display,
            fields=fields, parent=self
        )

        model = get_qml_root_backend().createModel(get_settings_group(admin_route), form_widget)
        self.action_routes = dict()
        form_widget.set_model(model)

        note_layout = QtWidgets.QVBoxLayout()
        note = editors.NoteEditor( parent=self )
        note.set_value(None)
        note.setObjectName('note')
        note_layout.addWidget(form_widget)
        note_layout.addWidget(note)
        layout.addLayout(note_layout)
        model.headerDataChanged.connect(self.header_data_changed)
        form_widget.setObjectName( 'form' )
        self.main_widget().setLayout(layout)
        cancel_button = QtWidgets.QPushButton(str(reject))
        cancel_button.setObjectName( 'cancel' )
        ok_button = QtWidgets.QPushButton(str(accept))
        ok_button.setObjectName( 'ok' )
        layout = QtWidgets.QHBoxLayout()
        layout.setDirection( QtWidgets.QBoxLayout.Direction.RightToLeft )
        layout.addWidget( ok_button )
        layout.addWidget( cancel_button )
        layout.addStretch()
        self.buttons_widget().setLayout( layout )
        self._change_complete(model, False)
        cancel_button.pressed.connect( self.reject )
        ok_button.pressed.connect( self.accept )
        # set the actions in the actions panel
        self.set_actions(form_actions)
        for action_route, action_state in action_states:
            self.set_action_state(self, tuple(action_route), action_state)
        # set the value last, so the validity can be updated
        model.setValue(proxy_route)
        self.model_context_name = proxy_route
        columns = [fn for fn, _fa in fields.items()]
        model.setColumns(columns)
        self.gui_context_name = gui_naming_context.bind(
            ('transient', str(id(self))), self
        )

    @property
    def widget_mapper(self):
        return self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')

    def get_window(self):
        return self.window()

    @QtCore.qt_slot(bool)
    def button_clicked(self, checked):
        self.run_action(self.sender(), self.gui_context_name, self.model_context_name, None)

    @QtCore.qt_slot()
    def menu_triggered(self):
        qaction = self.sender()
        self.run_action(qaction, self.gui_context_name, self.model_context_name, qaction.data())

    @QtCore.qt_slot(list)
    def set_actions(self, actions):
        layout = self.findChild(QtWidgets.QLayout, 'form_and_actions_layout' )
        if actions and layout:
            side_panel_layout = QtWidgets.QVBoxLayout()
            for action in actions:
                action_widget = self.render_action(
                    RenderHint(action['render_hint']), tuple(action['route']),
                    self, self
                )
                side_panel_layout.addWidget(action_widget)
            side_panel_layout.addStretch()
            layout.addLayout(side_panel_layout)

    @QtCore.qt_slot(Qt.Orientation, int, int)
    def header_data_changed(self, orientation, first, last):
        if orientation == Qt.Orientation.Vertical:
            model = self.sender()
            valid = model.headerData(0, orientation, ValidRole)
            self._change_complete(model, valid or False)

    def _change_complete(self, model, complete):
        note = self.findChild( QtWidgets.QWidget, 'note' )
        ok_button = self.findChild( QtWidgets.QPushButton, 'ok' )
        cancel_button = self.findChild( QtWidgets.QPushButton, 'cancel' )
        if ok_button is not None and note is not None:
            ok_button.setEnabled( complete )
            ok_button.setDefault( complete )
            if complete:
                note.set_value(None)
            else:
                note.set_value(model.headerData(0, Qt.Orientation.Vertical, ValidMessageRole))
        if cancel_button is not None:
            ok_button.setDefault( not complete )

class ChangeObjectsDialog( StandaloneWizardPage ):
    """A dialog to change a list of objects.  This differs from a ListView in
    that it does not contains Actions, and has an OK button that is enabled when
    all objects are valid.

    :param objects: The object to change
    :param admin: The admin class used to create a form

    .. image:: /_static/actionsteps/change_object.png
    """

    def __init__( self,
                  objects,
                  admin_route,
                  columns,
                  action_routes,
                  invalid_rows,
                  action_states,
                  list_action,
                  parent = None,
                  flags = QtCore.Qt.WindowType.Window ):
        super(ChangeObjectsDialog, self).__init__( '', parent, flags )
        self.banner_widget().setStyleSheet('background-color: white;')
        table_widget = editors.One2ManyEditor(
            admin_route = admin_route,
            parent = self,
            columns=[column['name'] for column in columns],
            # assume all actions are list actions and no field action,
            list_actions=action_routes,
            list_action=list_action,
        )
        self.invalid_rows = invalid_rows
        model = table_widget.get_model()
        model.headerDataChanged.connect(self.header_data_changed)
        table_widget.set_value(objects)
        table_widget.setObjectName( 'table_widget' )
        note = editors.NoteEditor( parent=self )
        note.set_value(None)
        note.setObjectName( 'note' )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( table_widget )
        layout.addWidget( note )
        self.main_widget().setLayout( layout )
        self.set_default_buttons()
        self.update_complete(model)
        for route, state in action_states:
            table_widget.action_state_changed(
                route,
                QtCore.QByteArray(json.dumps(state).encode('utf-8'))
            )

    @QtCore.qt_slot(Qt.Orientation, int, int)
    def header_data_changed(self, orientation, first, last):
        if orientation == Qt.Orientation.Vertical:
            model = self.sender()
            for row in range(first, last+1):
                valid = model.headerData(row, orientation, ValidRole)
                if (valid==True) and (row in self.invalid_rows):
                    self.invalid_rows.remove(row)
                    self.update_complete(model)
                elif (valid==False) and (row not in self.invalid_rows):
                    self.invalid_rows.add(row)
                    self.update_complete(model)
                elif (valid==False) and (row==min(self.invalid_rows)):
                    self.update_complete(model)

    def update_complete(self, model):
        complete = (len(self.invalid_rows)==0)
        note = self.findChild( QtWidgets.QWidget, 'note' )
        ok = self.findChild( QtWidgets.QWidget, 'accept' )
        if note != None and ok != None:
            ok.setEnabled(complete)
            if complete:
                note.set_value( None )
            else:
                row = min(self.invalid_rows)
                note.set_value(u'{0}<br/>{1}'.format(
                    ugettext(u'Please correct row {0} before proceeding.').format(row+1),
                    model.headerData(row, Qt.Orientation.Vertical, ValidMessageRole)
                ))

@dataclass
class ChangeObject(OpenFormView):
    """
    Pop up a form for the user to change an object

    :param obj: the object to change
    :param admin: an instance of an admin class to use to edit the object

    .. attribute:: accept

        The text shown in the accept button

    .. attribute:: reject

        The text shown in the reject button

    """

    subtitle: typing.Union[str, ugettext_lazy, None] = _('Complete the form and press the OK button')
    accept: typing.Union[str, ugettext_lazy] = _('OK')
    reject: typing.Union[str, ugettext_lazy] = _('Cancel')
    blocking: bool = True

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_form_actions(None))

    def get_object( self ):
        """Use this method to get access to the object to change in unit tests

        :return: the object to change
        """
        return self.get_objects()[0]

    @classmethod
    def render(self, gui_context, step):
        """create the dialog. this method is used to unit test
        the action step."""
        dialog = ChangeObjectDialog(
            step['model_context_name'],
            tuple(step['admin_route']),
            step['title'],
            step['form'],
            dict(step['fields']),
            step['actions'],
            step['action_states'],
            step['accept'],
            step['reject'],
        )
        dialog.set_banner_title(step['title'])
        dialog.set_banner_subtitle(step['subtitle'])
        return dialog

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        dialog = cls.render(gui_context, step)
        apply_form_state(dialog, None, step['form_state'])
        with hide_progress_dialog( gui_context ):
            result = dialog.exec()
            if result == QtWidgets.QDialog.DialogCode.Rejected:
                raise CancelRequest()


@dataclass
class ChangeObjects(UpdateTableView):
    """
    Pop up a list for the user to change objects

    :param objects: a list of objects to change
    :param admin: an instance of an admin class to use to edit the objects.
    :param validate: validate all objects before allowing the user to change
        them.  If objects are not validated before showing them, only the
        visible objects will be validated.  But validation of all  objects might
        take a lot of time.

    .. image:: /_static/listactions/import_from_file_preview.png

    This action step can be customised using these attributes :

    .. attribute:: window_title

        the window title of the dialog shown

    .. attribute:: title

        the title of the dialog shown

    .. attribute:: subtitle

        the subtitle of the dialog shown

    .. attribute:: icon

        the :class:`camelot.admin.icon.Icon` in the top right corner of
        the dialog

    """

    validate: bool = True

    invalid_rows: List = field(init=False, default_factory=list)
    admin_route: AdminRoute = field(init=False)
    window_title: str = field(init=False)
    title: Union[str, ugettext_lazy] = field(init=False, default= _('Data Preview'))
    subtitle: Union[str, ugettext_lazy] = field(init=False, default=_('Please review the data below.'))
    icon: typing.Union[Icon, None] = field(init=False, default=Icon('file-excel'))

    def __post_init__( self, value, admin, proxy, search_text):
        super().__post_init__(value, admin, proxy, search_text)
        self.admin_route = admin.get_admin_route()
        self.window_title = admin.get_verbose_name_plural()
        if self.validate:
            validator = admin.get_validator()
            for row, obj in enumerate(value):
                for _message in validator.validate_object(obj):
                    self.invalid_rows.append(row)
                    break

    @staticmethod
    def _add_actions(admin, actions):
        actions.extend(admin.get_related_toolbar_actions('onetomany'))

    def get_admin(self):
        """Use this method to get access to the admin in unit tests"""
        return initial_naming_context.resolve(self.admin_route)

    @classmethod
    def render(cls, step):
        """create the dialog. this method is used to unit test
        the action step."""
        dialog = ChangeObjectsDialog(
            tuple(step['model_context_name']),
            tuple(step['admin_route']), step['columns'],
            [RouteWithRenderHint(tuple(rwrh['route']), RenderHint(rwrh['render_hint'])) for rwrh in step['actions']],
            set(step['invalid_rows']), step['action_states'],
            step['list_action']
        )
        dialog.setWindowTitle(step['window_title'])
        dialog.set_banner_title(step['title'])
        dialog.set_banner_subtitle(step['subtitle'])
        if step['icon'] is not None:
            icon = Icon(
                step['icon']['name'],
                step['icon']['pixmap_size'],
                step['icon']['color']
            )
            dialog.set_banner_logo_pixmap(from_admin_icon(icon).getQPixmap())
        #
        # the dialog cannot estimate its size, so use 75% of screen estate
        #
        screen = dialog.screen()
        available_geometry = screen.availableGeometry()
        dialog.resize( available_geometry.width() * 0.75,
                       available_geometry.height() * 0.75 )
        return dialog

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        step = json.loads(serialized_step)
        dialog = cls.render(step)
        with hide_progress_dialog( gui_context ):
            result = dialog.exec()
            if result == QtWidgets.QDialog.DialogCode.Rejected:
                raise CancelRequest()
