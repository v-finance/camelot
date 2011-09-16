.. _doc-actions-new:

#############
 New Actions
#############

status : draft

Motivation
==========

The current action framework in Camelot has worked well for 
actions with little user interaction.  It however misses some
functions such as enabling the user to cancel an ongoing action,
or to decide at run time which questions will be asked to the
user.

The implementation of the actions within Camelot requires a
lot of boilerplate code that needs to be written for each 
type of action.  There are for example 2 print preview actions,
one for the form view and one for the list view.

This proposal aims to solve these issues, and make it easy 
to implement more sophisticated actions.

After implementing this proposal it should be possible to
implement parts of Camelot itself as actions.  This would
enable more customization.

Introduction
============

Besides displaying and editing data, every application needs the
functions to manipulate data or create reports.  In the Camelot
framework this is done through actions.  Actions appear as buttons
on the side of a form and a table.  When the user clicks on an
action button, a predefined function is called.

.. image:: ../_static/entityviews/new_view_address.png
  
An action is available to show the address on a map

Camelot comes with a set of standard actions that are easily 
extended to manipulate data or create reports.  When defining actions,
a clear distinction should be made between things happening in the
model thread (the manipulation or querying of data, and things happening
in the gui thread (pop up windows or reports).  The :ref:`doc-threads`
section gives more detail on this.

Summary
=======

In general, actions are defined by subclassing one of the standard Camelot
actions  (:class:`camelot.admin.action.ApplicationAction`,
:class:`camelot.admin.action.ListAction` or 
:class:`camelot.admin.action.FormAction`)
that share the same behavior and class attributes ::

    from camelot.admin.action import ApplicationAction, PrintPreview
    from camelot.core.utils import ugettext_lazy as _
    from camelot.view.art import Icon
    
    class PrintReport( ApplicationAction ):
        verbose_name = _('Print Report')
        icon = Icon('tango/16x16/actions/document-print.png')
        tooltip = _('Print a report with all the movies')
        
        def model_run( self, model_context ):
            yield PrintPreview( 'Hello World' )
            
Each standard action has two methods, :meth:`gui_run` and 
:meth:`model_run`, one of
them should be overloaded in the subclass to either run the action in the
gui thread or to run the action in the model thread.  The default 
:meth:`ApplicationAction.gui_run`
behavior is to pop-up a :class:`camelot.view.controls.ProgressDialog` dialog and 
start the :meth:`model_run` method in the model thread.

:meth:`model_run` in itself is a generator, that can yield 
object back to the gui, such as a :class:`camelot.admin.action.PrintPreview`.
            
The action subclass can than be used a an element of the actions list of an 
:class:`camelot.admin.application_admin.ApplicationAdmin` subclass::

    from camelot.admin.application_admin import ApplicationAdmin
    
    class MyApplicationAdmin( ApplicationAdmin ):

        actions = [ PrintReport ]
            
What can happen inside :meth:`model_run`
========================================

:keyword:`yield` events to the GUI
----------------------------------

But actions need to be able to send their results back to the user, or ask
the user for additional information.  This is done with the :keyword:`yield` 
statement.

Through :keyword:`yield`, an object is send to the GUI thread, where it creates
user action, and sends it result back to the 'model_thread'.  The model_thread
will be blocked while the action in the GUI thread takes place, eg ::

    yield PrintPreview( 'Hello World' )

Will pop up a print preview dialog in the GUI.

Events that can be yielded to the GUI should be of type 
:class:`camelot.admin.action.ActionStep`.  Action steps are reusable parts of
an action:

.. autoclass:: camelot.admin.action.ActionStep

Possible Action Steps that can be yielded to the GUI include:

  * :class:`camelot.view.action_steps.PrintPreview`
  * :class:`camelot.view.action_steps.OpenFile`
  * :class:`camelot.view.action_steps.OpenStream`
  * :class:`camelot.view.action_steps.OpenJinjaTemplate`
  * :class:`camelot.view.action_steps.ShowPixmap`
  * :class:`camelot.view.action_steps.ShowChart`

keep the user informed about progress
-------------------------------------

An :obj:`camelot.view.action_steps.UpdateProgress` object can be yielded, to update
the state of the progress dialog:

.. autoclass:: camelot.view.action_steps.UpdateProgress
        
This should be done regulary to keep the user informed about the
progres of the action::

    movie_count = Movie.query.count()

    report = '<table>'
    for i, movie in enumerate( Movie.query.all() ):
        report += '<tr><td>%s</td></tr>'%(movie.name)
        yield UpdateProgress( i, movie_count )
    report += '</table>'

    yield PrintPreview( report )

Should the user have pressed the :guilabel:`Cancel` button in the progress 
dialog, the next yield of an UpdateProgress object will raise a 
:class:`camelot.core.exception.CancelRequest`.  

In case an unexpected event occurs in the GUI, the :keyword:`yield` statement 
will raise a :class:`camelot.core.exception.GuiException`.  This exception
will propagate through the action an will be ignored unless handled by the
developer.

manipulation of the model
-------------------------

The most important purpose of an action is to query or manipulate the model,
all such things can be done in the :meth:`model_run` method, such as executing 
queries, manipulating files, etc.

Whenever a part of the model has been changed, it might be needed to inform
the GUI about this, so that it can update itself, the easy way of doing so
is by yielding an instance of :class:`camelot.view.action_steps.FlushSession` 
such as::

    from sqlalchemy.orm.session import object_session
    movie.rating = 5
    yield FlushSession( object_session( movie ) )
    
This will flush the session to the database, and at the same time update
the GUI so that the flushed changes are shown to the user by updating the
visualisation of the changed movie on every screen in the application that 
displays this object.  Alternative updates that can be generated are :

  * :class:`camelot.view.action_steps.ObjectUpdated`, if one wants to inform
    the GUI an object is going to be updated.
  * :class:`camelot.view.action_steps.ObjectDeleted`, if one wants to inform
    the GUI an object is going to be deleted.
  * :class:`camelot.view.action_steps.ObjectCreated`, if one wants to inform
    the GUI an object has been created.

raise exceptions
----------------

When an action fails, a normal Python :keyword:`Exception` can be raised, which
will pop-up an exception dialog to the user that displays a stack trace of the
exception.  In case no stack trace should be shown to the user, a 
:class:`camelot.core.exception.UserException` should be raised. This will popup
a friendly dialog :

.. image:: /_static/controls/user_exception.png

When the :meth:`model_run` method raises a :class:`camelot.core.exception.CancelRequest`,
a :class:`GeneratorExit` or a :class:`StopIteration` exception, these are 
ignored and nothing will be shown to the user.

request information from the user
---------------------------------

The pop-up of a dialog that presents the user with a number of options can be 
triggered from within the :meth:`model_run` method.  This
happens by transferring an **options** object back and forth between the 
**model_thread** and the **gui_thread**.  To transfer such an object, this object
first needs to be defined::

    class Options( object ):
        
        def __init__(self):
            self.earliest_releasedate = datetime.date(2000, 1, 1)
            self.latest_releasedate = datetime.date.today()
            
        class Admin( ObjectAdmin ):
            form_display = [ 'earliest_releasedate', 'latest_releasedate' ]
            field_attributes = { 'earliest_releasedate':{'delegate':delegates.DateDelegate},
                                 'latest_releasedate':{'delegate':delegates.DateDelegate}, }
                                 
Than a :class:`camelot.view.action_steps.ChangeObject` can be :keyword:`yield` to present
the options to the user and get the filled in values back:

.. literalinclude:: ../../../../camelot/bin/meta.py
   :start-after: begin change object
   :end-before: end change object
                                 
Will show a dialog to modify the object:

..image:: /_static/actionsteps/change_object.png

When the user presses :guilabel:`Cancel` button of the dialog, the 
:keyword:`yield` statement will raise a 
:class:`camelot.core.exception.CancelRequest`.

Other ways of requesting information are :

  * :class:`camelot.view.action_steps.NewObject`, to request the user to fill in
    a new form for an object of a specified class.  This will return such
    a new object or None if the user canceled the operation.
  * :class:`camelot.view.action_steps.SelectFile`, to request to select an existing
    file to process or a new file to save information.

States and Modes
================

States
------

The widget that is used to trigger an action can be in different states.  The
default supported states are :

  - *enabled* : this is the default state, where the user is able to trigger
    the action
    
  - *disabled* : in this state the user is unable to trigger the action
  
  - *forbidden* : the user has no permission to trigger the action
  
  - *hidden* : the action widget is not visible
  
  - *notification* : the action widget attracts the attention of the user, this
    implies it is 'enabled'
    
Modes
-----

An action widget can be triggered in different modes, for example a print button
can be triggered as simply 'Print' or 'Export to PDF'.  The different modes of
an action are specified as a list of :class:`camelot.admin.action.Mode` objects:

.. autoclass:: camelot.admin.action.Action            

Actions and Context
===================

All action classes are based on the :class:`camelot.admin.action.Action`
class.  An Action is in fact a special :class:`camelot.admin.action.ActionStep`,
with some additional methods:

.. autoclass:: camelot.admin.action.Action
    
The :attr:`name` attribute specifies the name of the action as it will be stored
in the permission and preferences system.
  
Context
-------

Depending on where an action was triggered, a different context will be 
available during its execution in :meth:`camelot.admin.action.Action.gui_run`
and :meth:`camelot.admin.action.Action.model_run`.

The minimal context available in the *GUI thread* is :

.. autoclass:: camelot.admin.action.GuiContext

ApplicationAction
-----------------

The API of the :class:`camelot.admin.action.ApplicationAction`::

.. autoclass:: camelot.admin.action.ApplicationAction
            
To enable Application Actions for a certain 
:class:`camelot.admin.application_admin.ApplicationAdmin` either overwrite
its :meth:`camelot.admin.application_admin.ApplicationAdmin.get_actions`
or specify the :attr:`actions` attribute::

    from camelot.admin.application_admin import ApplicationAdmin
    from camelot.admin.action import ApplicationAction
    
    class GenerateReports(ApplicationAction):
    
        verbose_name = _('Generate Reports')
        
        def model_run( self, mode=None):
            print 'generating reports'
            for i in range(10):
                yield UpdateProgress(i, 10)
    
    class MyApplicationAdmin( ApplicationAdmin )
    
          actions = [GenerateReports,]

FormAction
----------

The API of the :class:`camelot.admin.action.FormAction`::

    class FormAction( AbstractAction ):
    
        def render( self, parent, view, widget_mapper ):
            """
            :param parent: the parent :class:`QtGui.QWidget`
            :param view: the :class:`camelot.view.controls.AbstractView` object
                to which this action belongs.
            :param widget_mapper: the :class:`QtGui.QDataWidgetMapper` class
                that relates to the form view on which the widget will be
                placed.
            :return: a :class:`QtGui.QWidget` which when triggered
                will execute the run method.
            """
            
        def gui_run( self,
                     widget,
                     widget_mapper,
                     mode ):
            """This method is called inside the GUI thread, by default it
            executes the :meth:`model_run` in the Model thread.
            :param widget: the rendered :class:`QtGui.QWidget` that triggered
                the method call
            :param selection_model: the :class:`QtGui.QDataWidgetMapper` class
            :param mode: the name of the mode in which this action was triggered.
            """
            pass
            
        def model_run( self,
                       current_obj,
                       mode = None ):
            """This generator method is called inside the Model thread.
            :param current_obj: the object in the current row
                current column
            :param mode: the mode in which the action was triggered.
            """
            pass
            
        def get_state( self, 
                        current_obj ):
            """This method is called inside the Model thread to verify if
            the state of the action widget visible to the current user.
            :return: a :keyword:`str`
            """
            return 'enabled'

ListAction
----------

The API of the :class:`camelot.admin.action.ListAction`::

    class ListAction( AbstractAction ):
    
        def render( self, parent, view, selection_model ):
            """
            :param parent: the parent :class:`QtGui.QWidget`
            :param view: the :class:`camelot.view.controls.AbstractView` object
                to which this action belongs.
            :param selection_model: the :class:`QtGui.QItemSelectionModel` class
                that relates to the table view on which the widget will be
                placed.
            :return: a :class:`QtGui.QWidget` which when triggered
                will execute the run method.
            """
            
        def gui_run( self,
                     widget,
                     selection_model,
                     mode ):
            """This method is called inside the GUI thread, by default it
            executes the :meth:`model_run` in the Model thread.
            :param widget: the rendered :class:`QtGui.QWidget` that triggered
                the method call
            :param selection_model: the :class:`QtGui.QItemSelectionModel` class
            :param mode: the name of the mode in which this action was triggered.
            """
            pass
            
        def model_run( self,
                       collection, 
                       selection,
                       current_obj,
                       current_field,
                       mode = None):
            """This generator method is called inside the Model thread.
            :param collection: an iterator for all objects in the collection
                displayed in the table view.
            :param selection: an iterator for all object selected
            :param current_obj: the object in the current row
            :param current_field: the name of the field that is displayed in the
                current column
            :param mode: the mode in which the action was triggered.
            """
            pass
            
        def get_state( self, 
                       collection_length,
                       selection_length,
                       current_obj,
                       current_field ):
            """This method is called inside the Model thread to verify the state
            of the action widget visible to the current user.
            :return: a :keyword:`str`
            """
            return 'enabled'
            
Inspiration
===========

  * Implementing actions as generators was made possible with the language functions
    of :pep:`342`.  
    
  * The EuroPython talk of Erik Groeneveld inspired the use of these
    features. (http://ep2011.europython.eu/conference/talks/beyond-python-enhanched-generators)
    
  * Action steps were introduced to be able to take advantage of the new language
    features of :pep:`380` in Python 3.3

