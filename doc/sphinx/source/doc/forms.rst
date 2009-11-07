.. _doc-forms:

###############
 Creating Forms
###############

:Release: |version|
:Date: |today|

This section describes how to place fields on forms and applying
various layouts.  It also covers how to customize forms to your
specific needs.  As with everything in Camelot, the goal of the framework
is that you can create 80% of your forms with minimal effort, while
the framework should allow you to really customize the other 20% of
your forms.

Form
====

A form is a collection of fields organized within a layout.  Each
field is represented by its editor.

Usually forms are defined by specifying the 'form_display' attribute of an
Admin class :

.. literalinclude:: ../../../../test/snippet/form/simple_form.py

.. image:: ../_static/form/form.png

The 'form_display' attribute should either be a list of fields to display
or an instance of camelot.view.forms.Form or its subclasses.

Forms can be nested into each other :

.. literalinclude:: ../../../../test/snippet/form/nested_form.py

.. image:: ../_static/form/nested_form.png

Inheritance and Forms
=====================

Just as Entities support inheritance, forms support inheritance as well.  This
avoids duplication of effort when designing and maintaining forms.  Each of the
Form subclasses has a set of methods to modify its content.  In the example below
a new tab is added to the form defined in the previous section.

.. literalinclude:: ../../../../test/snippet/form/inherited_form.py

.. image:: ../_static/form/inherited_form.png

Available Form Subclasses
=========================

camelot.view.forms.Form has several subclasses that can be used to create
various layouts.  Each subclass maps to a QT Layout class.

.. automodule:: camelot.view.forms
   :members: