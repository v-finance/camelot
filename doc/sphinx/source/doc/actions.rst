.. _doc-actions:

####################
 Actions and Reports
####################

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

This section describes how to put any of the predefined action
buttons next to a form or a table.

.. _form-actions:

Form view actions
=================

.. automodule:: camelot.admin.form_action

All Form view actions are subclasses of the FormAction class, the
FormAction class specifies the name and the icon of the button
to trigger the action.  Its run method will be called whenever the
action is triggered.

.. autoclass:: camelot.admin.form_action.FormAction
   :members:

Manipulate the model
--------------------

.. autoclass:: camelot.admin.form_action.FormActionFromModelFunction
   :members:

Generate documents
------------------

Generating reports and documents is an important part of any application.
Python and Qt provide various ways to generate documents.  Each of them
with its own advantages and disadvantages.  

  +-----------------------+-------------------------+--------------------------+
  | Method                | Advantages              | Disadvantages            |
  +-----------------------+-------------------------+--------------------------+
  | PDF documents through | * Perfect control over  | * Relatively steep       |
  | reportlab             |   layout                |   learning curve         |
  |                       | * Excellent for mass    | * User cannot edit       |
  |                       |   creation of documents |   document               |
  +-----------------------+-------------------------+--------------------------+
  | HTML                  | * Easy to get started   | * Not much layout control|
  |                       | * Print preview within  | * User cannot edit       |
  |                       |   Camelot               |   document               |
  |                       | * No dependencies       |                          |
  +-----------------------+-------------------------+--------------------------+
  | Docx Word documents   | * User can edit         | * Proprietary format     |
  |                       |   document              | * Word processor needed  |
  +-----------------------+-------------------------+--------------------------+
  
Camelot leaves all options open to the developer.

Please have a look at :ref:`tutorial-reporting` to get started with generating
documents.

Printing through Html documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: camelot.admin.form_action.PrintHtmlFormAction
   :members:

Generating PDF, TXT and others
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   
.. autoclass:: camelot.admin.form_action.OpenFileFormAction
   :members:

DOCX Word documents
^^^^^^^^^^^^^^^^^^^

.. autoclass:: camelot.admin.form_action.DocxFormAction
   :members:
      
List view actions
=================

List actions, are actions that will appear on a table view, a very simple list
action is one that pops up a print preview of a report based on the current
table :

.. autoclass:: camelot.admin.list_action.PrintHtmlListAction

It is used by appending an instance of this action to the list actions of the
EntityAdmin::

   list_actions = [PrintHtmlListAction('Report')]
   
This will result in a Report button being displayed on the table view.

.. image:: ../_static/entityviews/table_view_movie.png

When this button is pressed, a report of the current table view will pop up.
To customize this report, one should subclass the PrintHtmlListAction and
create a custom html method::

   def html(self, collection, selection, options):
       return '<br/>'.join([movie.title for movie in collection])

The html function takes 3 arguments:

.. automethod:: camelot.admin.list_action.PrintHtmlListAction.html

Printing through Html documents
-------------------------------

A full example of a custom PrintHtmlListAction, including the use of Options
can look like this :

.. literalinclude:: ../../../../camelot_example/action.py

Actions in the model thread
---------------------------

.. autoclass:: camelot.admin.list_action.ListActionFromModelFunction
   :members:
