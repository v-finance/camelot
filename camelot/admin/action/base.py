#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

import logging

from PyQt4 import QtGui

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

.. attribute:: progress_dialog

    an instance of :class:`QtGui.QProgressDialog` or :keyword:`None`
    
.. attribute:: mode_name

    the name of the mode in which the action was triggered
    
.. attribute:: model_context

    a subclass of :class:`ModelContext` to be used in :meth:`create_model_context`
    as the type of object to return.
    """
    
    model_context = ModelContext
    
    def __init__( self ):
        self.progress_dialog = None
        self.mode_name = None
        
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
        new_context.progress_dialog = self.progress_dialog
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

    :keyword:`True` if the widget should be enabled (the default), 
    :keyword:`False` otherwise
    
.. attribute:: visible

    :keyword:`True` if the widget should be visible (the default), 
    :keyword:`False` otherwise

.. attribute:: notification

    :keyword:`True` if the buttons should attract the attention of the user, 
    defaults to :keyword:`False`.

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
        self.verbose_name = verbose_name or name.capitalize()
        self.icon = icon
        
    def render( self, parent ):
        """Create a :class:`QtGui.QAction` that can be used to enable widget
        to trigger the action in a specific mode.  The data attribute of the
        action will contain the name of the mode.
        
        :return: a :class:`QtGui.QAction` class to use this mode
        """
        action = QtGui.QAction( parent )
        action.setData( self.name )
        action.setText( unicode(self.verbose_name) )
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
    to :keyword:`True`
    """

    blocking = True
            
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

class Action( ActionStep ):
    """An action has a set of attributes that define its appearance in the
GUI.  
    
.. attribute:: name

    The internal name of the action, this can be used to store preferences
    concerning the action in the settings

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
    :class:`camelot.core.utils.ugettext_lazy`

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
        """
    
    name = u'action'
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
        
    def render( self, gui_context, parent ):
        """Create a widget to trigger the action.  Depending on the type of
        gui_context and parent, a different widget type might be returned.
        
        :param gui_context: the context available in the *GUI thread*, a
            subclass of :class:`camelot.action.GuiContext`
        :param parent: the parent :class:`QtGui.QWidget`
        :return: a :class:`QtGui.QWidget` which when triggered
            will execute the :meth:`gui_run` method.
        """
        from camelot.view.controls.action_widget import ( ActionLabel, 
                                                          ActionPushButton,
                                                          ActionAction )
        from camelot.view.workspace import DesktopBackground
        if isinstance( parent, DesktopBackground ):
            return ActionLabel( self, gui_context, parent )
        if isinstance( parent, (QtGui.QToolBar, QtGui.QMenu) ):
            return ActionAction( self, gui_context, parent )
        return ActionPushButton( self, gui_context, parent )
        
    def gui_run( self, gui_context ):
        """This method is called inside the GUI thread, by default it
        executes the :meth:`model_run` in the Model thread.
        
        :param gui_context: the context available in the *GUI thread*,
            of type :class:`GuiContext`
            
        """
        from camelot.view.controls.progress_dialog import ProgressDialog
        progress_dialog = None
        # only create a progress dialog if there is none yet, or if the
        # existing dialog was canceled
        LOGGER.debug( 'action gui run started' )
        if gui_context.progress_dialog and gui_context.progress_dialog.wasCanceled():
            gui_context.progress_dialog = None
        if gui_context.progress_dialog == None:
            LOGGER.debug( 'create new progress dialog' )
            progress_dialog = ProgressDialog( unicode( self.verbose_name ) )
            gui_context.progress_dialog = progress_dialog
            #progress_dialog.show()
        super(Action, self).gui_run( gui_context )
        # only close the progress dialog if it was created here
        if progress_dialog != None:
            progress_dialog.close()
            gui_context.progress_dialog = None
        LOGGER.debug( 'gui run finished' )
        
    def get_state( self, model_context ):
        """
        This method is called inside the Model thread to verify if
        the state of the action widget visible to the current user.
        
        :param model_context: the context available in the *Model thread*
        :return: an instance of :class:`camelot.action.base.State`
        """
        state = State()
        state.verbose_name = self.verbose_name
        state.icon = self.icon
        state.tooltip = self.tooltip
        state.modes = self.modes
        return state

