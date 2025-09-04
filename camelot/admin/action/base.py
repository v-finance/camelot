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
from __future__ import annotations

import logging
import typing

from camelot.admin.icon import Icon
from camelot.core.qt import QtWidgets, QtGui
from camelot.core.serializable import DataclassSerializable
from camelot.core.utils import ugettext_lazy

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


LOGGER = logging.getLogger( 'camelot.admin.action' )

class ModelContext( object ):
    """
The Model context in which an action is running.  The model context can contain
reference to database sessions or other model related data. 
    """

    def __init__( self ):
        pass


@dataclass
class Mode(DataclassSerializable):
    """A mode is a way in which an action can be triggered, a print action could
be triggered as 'Export to PDF' or 'Export to Word'.  None always represents
the default mode.
    
.. attribute:: value

    a value representing the mode to the developer
    
.. attribute:: verbose_name

    The name shown to the user
    
.. attribute:: icon

    The icon of the mode
    
.. attribute:: modes: 

    Optionally, a list of sub modes.
    
.. attribute:: enabled:

    Flag indicating whether mode should be enabled or not.
    """

    value: Any
    verbose_name: typing.Union[str, ugettext_lazy]
    icon: typing.Union[Icon, None] = None
    modes: typing.List[Mode] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        for mode in self.modes:
            assert isinstance(mode, type(self))

    def render( self, parent ):
        """
        In case this mode is a leaf (no containing sub modes), a :class:`QtWidgets.QAction`
        will be created (or `QtWidgets.QMenu` in case this modes has sub modes defined)
        that can be used to enable the widget to trigger the action in a specific mode.
        The data attribute of the action will contain the value of the mode.
        In case has underlying sub modes, a `QtWidgets.QMenu` will be created to which
        the rendered sub modes can be attached.
        :return: a :class:`QtWidgets.QAction` or :class:`QtWidgets.QMenu` to use this mode
        """
        if self.modes:
            menu = QtWidgets.QMenu(str(self.verbose_name), parent=parent)
            parent.addMenu(menu)
            return menu
        else:
            action = QtGui.QAction( parent )
            action.setData( self.value )
            action.setText( str(self.verbose_name) )
            action.setEnabled(self.enabled)
            action.setIconVisibleInMenu(False)
            return action

@dataclass
class State(DataclassSerializable):
    """A state represents the appearance and behavior of the widget that
triggers the action.  When the objects in the model change, the 
:meth:`Action.get_state` method will be called, which should return the
updated state for the widget.

.. attribute:: verbose_name

    The name of the action as it will appear in the button, this defaults to
    the verbose_name of the action.
    
.. attribute:: icon

    The icon that represents the action, of type 
    :class:`camelot.admin.icon.Icon`, this defaults to the icon of the action.

.. attribute:: tooltip

    The tooltip as displayed to the user, this should be of type 
    :class:`camelot.core.utils.ugettext_lazy`, this defaults to the tooltip
    op the action.

.. attribute:: enabled

    :const:`True` if the widget should be enabled (the default), 
    :const:`False` otherwise
    
.. attribute:: visible

    :const:`True` if the widget should be visible (the default), 
    :const:`False` otherwise

.. attribute:: notification

    :const:`True` if the buttons should attract the attention of the user, 
    defaults to :const:`False`.

.. attribute:: modes

    The modes in which an action can be triggered, a list of :class:`Mode`
    objects.

.. attribute:: shortcut

    The shortcut key sequence to trigger the action.

.. attribute:: color

    A color used to indicate something regarding the action's state. This color
    can be used as button text color, background or outline for example.
    """

    verbose_name: typing.Union[str, ugettext_lazy, None] = None
    icon: typing.Union[Icon, None] = None
    tooltip: typing.Union[str, ugettext_lazy, None] = None
    enabled: bool = True
    visible: bool = True
    notification: bool = False
    modes: typing.List[Mode] = field(default_factory=list)
    shortcut: typing.Optional[str] = None
    color: typing.Optional[str] = None

# TODO: When all action step have been refactored to be serializable, ActionStep can be implemented as NamedDataclassSerializable,
#       which NamedDataclassSerializableMeta metaclass replaces the need for MetaActionStep.
class MetaActionStep(type):

    action_steps = dict()

    def __new__(cls, clsname, bases, attrs):
        newclass = super().__new__(cls, clsname, bases, attrs)
        cls.action_steps[clsname] = newclass
        return newclass

class ActionStep(metaclass=MetaActionStep):
    """A reusable part of an action.  Action step object can be yielded inside
the :meth:`model_run`.  When this happens, their :meth:`gui_run` method will
be called inside the *GUI thread*.  The :meth:`gui_run` can pop up a dialog
box or perform other GUI related tasks.

When the ActionStep is blocking, it will return control after the 
:meth:`gui_run` is finished, and the return value of :meth:`gui_run` will
be the result of the :keyword:`yield` statement.

When the ActionStep is not blocking, the :keyword:`yield` statement will
return immediately and the :meth:`model_run` will not be blocked.

.. attribute:: blocking

    a :keyword:`boolean` indicating if the ActionStep is blocking, defaults
    to :const:`True`
    
.. attribute:: cancelable

    a :keyword:`boolean` indicating if the ActionStep is allowed to raise
    a `CancelRequest` exception when yielded, defaults to :const:`True`

    """

    blocking = True
    cancelable = True

    def model_run( self, model_context, mode ):
        raise Exception('This should not happen')

    @classmethod
    def deserialize_result(cls, model_context: ModelContext, serialized_result):
        """
        :param model_context:  An object of type
            :class:`camelot.admin.action.ModelContext`, which is the context
            on which the action was started.

        :param serialized_result: The serialized result coming from the client.

        :return: The deserialized result. The default implementation returns the
            serialized result as is. This function can be reimplemented to change
            this behavior.
        """
        return serialized_result


class RenderHint(Enum):
    """
    How an action wants to be rendered in the ui
    """

    PUSH_BUTTON = 'push_button'
    TOOL_BUTTON = 'tool_button'
    CLOSE_BUTTON = 'close_button'
    SEARCH_BUTTON = 'search_button'
    EXCLUSIVE_GROUP_BOX = 'exclusive_group_box'
    NON_EXCLUSIVE_GROUP_BOX = 'non_exclusive_group_box'
    COMBO_BOX = 'combo_box'
    LABEL = 'label'
    STRETCH = 'stretch'
    STATUS_BUTTON = 'status_button'
    DROP = 'drop'
    NOTE = 'note'

