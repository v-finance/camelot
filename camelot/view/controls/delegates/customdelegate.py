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


import json
import logging
import dataclasses

from camelot.core.naming import initial_naming_context

from ....admin.icon import CompletionValue
from ....core.qt import QtGui, QtCore, QtWidgets, Qt
from ....core.serializable import json_encoder, NamedDataclassSerializable
from ....core.item_model import (
    ActionRoutesRole, ActionStatesRole,
    ChoicesRole, VisibleRole, NullableRole
)
from ..action_widget import AbstractActionWidget
from camelot.view.controls import editors
from camelot.view.crud_action import DataCell
from dataclasses import dataclass, InitVar
from typing import Any, ClassVar



LOGGER = logging.getLogger(__name__)

def DocumentationMetaclass(name, bases, dct):
    dct['__doc__'] = (dct.get('__doc__') or '') + """

.. _delegate-%s:

.. image:: /_static/delegates/%s_unselected_disabled.png
.. image:: /_static/delegates/%s_unselected_editable.png

.. image:: /_static/delegates/%s_selected_disabled.png
.. image:: /_static/delegates/%s_selected_editable.png

"""%(name, name, name, name, name,)
    import inspect

    def add_field_attribute_item(a):
        """Add the name of a field attribute and a reference to its documentation
        to the docstring"""
        dct['__doc__'] = dct['__doc__'] + "\n * :ref:`%s <field-attribute-%s>`"%(arg, arg)

    if '__init__' in dct:
        dct['__doc__'] = dct['__doc__'] + 'Field attributes supported by the delegate : \n'
        args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['__init__'])
        for arg in args:
            if arg not in ['self', 'parent']:
                add_field_attribute_item(arg)

    if 'editor' in dct:
        
        row_separator = '+' + '-'*40 + '+' + '-'*90 + '+'
        row_format = """| %-38s | %-88s |"""
        states = {'editable':['editable=True'], 
                  'disabled':['editable=False'],
                  'editable_tooltip':['editable=True', "tooltip='tooltip'"], 
                  'disabled_tooltip':['editable=False', "tooltip='tooltip'"],
                  'editable_background_color':['editable=True', 'background_color=ColorScheme.green'], 
                  'disabled_background_color':['editable=False', 'background_color=ColorScheme.green']                  
                  }

        dct['__doc__'] = dct['__doc__'] + '\n\nBy default, creates a %s as its editor.\n\n'%dct['editor'].__name__
        dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        dct['__doc__'] = dct['__doc__'] + row_format%('**Field Attributes**', '**Editor**') + '\n'
        dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        for state, attrs in states.items():
            for i,attr in enumerate(attrs):
                if i==0:
                    image = '.. image:: /_static/editors/%s_%s.png'%(dct['editor'].__name__, state)
                else:
                    image = ''
                dct['__doc__'] = dct['__doc__'] + row_format%(attr, image) + '\n'
            dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        
        dct['__doc__'] = dct['__doc__'] + '\nStatic attributes supported by this editor : \n'
        args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['editor'].__init__)
        for arg in args:
            if arg not in ['self', 'parent']:
                add_field_attribute_item(arg)

        if hasattr(dct['editor'], 'set_field_attributes'):
            dct['__doc__'] = dct['__doc__'] + '\n\nDynamic field attributes supported by the editor : \n'
            args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['editor'].set_field_attributes)
            for arg in args:
                if arg not in ['self', 'parent']:
                    add_field_attribute_item(arg)

        dct['__doc__'] = dct['__doc__'] + '\n\n'

    return type(name, bases, dct)

color_groups = {True: QtGui.QPalette.ColorGroup.Inactive,
                False: QtGui.QPalette.ColorGroup.Disabled}

class CustomDelegateMeta(type(NamedDataclassSerializable), type(QtWidgets.QItemDelegate)):
    pass

@dataclass
class CustomDelegate(NamedDataclassSerializable, QtWidgets.QItemDelegate, metaclass=CustomDelegateMeta):
    """Base class for implementing custom delegates.

    .. attribute:: editor

    class attribute specifies the editor class that should be used

    """

    _parent: InitVar[QtCore.QObject] = None

    horizontal_align: ClassVar[Any] = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

    def __post_init__(self, parent):
        """:param parent: the parent object for the delegate
        :param editable: a boolean indicating if the field associated to the delegate
        is editable
        """
        super().__init__(parent)
        self._font_metrics = QtGui.QFontMetrics(QtWidgets.QApplication.font())
        self._height = self._font_metrics.lineSpacing() + 10
        self._width = self._font_metrics.averageCharWidth() * 20

    @classmethod
    def get_editor_class(cls):
        """Get the editor class for this delegate."""
        raise NotImplementedError

    @classmethod
    def set_item_editability(cls, model_context, item, default):
        editable = model_context.field_attributes.get('editable', default)
        if editable:
            item.flags = item.flags | Qt.ItemFlag.ItemIsEditable
        else:
            item.flags = item.flags & ~Qt.ItemFlag.ItemIsEditable

    @classmethod
    def get_standard_item(cls, locale, model_context):
        """
        This method is used by the proxy to convert the value of a field
        to the data for the standard item model.  The result of this call can be
        used by the methods of the delegate.

        :param locale: the `QLocale` to be used to display locale dependent values
        :param model_context: a FieldActionModelContext object
        :return: a `QStandardItem` object
        """
        routes = model_context.field_attributes.get('action_routes', [])
        states = []
        for action in model_context.field_attributes.get('actions', []):
            state = action.get_state(model_context)
            states.append(dataclasses.asdict(state))
        #assert len(routes) == len(states), 'len(routes) != len(states)\nroutes: {}\nstates: {}'.format(routes, states)
        if len(routes) != len(states):
            LOGGER.error('CustomDelegate: len(routes) != len(states)\nroutes: {}\nstates: {}'.format(routes, states))

        # eventually, the whole item will need to be serialized, while this
        # is not yet the case, serialize some roles to make the usable outside
        # python.
        serialized_action_routes = json_encoder.encode(routes)
        serialized_action_states = json_encoder.encode(states)
        item = DataCell()
        # @todo : the line below should be removed, but only after testing
        #         if each delegate properly handles setting edit role
        item.roles[Qt.ItemDataRole.EditRole] = model_context.value
        # NOTE: one of the goals is to serialize the field attributes, which currently
        # still comprises a large variety of elements, some of which should still be made serializable,
        # while others may only be used at the model side and should not be included in the serialization.
        # That exact set of elements that should be included is still a TODO, as many editors still rely
        # on the field attributes being passes as kwargs as part of their initialization.
        # As a transition phase, custom ItemData roles are introduced to store those elements
        # that are already made serializable, as to gradually get towards the final goal.
        # Eventually, when the final set of serializable field attributes is known, those roles
        # may be combined again somehow, but this is still TBD.
        item.roles[ActionRoutesRole] = serialized_action_routes
        item.roles[ActionStatesRole] = serialized_action_states
        item.roles[Qt.ItemDataRole.TextAlignmentRole] = cls.horizontal_align
        item.roles[Qt.ItemDataRole.ToolTipRole] = model_context.field_attributes.get('tooltip')
        background_color = model_context.field_attributes.get('background_color')
        if background_color is not None:
            if not isinstance(background_color, QtGui.QColor):
                background_color = QtGui.QColor(background_color)
            item.roles[Qt.ItemDataRole.BackgroundRole] = initial_naming_context._bind_object(background_color)
        item.roles[VisibleRole] = model_context.field_attributes.get('visible', True)
        item.roles[NullableRole] = model_context.field_attributes.get('nullable', True)
        # FIXME: move choices to delegates that actually use it?
        choices = model_context.field_attributes.get('choices')
        if choices is not None:
            choices = [CompletionValue(
                value=initial_naming_context._bind_object(obj),
                verbose_name=verbose_name
                )._to_dict() for obj, verbose_name in choices]
        item.roles[ChoicesRole] = choices
        return item

    def createEditor(self, parent, option, index):
        """
        :param option: use an option with version 5 to indicate the widget
        will be put onto a form
        """
        editor_cls = self.get_editor_class()
        if issubclass(editor_cls, (editors.BoolEditor, editors.ColorEditor, editors.LanguageEditor,
                                   editors.NoteEditor, editors.RichTextEditor)):
            editor = editor_cls(parent)
        elif issubclass(editor_cls, (editors.ChoicesEditor, editors.Many2OneEditor,
                                     editors.FileEditor)):
            editor = editor_cls(parent, self.action_routes)
        elif issubclass(editor_cls, editors.DateEditor):
            editor = editor_cls(parent, self.nullable)
        elif issubclass(editor_cls, editors.DbImageEditor):
            editor = editor_cls(parent, self.preview_width, self.preview_height, self.max_size)
        elif issubclass(editor_cls, editors.FloatEditor):
            editor = editor_cls(parent, self.calculator, self.decimal, self.action_routes, option)
        elif issubclass(editor_cls, editors.IntegerEditor):
            editor = editor_cls(parent, self.calculator, option)
        elif issubclass(editor_cls, editors.LabelEditor):
            editor = editor_cls(parent, self.text, self.field_name)
        elif issubclass(editor_cls, editors.LocalFileEditor):
            editor = editor_cls(parent, self.directory, self.save_as, self.file_filter)
        elif issubclass(editor_cls, editors.MonthsEditor):
            editor = editor_cls(parent, self.minimum, self.maximum)
        elif issubclass(editor_cls, editors.TextLineEditor):
            editor = editor_cls(parent, self.length, self.echo_mode, self.column_width, self.action_routes, self.validator_type, self.completer_type)
        elif issubclass(editor_cls, editors.TextEditEditor):
            editor = editor_cls(parent, self.length, self.editable)
        elif issubclass(editor_cls, editors.VirtualAddressEditor):
            editor = editor_cls(parent, self.address_type)
        else:
            raise NotImplementedError()
        assert editor != None
        assert isinstance(editor, QtWidgets.QWidget)
        if option.version != 5:
            editor.setAutoFillBackground(True)
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def sizeHint(self, option, index):
        return QtCore.QSize(self._width, self._height)

    #@QtCore.qt_slot()
    # not yet converted to new style sig slot because sender doesn't work
    # in certain versions of pyqt
    def commitAndCloseEditor(self):
        editor = self.sender()
        assert editor != None
        assert isinstance(editor, QtWidgets.QWidget)
        self.commitData.emit(editor)
        # * Closing the editor results in the calculator not working
        # * not closing the editor results in the virtualaddresseditor not
        #   getting closed always
        #self.closeEditor.emit( editor, QtWidgets.QAbstractItemDelegate.EndEditHint.NoHint )

    def set_default_editor_data(self, editor, index):
        editable = bool(index.flags() & Qt.ItemFlag.ItemIsEditable)
        nullable = bool(index.data(NullableRole))
        visible = bool(index.data(VisibleRole))
        tooltip = index.data(Qt.ItemDataRole.ToolTipRole)
        background_color = index.data(Qt.ItemDataRole.BackgroundRole)
        editor.set_editable(editable)
        editor.set_nullable(nullable)
        editor.set_visible(visible)
        editor.set_tooltip(tooltip)
        editor.set_background_color(background_color)

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        self.set_default_editor_data(editor, index)
        #
        # first set the field attributes, as these may change the 'state' of the
        # editor to properly display and hold the value, eg 'precision' of a 
        # float might be changed
        #
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.set_value(value)
        # update actions
        self.update_field_action_states(editor, index)

    def update_field_action_states(self, editor, index):
        action_states = json.loads(index.model().data(index, ActionStatesRole))
        action_routes = json.loads(index.model().data(index, ActionRoutesRole))
        if len(action_routes) == 0:
            return
        for action_route, action_state in zip(action_routes, action_states):
            for action_widget in editor.findChildren(QtWidgets.QToolButton):
                action_route_of_widget = action_widget.property('action_route')
                if action_route_of_widget is None:
                    continue
                if list(action_route_of_widget)==action_route:
                    AbstractActionWidget.set_toolbutton_state(
                        action_widget, action_state, editor.action_menu_triggered
                    )
                    break
            else:
                LOGGER.error('action route not found {} in editor'.format(
                    action_route
                ))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.get_value())
