.. _doc-actions:

####################
 Actions and Reports
####################

:Release: |version|
:Date: |today|

Besides displaying and editing data, every application needs the
functions to manipulate data or create reports.  In the Camelot
framework this is done through actions.  Actions appear as buttons
on the side of a form and a table.  When the user clicks on an
action button, a predefined function is called.

  .. image:: ../_static/entityviews/new_view_address.png
  
  an action is available to show the address on a map

Camelot comes with a set of standard actions that are easily 
extended to manipulate data or create reports.

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

Actions to generate documents
-----------------------------

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

.. autoclass:: camelot.admin.list_action.ListAction
   :members: