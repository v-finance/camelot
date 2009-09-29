.. _doc-forms:

################################
 Form layout and customization
################################

:Release: |version|
:Date: |today|

This section describes how to place fields on forms and applying
various layouts.  It also covers how to use form layouts outside
of the Admin class.

Form
====

A form is a collection of fields organized within a layout.  Each
field is represented by its editor.

Usually forms are defined by specifying the 'form_display' attribute of an
ObjectAdmin class :

.. literalinclude:: ../../../../test/snippet/form/simple_form.py

.. image:: ../_static/form/form.png

The 'form_display' attribute should either be a list of fields to display
or an instance of camelot.view.forms.Form.

Available Form Layouts
======================

camelot.view.forms.Form has several subclasses that can be used to create
various layouts.

.. automodule:: camelot.view.forms
   :members: