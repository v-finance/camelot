.. _doc-actions-new:

##############
 Actions (New)
##############

.. note::

   The functionality described here is currently not implemented in Camelot,
   but is a proposal for implementation, a Camelot Enhancement Proposal
   
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
:class:`camelot.admin.action.FromAction`)
that share the same behavior and class attributes ::

    from camelot.admin.action import FormAction, PrintPreview
    from camelot.core.utils import ugettext_lazy as _
    from camelot.view.art import Icon
    
    class PrintReport( FormAction ):
        verbose_name = _('Print Report')
        icon = Icon('tango/16x16/actions/document-print.png')
        tooltip = _('Print a report with all the movies')
        
        def model_run( self, obj, mode=None ):
            yield PrintPreview( 'hello %s'%(obj.name) )
            
Each standard action has two methods, `gui_run` and `model_run`, one of
them should be overloaded in the subclass to either run the action in the
gui thread or to run the action in the model thread.  The default `gui_run`
behavior is to pop-up a 'Please wait' dialog and pass control to the `model_run`
method.

`model_run` in itself is a generator, that can yield object back to the gui,
such as a :class:`camelot.admin.action.PrintPreview`.
            
The action subclass can than be used a an element of the actions list of an 
:class:`camelot.admin.entity_admin.EntityAdmin` subclass::

    from camelot.admin.entity_admin import EntityAdmin
    from elixir import Entity
    
    class Movie( Entity ):
        name = Field( Unicode( 50 ) )
        
        class Admin( EntityAdmin ):
            list_display = [ 'name' ]
            list_actions = [ PrintReport ]
            
What can happen inside :meth:`FormAction.model_run`
===================================================

manipulation of the model
-------------------------

The most important purpose of an action is to query or manipulate the model,
all such things can be done in the `model_run` method, such as executing queries,
manipulating files, etc.

keep the user informed about progress
-------------------------------------

Every action object has a method :

.. method:: update_progress(value=0, maximum=0, text=None, info=None, clear=False)
    :param value: the current step
    :param maximum: the maximum number of steps that will be executed. set it
        to 0 to display a busy indicator instead of a progres bar
    :param text: the text to be displayed inside the progres bar
    :param info: the text to be displayed below the progres bar, this text is
        appended to the text allready there
    :param clear: clear the info text allready there before putting the new info
        text.
        
This method should be called regulary to keep the user informed about the
progres of the action::

    report = '<table>'
    movie_count = Movie.query.count()
    for i, movie in enumerate( Movie.query.all() ):
        report += '<tr><td>%s</td></tr>'%(movie.name)
        self.update_progress( i, movie_count )
    report += '</table>'
    yield PrintPreview( report )

Should the user press the :guilabel:`Cancel` button in the progress dialog, the
next call to :meth:`update_progres` will raise a 
:class:`camelot.core.exeption.CancelRequest`.  The :meth:`model_run` its 
execution will not be blocked while the GUI updates the 
:class:`camelot.view.controls.ProgressDialog`

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

Possible results that can be send to the GUI are:

  * :class:`camelot.admin.action.PrintPreview`
  * :class:`camelot.admin.action.OpenFile`
  * :class:`camelot.admin.action.ShowPixmap`
  * :class:`camelot.admin.action.ShowChart`
  * :class:`camelot.admin.action.OpenDocx`

raise exceptions
----------------

When an action fails, a normal Python :keyword:`Exception` can be raised, which
will pop-up an exception dialog to the user that displays a stack trace of the
exception.  In case no stack trace should be shown to the user, a 
:class:`camelot.core.exception.UserException` should be raised.

When the :meth:`model_run` method raises a :class:`camelot.core.exception.CancelRequest`
or a :class:`GeneratorExit` exception, these are ignored and nothing will be
shown to the user.

the user cancels the action
---------------------------

Should the user press the :guilabel:`Cancel` button in the progress dialog, the
next :keyword:`yield` statement will raise a :class:`GeneratorExit` exception.

When this exception is raised, the :meth:`model_run` should handle it by not
not catching this exception, or do some cleanup, and then stop the iterator.

:pep:`342`