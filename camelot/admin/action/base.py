#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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
references to widgets and other usefull information.  This object cannot
contain reference to anything database or model related, as those belong
strictly to the :class:`ModelContext`

.. attribute:: progress_dialog

    an instance of :class:`QtGui.QProgressDialog` or :keyword:`None'
    
.. attribute:: mode_name

    the name of the mode in which the action was triggered
    
.. attribute:: model_context

    a subclass of :class:`ModelContext` to be used in :method:`create_model_context`
    as the type of object to return.
    """
    
    model_context = ModelContext
    
    def __init__( self ):
        self.progress_dialog = None
        self.mode_name = None
        
    def create_model_context( self ):
        """Create a :class:`ModelContext` filled with base information, 
        extracted from this GuiContext.
        
        :return: a :class:`ModelContext`
        """
        context = self.model_context()
        context.mode_name = self.mode_name
        return context
        
    def copy( self ):
        """Create a copy of the GuiContext, this function is used
        to create new GuiContext's that are more specialized without
        modifying the original one."""
        new_context = self.__class__()
        new_context.progress_dialog = self.progress_dialog
        new_context.mode_name = self.mode_name
        return new_context
                    
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
        """
        from camelot.view.action_runner import ActionRunner
        runner = ActionRunner( self.model_run, gui_context, None )
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
GUI.  For each of these attributes there is a corresponding getter method
which is used by the view.  Subclasses of :class:`Action` that require dynamic
values for these attributes can reimplement the getter methods.
    
.. attribute:: name

    The internal name of the action, this can be used to store preferences
    concerning the action in the settings
    
.. attribute:: verbose_name

    The name as displayed to the user, this should be of type 
    :class:`camelot.core.utils.ugettext_lazy`
    
.. attribute:: icon

    The icon that represents the action, of type 
    :class:`camelot.view.art.Icon`

.. attribute:: tooltip

    The tooltip as displayed to the user, this should be of type 
    :class:`camelot.core.utils.ugettext_lazy`

.. attribute:: shortcut

    The shortcut that can be used to trigger the action, this should be of 
    type :class:`camelot.core.utils.ugettext_lazy`

.. attribute:: modes

    The modes in which an action can be triggered, a list of :class:`Mode`
    objects.
    
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
    
    def get_name( self ):
        """
        :return: a string, by default the :attr:`name` attribute
        """
        return self.name
    
    def get_verbose_name( self ):
        """
        :return: a :class:`camelot.core.utils.ugettext_lazy` string, by default 
            the :attr:`verbose_name` attribute
        """
        return self.verbose_name
    
    def get_icon( self ):
        """
        :return: a :class:`camelot.view.art.Icon`, by default the :attr:`icon` 
            attribute
        """
        return self.icon
    
    def get_tooltip( self ):
        """
        :return: a :class:`camelot.core.utils.ugettext_lazy`, by default the 
            :attr:`tooltip` attribute
        """
        return self.tooltip
    
    def get_shortcut( self ):
        """
        :return: a :class:`camelot.core.utils.ugettext_lazy`, by default the 
        :attr:`shortcut` attribute
        """
        return self.shortcut
    
    def get_modes( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Mode` objects, 
            by default the :attr:`modes` attribute
        """
        return self.modes
    
    def render( self, parent, gui_context ):
        """
        :param parent: the parent :class:`QtGui.QWidget`
        :param gui_context: the context available in the *GUI thread*, a
            subclass of :class:`camelot.action.GuiContext`
        :return: a :class:`QtGui.QWidget` which when triggered
            will execute the :meth:`gui_run` method.
        """
        
    def gui_run( self, gui_context ):
        """This method is called inside the GUI thread, by default it
        executes the :meth:`model_run` in the Model thread.
        :param gui_context: the context available in the *GUI thread*,
            of type :class:`GuiContext`
        """
        super(Action, self).gui_run( gui_context )
        
    def get_state( self, model_context ):
        """
        This method is called inside the Model thread to verify if
        the state of the action widget visible to the current user.
        
        :param model_context: the context available in the *Model thread*
        :return: a :keyword:`str`
        """
        return 'enabled'
