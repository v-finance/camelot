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

from enum import Enum
import logging

from ...core.qt import QtWidgets, QtGui, Qt

import six

LOGGER = logging.getLogger( 'camelot.admin.action' )

class ModelContext( object ):
    """
The Model context in which an action is running.  The model context can contain
reference to database sessions or other model related data. This object can not 
contain references to widgets as those belong strictly to the :class:`GuiContext`.

.. attribute:: mode_name

    the name of the mode in which the action was triggered
    """
          
    def __init__( self ):
        self.mode_name = None
        
class GuiContext( object ):
    """
The GUI context in which an action is running.  This object can contain
references to widgets and other useful information.  This object cannot
contain reference to anything database or model related, as those belong
strictly to the :class:`ModelContext`

.. attribute:: mode_name

    the name of the mode in which the action was triggered
    
.. attribute:: model_context

    a subclass of :class:`ModelContext` to be used in :meth:`create_model_context`
    as the type of object to return.
    """
    
    model_context = ModelContext
    
    def __init__( self ):
        self.mode_name = None

    def get_progress_dialog(self):
        """
        :return: an instance of :class:`QtWidgets.QProgressDialog`
                 or :keyword:`None`
        """
        from camelot.view.controls.progress_dialog import ProgressDialog
        window = self.get_window()
        if window is not None:
            progress_dialog = window.findChild(
                QtWidgets.QProgressDialog, 'application_progress',
                Qt.FindDirectChildrenOnly
            )
            if progress_dialog is None:
                progress_dialog = ProgressDialog(parent=window)
                progress_dialog.setObjectName('application_progress')
            return progress_dialog

    def get_window(self):
        """
        The window to be used as a reference to position new windows.  Returns
        `None` if there is no window yet.
        
        :return: a :class:`QtWidgets.QWidget`
        """
        return None

    def create_model_context( self ):
        """Create a :class:`ModelContext` filled with base information, 
        extracted from this GuiContext.  This function will be called in the
        GUI thread, so it should not access the model directly, but rather
        extract all information needed from te GUI to be available in the
        model.
        
        :return: a :class:`ModelContext`
        """
        context = self.model_context()
        context.mode_name = self.mode_name
        return context
        
    def copy( self, base_class = None ):
        """Create a copy of the GuiContext, this function is used
        to create new GuiContext's that are more specialized without
        modifying the original one.

        :param base_class: the type of the new context to be created, None
            if the new context should be of the same type as the copied context.
        """
        new_context = (base_class or self.__class__)()
        new_context.mode_name = self.mode_name
        return new_context

class State( object ):
    """A state represents the appearance and behavior of the widget that
triggers the action.  When the objects in the model change, the 
:meth:`Action.get_state` method will be called, which should return the
updated state for the widget.

.. attribute:: verbose_name

    The name of the action as it will appear in the button, this defaults to
    the verbose_name of the action.
    
.. attribute:: icon

    The icon that represents the action, of type 
    :class:`camelot.view.art.Icon`, this defaults to the icon of the action.

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
    """
    
    def __init__( self ):
        self.verbose_name = None
        self.icon = None
        self.tooltip = None
        self.enabled = True
        self.visible = True
        self.notification = False
        self.modes = []

class Mode( object ):
    """A mode is a way in which an action can be triggered, a print action could
be triggered as 'Export to PDF' or 'Export to Word'.  None always represents
the default mode.
    
.. attribute:: name

    a string representing the mode to the developer and the authentication
    system.  this name will be used in the :class:`GuiContext`
    
.. attribute:: verbose_name

    The name shown to the user
    
.. attribute:: icon

    The icon of the mode
    """
    
    def __init__( self, name, verbose_name=None, icon=None):
        """
        :param name: the name of the mode, as it will be passed to the
            gui_run and model_run method
        :param verbose_name: the name shown to the user
        :param icon: the icon of the mode
        """
        self.name = name
        if verbose_name is None:
            verbose_name = name.capitalize()
        self.verbose_name = verbose_name
        self.icon = icon
        
    def render( self, parent ):
        """Create a :class:`QtWidgets.QAction` that can be used to enable widget
        to trigger the action in a specific mode.  The data attribute of the
        action will contain the name of the mode.
        
        :return: a :class:`QtWidgets.QAction` class to use this mode
        """
        action = QtWidgets.QAction( parent )
        action.setData( self.name )
        action.setText( six.text_type(self.verbose_name) )
        action.setIconVisibleInMenu( False )
        return action
        
class ActionStep( object ):
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
            
    def gui_run( self, gui_context ):
        """This method is called in the *GUI thread* upon execution of the
        action step.  The return value of this method is the result of the
        :keyword:`yield` statement in the *model thread*.
        
        The default behavior of this method is to call the model_run generator
        in the *model thread* until it is finished.
        
        :param gui_context:  An object of type 
            :class:`camelot.admin.action.GuiContext`, which is the context 
            of this action available in the *GUI thread*.  What is in the 
            context depends on how the action was called.
            
        this method will raise a :class:`camelot.core.exception.CancelRequest`
        exception, if the user canceled the operation.
        """
        from camelot.view.action_runner import ActionRunner
        runner = ActionRunner( self.model_run, gui_context )
        runner.exec_()
        
    def model_run( self, model_context = None ):
        """A generator that yields :class:`camelot.admin.action.ActionStep`
        objects.  This generator can be called in the *model thread*.
        
        :param context:  An object of type
            :class:`camelot.admin.action.ModelContext`, which is context 
            of this action available in the model_thread.  What is in the 
            context depends on how the action was called.
        """
        yield

class ProgressLevel(object):

    def __init__(self, gui_context, verbose_name):
        self.verbose_name = verbose_name
        self.gui_context = gui_context
        self.progress_dialog = None

    def __enter__(self):
        self.progress_dialog = self.gui_context.get_progress_dialog()
        if self.progress_dialog is not None:
            self.progress_dialog.push_level(self.verbose_name)
        return self

    def __exit__(self, type, value, traceback):
        if self.progress_dialog is not None:
            self.progress_dialog.pop_level()
        self.progress_dialog = None
        return False


class RenderHint(Enum):
    """
    How an action wants to be rendered in the ui
    """

    PUSH_BUTTON = 'push_button'
    TOOL_BUTTON = 'tool_button'
    SEARCH_BUTTON = 'search_button'
    GROUP_BOX = 'group_box'
    COMBO_BOX = 'combo_box'
    LABEL = 'label'


class Action( ActionStep ):
    """An action has a set of attributes that define its appearance in the
GUI.  
    
.. attribute:: name

    The internal name of the action, this can be used to store preferences
    concerning the action in the settings

.. attribute:: render_hint

    a :class:`RenderHint` instance indicating the preffered way to render
    this action in the user interface

These attributes are used at the default values for the creation of a
:class:`camelot.admin.action.base.State` object that defines the appearance
of the action button.  Subclasses of :class:`Action` that require dynamic
values for these attributes can reimplement the :class:`Action.get_state`
method.

.. attribute:: verbose_name

    The name as displayed to the user, this should be of type 
    :class:`camelot.core.utils.ugettext_lazy`
    
.. attribute:: icon

    The icon that represents the action, of type 
    :class:`camelot.view.art.Icon`

.. attribute:: tooltip

    The tooltip as displayed to the user, this should be of type 
    :class:`camelot.core.utils.ugettext_lazy` or :class:`QtGui.QKeySequence`

.. attribute:: modes

    The modes in which an action can be triggered, a list of :class:`Mode`
    objects.
    
For each of these attributes there is a corresponding getter method
which is used by the view.  Subclasses of :class:`Action` that require dynamic
values for these attributes can reimplement the getter methods.

.. attribute:: shortcut

    The shortcut that can be used to trigger the action, this should be of 
    type :class:`camelot.core.utils.ugettext_lazy`
    
.. attribute:: drop_mime_types

    A list of strings with the mime types that can be used to trigger this
    action by dropping objects on the related widget.  Example ::
    
        drop_mime_types = ['text/plain']
    
An action has two important methods that can be reimplemented.  These are 
:meth:`model_run` for manipulations of the model and :meth:`gui_run` for
direct manipulations of the user interface without a need to access the model.

To prevent an action object from being garbage collected, it can be registered
with a view.

        """

    name = u'action'
    render_hint = RenderHint.PUSH_BUTTON
    verbose_name = None
    icon = None
    tooltip = None
    shortcut = None 
    modes = []
    drop_mime_types = []
    
    def get_name( self ):
        """
        :return: a string, by default the :attr:`name` attribute
        """
        return self.name
    
    def get_shortcut( self ):
        """
        :return: a :class:`camelot.core.utils.ugettext_lazy`, by default the 
        :attr:`shortcut` attribute
        """
        return self.shortcut

    def get_tooltip( self ):
        """
        :return: a `str` with the tooltip to display, by default this is
            a combination of the :attr:`tooltip` and the :attr:`shortcut`
            attribute
        """
        tooltip = None

        if self.tooltip is not None:
            tooltip = six.text_type(self.tooltip)

        if isinstance(self.shortcut, QtGui.QKeySequence):
            tooltip = (tooltip or u'') + '\n' + self.shortcut.toString(QtGui.QKeySequence.NativeText)
        elif isinstance(self.shortcut, QtGui.QKeySequence.StandardKey):
            for shortcut in QtGui.QKeySequence.keyBindings(self.shortcut):
                tooltip = (tooltip or u'') + '\n' + shortcut.toString(QtGui.QKeySequence.NativeText)
                break
        elif self.shortcut is not None:
            tooltip = (tooltip or u'') + '\n' + six.text_type(self.shortcut)

        return tooltip


    def gui_run( self, gui_context ):
        """This method is called inside the GUI thread, by default it
        executes the :meth:`model_run` in the Model thread.
        
        :param gui_context: the context available in the *GUI thread*,
            of type :class:`GuiContext`
            
        """
        from ..application_admin import ApplicationAdmin
        # only create a progress dialog if there is none yet, or if the
        # existing dialog was canceled
        LOGGER.debug( 'action gui run started' )
        with ProgressLevel(gui_context, str(self.verbose_name)):
            if gui_context.admin is None:
                gui_context.admin = ApplicationAdmin()
            super(Action, self).gui_run(gui_context)
        LOGGER.debug( 'gui run finished' )
        
    def get_state( self, model_context ):
        """
        This method is called inside the Model thread to verify if
        the state of the action widget visible to the current user.
        
        :param model_context: the context available in the *Model thread*
        :return: an instance of :class:`camelot.admin.action.base.State`
        """
        state = State()
        state.verbose_name = self.verbose_name
        state.icon = self.icon
        state.tooltip = self.get_tooltip()
        state.modes = self.modes
        return state



