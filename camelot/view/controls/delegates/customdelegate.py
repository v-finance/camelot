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

from ....core.qt import (QtGui, QtCore, QtWidgets, Qt,
                         py_to_variant, variant_to_py)
from ....core.serializable import json_encoder
from ....core.item_model import (
    ProxyDict, FieldAttributesRole, ActionRoutesRole, ActionStatesRole
)
from ....admin.action.field_action import FieldAction
from ..action_widget import ActionToolbutton

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

class CustomDelegate(QtWidgets.QItemDelegate):
    """Base class for implementing custom delegates.

    .. attribute:: editor

    class attribute specifies the editor class that should be used

    """

    editor = None
    horizontal_align = Qt.Alignment.AlignLeft | Qt.Alignment.AlignVCenter

    def __init__(self, parent=None, editable=True, **kwargs):
        """:param parent: the parent object for the delegate
        :param editable: a boolean indicating if the field associated to the delegate
        is editable

        """
        super( CustomDelegate, self ).__init__(parent)
        self.editable = editable
        self.kwargs = kwargs
        self._font_metrics = QtGui.QFontMetrics(QtWidgets.QApplication.font())
        self._height = self._font_metrics.lineSpacing() + 10
        self._width = self._font_metrics.averageCharWidth() * 20

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
            if isinstance(action, FieldAction):
                state = action.get_state(model_context)
                states.append(dataclasses.asdict(state))
            else:
                states.append(None)
        #assert len(routes) == len(states), 'len(routes) != len(states)\nroutes: {}\nstates: {}'.format(routes, states)
        if len(routes) != len(states):
            LOGGER.error('CustomDelegate: len(routes) != len(states)\nroutes: {}\nstates: {}'.format(routes, states))

        # eventually, the whole item will need to be serialized, while this
        # is not yet the case, serialize some roles to make the usable outside
        # python.
        serialized_action_routes = json_encoder.encode(routes)
        serialized_action_states = json_encoder.encode(states)
        item = QtGui.QStandardItem()
        item.setData(py_to_variant(model_context.value), Qt.ItemDataRole.EditRole)
        item.setData(serialized_action_routes, ActionRoutesRole)
        item.setData(serialized_action_states, ActionStatesRole)
        item.setData(py_to_variant(cls.horizontal_align), Qt.ItemDataRole.TextAlignmentRole)
        item.setData(py_to_variant(ProxyDict(model_context.field_attributes)),
                     FieldAttributesRole)
        item.setData(py_to_variant(model_context.field_attributes.get('tooltip')),
                     Qt.ItemDataRole.ToolTipRole)
        item.setData(py_to_variant(model_context.field_attributes.get('background_color')),
                     Qt.ItemDataRole.BackgroundRole)
        return item

    def createEditor(self, parent, option, index):
        """
        :param option: use an option with version 5 to indicate the widget
        will be put onto a form
        """

        editor = self.editor(parent, editable = self.editable, option = option, **self.kwargs)
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

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        value = variant_to_py(index.model().data(index, Qt.ItemDataRole.EditRole))
        field_attributes = variant_to_py(index.data(FieldAttributesRole)) or dict()
        # ok i think i'm onto something, dynamically set tooltip doesn't change
        # Qt model's data for Qt.ItemDataRole.ToolTipRole
        # but i wonder if we should make the detour by Qt.ItemDataRole.ToolTipRole or just
        # get our tooltip from field_attributes
        # (Nick G.): Avoid 'None' being set as tooltip.
        if field_attributes.get('tooltip'):
            editor.setToolTip( str( field_attributes.get('tooltip', '') ) )
        #
        # first set the field attributes, as these may change the 'state' of the
        # editor to properly display and hold the value, eg 'precision' of a 
        # float might be changed
        #
        editor.set_field_attributes(**field_attributes)
        editor.set_value(value)

        # update actions
        self.update_field_action_states(editor, index)

    def update_field_action_states(self, editor, index):
        action_states = json.loads(index.model().data(index, ActionStatesRole))
        action_routes = json.loads(index.model().data(index, ActionRoutesRole))
        if len(action_routes) == 0:
            return
        for action_widget in editor.findChildren(ActionToolbutton):
            try:
                action_index = action_routes.index(list(action_widget.action_route))
            except ValueError:
                LOGGER.error('action route not found {}, available routes'.format(
                    action_widget.action_route
                ))
                for route in action_routes:
                    LOGGER.error(route)
                continue
            state = action_states[action_index]
            if state is not None:
                action_widget.set_state_v2(state)

    def setModelData(self, editor, model, index):
        model.setData(index, py_to_variant(editor.get_value()))
