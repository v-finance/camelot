.. _doc-actions:

#########
 Actions
#########

Introduction
============

Besides displaying and editing data, every application needs the
functions to manipulate data or create reports.  In Camelot this is done through 
actions.  Actions can appear as buttons on the side of a form or a table, as
icons in a toolbar or as icons in the home workspace.

.. image:: /_static/entityviews/new_view_address.png
  
Every Action is build up with a set of Action Steps.  An Action Step is a
reusable part of an Action, such as for example, ask the user to select a
file.  Camelot comes with a set of standard Actions and Action Steps that are 
easily extended to manipulate data or create reports.  

When defining Actions, a clear distinction should be made between things 
happening in the model thread (the manipulation or querying of data), and things 
happening in the gui thread (pop up windows or reports).  The :ref:`doc-threads`
section gives more detail on this.

Summary
=======

In general, actions are defined by subclassing the standard Camelot
:class:`camelot.admin.action.Action` class ::

    from camelot.admin.action import Action
    from camelot.view.action_steps import PrintHtml
    from camelot.core.utils import ugettext_lazy as _
    from camelot.view.art import Icon
    
    class PrintReport( Action ):
    
        verbose_name = _('Print Report')
        icon = Icon('tango/16x16/actions/document-print.png')
        tooltip = _('Print a report with all the movies')
        
        def model_run( self, model_context ):
            yield PrintHtml( 'Hello World' )
            
Each action has two methods, :meth:`gui_run` and  :meth:`model_run`, one of
them should be reimplemented in the subclass to either run the action in the
gui thread or to run the action in the model thread.  The default 
:meth:`Action.gui_run` behavior is to pop-up a :class:`ProgressDialog` dialog 
and start the :meth:`model_run` method in the model thread.

:meth:`model_run` in itself is a generator, that can yield :class:`ActionStep` 
objects back to the gui, such as a :class:`PrintHtml`.
            
The action objects can than be used a an element of the actions list returned by 
the :meth:`ApplicationAdmin.get_actions` method:

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin actions
   :end-before: end actions
   
or be used in the :attr:`ObjectAdmin.list_actions` or 
:attr:`ObjectAdmin.form_actions` attributes.

The :ref:`tutorial-importer` tutorial has a complete example of creating and
using and action.
   
What can happen inside :meth:`model_run`
========================================

:keyword:`yield` events to the GUI
----------------------------------

Actions need to be able to send their results back to the user, or ask
the user for additional information.  This is done with the :keyword:`yield` 
statement.

Through :keyword:`yield`, an Action Step is send to the GUI thread, where it creates
user interaction, and sends it result back to the 'model_thread'.  The model_thread
will be blocked while the action in the GUI thread takes place, eg ::

    yield PrintHtml( 'Hello World' )

Will pop up a print preview dialog in the GUI, and the model_run method will
only continue when this dialog is closed.

Events that can be yielded to the GUI should be of type 
:class:`camelot.admin.action.base.ActionStep`.  Action steps are reusable parts of
an action.  Possible Action Steps that can be yielded to the GUI include:

  * :class:`camelot.view.action_steps.change_object.ChangeObject`
  * :class:`camelot.view.action_steps.change_object.ChangeObjects`
  * :class:`camelot.view.action_steps.print_preview.PrintPreview`
  * :class:`camelot.view.action_steps.print_preview.PrintHtml`
  * :class:`camelot.view.action_steps.print_preview.PrintJinjaTemplate`
  * :class:`camelot.view.action_steps.open_file.OpenFile`
  * :class:`camelot.view.action_steps.open_file.OpenStream`
  * :class:`camelot.view.action_steps.open_file.OpenJinjaTemplate`
  * :class:`camelot.view.action_steps.gui.CloseView`
  * :class:`camelot.view.action_steps.gui.MessageBox`
  * :class:`camelot.view.action_steps.gui.Refresh`
  * :class:`camelot.view.action_steps.gui.OpenFormView`
  * :class:`camelot.view.action_steps.gui.ShowPixmap`
  * :class:`camelot.view.action_steps.gui.ShowChart`
  * :class:`camelot.view.action_steps.select_file.SelectFile`
  * :class:`camelot.view.action_steps.select_object.SelectObject`

keep the user informed about progress
-------------------------------------

An :obj:`camelot.view.action_steps.update_progress.UpdateProgress` object can be 
yielded, to update the state of the progress dialog:
        
This should be done regulary to keep the user informed about the
progres of the action::

    movie_count = Movie.query.count()

    report = '<table>'
    for i, movie in enumerate( Movie.query.all() ):
        report += '<tr><td>%s</td></tr>'%(movie.name)
        yield UpdateProgress( i, movie_count )
    report += '</table>'

    yield PrintHtml( report )

Should the user have pressed the :guilabel:`Cancel` button in the progress 
dialog, the next yield of an UpdateProgress object will raise a 
:class:`camelot.core.exception.CancelRequest`.  

manipulation of the model
-------------------------

The most important purpose of an action is to query or manipulate the model,
all such things can be done in the :meth:`model_run` method, such as executing 
queries, manipulating files, etc.

Whenever a part of the model has been changed, it might be needed to inform
the GUI about this, so that it can update itself, the easy way of doing so
is by yielding an instance of :class:`camelot.view.action_steps.orm.FlushSession` 
such as::

    movie.rating = 5
    yield FlushSession( model_context.session )
    
This will flush the session to the database, and at the same time update
the GUI so that the flushed changes are shown to the user by updating the
visualisation of the changed movie on every screen in the application that 
displays this object.  Alternative updates that can be generated are :

  * :class:`camelot.view.action_steps.orm.UpdateObject`, if one wants to inform
    the GUI an object has been updated.
  * :class:`camelot.view.action_steps.orm.DeleteObject`, if one wants to inform
    the GUI an object is going to be deleted.
  * :class:`camelot.view.action_steps.orm.CreateObject`, if one wants to inform
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

handle exceptions
-----------------

In case an unexpected event occurs in the GUI, a :keyword:`yield` statement 
will raise a :class:`camelot.core.exception.GuiException`.  This exception
will propagate through the action an will be ignored unless handled by the
developer.

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
                                 
Than a :class:`camelot.view.action_steps.change_object.ChangeObject` action step can be 
:keyword:`yield` to present the options to the user and get the filled in values back :

.. literalinclude:: ../../../../camelot/bin/meta.py
   :start-after: begin change object
   :end-before: end change object
                                 
Will show a dialog to modify the object:

.. image:: /_static/actionsteps/change_object.png

When the user presses :guilabel:`Cancel` button of the dialog, the 
:keyword:`yield` statement will raise a 
:class:`camelot.core.exception.CancelRequest`.

Other ways of requesting information are :

  * :class:`camelot.view.action_steps.select_file.SelectFile`, to request 
    to select an existing file to process or a new file to save information.
    
Issue SQLAlchemy statements
---------------------------

Camelot itself only manipulates the database through objects of the
ORM for the sake of make no difference between objects mapped to the database
and plain old python objects.  But for performance reasons, it is often desired
to do manipulations directly through SQLAlchemy ORM or Core queries :

.. literalinclude:: ../../../../test/test_action.py
   :start-after: begin issue a query through the model_context
   :end-before: end issue a query through the model_context

States and Modes
================

States
------

The widget that is used to trigger an action can be in different states.  A 
:class:`camelot.admin.action.base.State` object is returned by the 
:class:`camelot.admin.action.base.Action.get_state` method.  Subclasses of 
Action can reimplement this method to change the State of an action button.

This allows to hide or disable the action button, depending on the objects 
selected or the current object being displayed.
    
Modes
-----

An action widget can be triggered in different modes, for example a print button
can be triggered as *Print* or *Export to PDF*.  The different modes of
an action are specified as a list of :class:`camelot.admin.action.base.Mode` objects.

To change the modes of an Action, either specify the :attr:`modes` attribute of
an :class:`Action` or specify the :attr:`modes` attribute of the :class:`State`
returned by the :meth:`Action.get_state` method.

Action Context
==============

Depending on where an action was triggered, a different context will be 
available during its execution in :meth:`camelot.admin.action.base.Action.gui_run`
and :meth:`camelot.admin.action.base.Action.model_run`.

The minimal context available in the *GUI thread* when :meth:`gui_run` is
called :

.. autoclass:: camelot.admin.action.base.GuiContext
   :noindex:

While the minimal contact available in the *Model thread* when :meth:`model_run`
is called :

.. autoclass:: camelot.admin.action.base.ModelContext
   :noindex:

.. _doc-application-action:

Application Actions
-------------------
            
To enable Application Actions for a certain :class:`ApplicationAdmin` overwrite 
its :meth:`ApplicationAdmin.get_actions` method::

    from camelot.admin.application_admin import ApplicationAdmin
    from camelot.admin.action import Action
    
    class GenerateReports( Action ):
    
        verbose_name = _('Generate Reports')
        
        def model_run( self, model_context):
            for i in range(10):
                yield UpdateProgress(i, 10)
    
    class MyApplicationAdmin( ApplicationAdmin )
    
        def get_actions( self ):
            return [GenerateReports(),]
          
An action specified here will receive an :class:`ApplicationActionGuiContext` 
object as the *gui_context* argument of the the :meth:`gui_run`
method, and a :class:`ApplicationActionModelContext` object as the 
*model_context* argument of the :meth:`model_run` method.

.. autoclass:: camelot.admin.action.application_action.ApplicationActionGuiContext
   :noindex:

.. autoclass:: camelot.admin.action.application_action.ApplicationActionModelContext
   :noindex:
   :members:
   
Form Actions
------------

A form action has access to the object currently visible on the form.

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin simple action definition
   :end-before: end simple action definition
   
To enable Form Actions for a certain :class:`ObjectAdmin` or :class:`EntityAdmin`, 
specify the :attr:`form_actions` attribute.

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin form_actions
   :end-before: end form_actions

.. image:: /_static/entityviews/new_view_movie.png

An action specified here will receive a :class:`FormActionGuiContext`  object as the 
*gui_context* argument of the :meth:`gui_run` method, and a 
:class:`FormActionModelContext` object as the *model_context* argument of the 
:meth:`model_run` method.

.. autoclass:: camelot.admin.action.form_action.FormActionGuiContext
   :noindex:

.. autoclass:: camelot.admin.action.form_action.FormActionModelContext
   :noindex:
   :members:
   
List Actions
------------

A list action has access to both all the rows displayed in the table
(called the collection) and the rows selected by the user (called the
selection) :

.. literalinclude:: ../../../../camelot_example/change_rating.py
   :start-after: begin change rating action definition
   :end-before: end change rating action definition
   
To enable List Actions for a certain :class:`ObjectAdmin` or
:class:`EntityAdmin`, specify the :attr:`list_actions` attribute:

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin list_actions
   :end-before: end list_actions
   
This will result in a button being displayed on the table view.

.. image:: /_static/entityviews/table_view_movie.png

An action specified here will receive a :class:`ListActionGuiContext` object as 
the *gui_context* argument of th the :meth:`gui_run` method, and a 
:class:`ListActionModelContext` object as the *model_context* argument of the 
:meth:`model_run` method.

.. autoclass:: camelot.admin.action.list_action.ListActionGuiContext
   :noindex:

.. autoclass:: camelot.admin.action.list_action.ListActionModelContext
   :noindex:
   :members:

Reusing List and Form actions
-----------------------------

There is no need to define a different action subclass for form and list
actions, as both their model_context have a **get_selection** method, a single
action can be used both for the list and the form.

Available actions
=================

Camelot has a set of available actions that combine the various 
:class:`ActionStep` subclasses.  Those actions can be used directly or as an
inspiration to build new actions:

  * :class:`camelot.admin.action.application_action.OpenNewView`
  * :class:`camelot.admin.action.application_action.OpenTableView`
  * :class:`camelot.admin.action.application_action.ShowHelp`
  * :class:`camelot.admin.action.application_action.ShowAbout`
  * :class:`camelot.admin.action.application_action.Backup`
  * :class:`camelot.admin.action.application_action.Restore`
  * :class:`camelot.admin.action.application_action.Refresh`
  * :class:`camelot.admin.action.form_action.CloseForm`
  * :class:`camelot.admin.action.list_action.CallMethod`
  * :class:`camelot.admin.action.list_action.OpenFormView`
  * :class:`camelot.admin.action.list_action.OpenNewView`
  * :class:`camelot.admin.action.list_action.ToPreviousRow`
  * :class:`camelot.admin.action.list_action.ToNextRow`
  * :class:`camelot.admin.action.list_action.ToFirstRow`
  * :class:`camelot.admin.action.list_action.ToLastRow`
  * :class:`camelot.admin.action.list_action.ExportSpreadsheet`
  * :class:`camelot.admin.action.list_action.PrintPreview`
  * :class:`camelot.admin.action.list_action.SelectAll`
  * :class:`camelot.admin.action.list_action.ImportFromFile`  
  * :class:`camelot.admin.action.list_action.ReplaceFieldContents`
  
Inspiration
===========

  * Implementing actions as generators was made possible with the language functions
    of :pep:`342`.  
    
  * The EuroPython talk of Erik Groeneveld inspired the use of these
    features. (http://ep2011.europython.eu/conference/talks/beyond-python-enhanched-generators)
    
  * Action steps were introduced to be able to take advantage of the new language
    features of :pep:`380` in Python 3.3
