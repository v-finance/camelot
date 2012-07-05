.. _cep-unified-model:

##########################
 Unified Model Definition
##########################

status : draft

.. note::
   This Camelot enhancement proposal is a work in progress and implementation
   has not started.

Introduction
============

When Camelot is used to display objects that are mapped to the database
through SQLAlchemy, Camelot uses introspection to create default views.

When displaying objects that are not mapped to the database, such 
introspection is not possible, which often leads to a rather verbose
definition of the model and the view ::

    class Simple( object ):

        def __init__( self ):
            self.x = 0
            self.y = 0

        class Admin( ObjectAdmin ):
            list_display = ['x', 'y']
            field_attributes = { 'x': {'delegate':delegates.IntegerDelegate,
                                       'editable':True},
                                 'y': {'delegate':delegates.IntegerDelegate,
                                       'editable':True}, }

This proposal aims to find a way to create a less descriptive way to
define model and view in the case of simple Python objects.

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
   
