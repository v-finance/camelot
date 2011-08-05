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
            
What can an action do
=====================

The most important purpose of an action is to query or manipulate the model,
all such things can be done in the `model_run` method, such as executing queries,
manipulating files, etc.

But actions need to be able to send their results back to the user, or ask
the user for additional information.  This is done with the `yield` statement.

:pep:342