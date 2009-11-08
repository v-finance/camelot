.. _doc-admin:

###############################
  Customizing the Admin classes
###############################

:Release: |version|
:Date: |today|

The Admin classes are the classes that specify how objects should be visualized,
they define the look, feel and behaviour of the Application.  Most of the behaviour
of the Admin classes can be tuned by changing their static attributes.  This makes
it easy to subclass a default Admin class and tune it to your needs.

Each elixir Entity that is visualized within Camelot has an associated Admin
class which specifies how the entity or a list of entities should be visualized.

Those entities are subclasses of the EntityAdmin class in the module 
camelot/view/elixir_admin.

Usually the Admin class is bound to the Entity class by defining it as an
inner class of the Entity class::

  class Movie(Entity):
    title = Field(Unicode(60), required=True)

    class Admin(EntityAdmin):
      name = 'Movies'
      list_display = ['title']

Most of the behaviour of the Admin class can be customized by changing
the class attributes like name or list_display.

ObjectAdmin
===========

The base type of EntityAdmin, is ObjectAdmin, which specifies most of the class attributes
that can be used to customize the interface.  

.. autoclass:: camelot.admin.object_admin.ObjectAdmin

.. note::
  While EntityAdmin can only be used for classes
  that are mapped by Sqlalchemy, ObjectAdmin can be used for plain old python objects as well.

EntityAdmin
===========

EntityAdmin is a specialization of ObjectAdmin, to be used for classes that are mapped by
Sqlalchemy.  EntityAdmin will use introspection to determine field types and assign 
according delegates and editors.

.. _form-actions:

Form View Actions
=================

.. automodule:: camelot.admin.form_action

Printing reports in the form view
---------------------------------

.. autoclass:: camelot.admin.form_action.PrintHtmlFormAction

.. _validators:

Validators
==========

Before an object is written to the database it needs to be validated, and
the user needs to be informed in case the object is not valid.

By default Camelot does some introspection on the model to check the validity
of an object, to make sure it will be able to write the object to the
database.

But this might not be enough.  If more validation is needed, a custom Validator
class can be defined.  The default EntityValidator class is located in 
camelot/admin/validator/entity_validator.  This class can be subclassed to
create a custom validator.  The new class should then be bound to the
Admin class :

  .. literalinclude:: ../../../../test/snippet/entity_validator.py

Its most important method is objectValidity, which takes an object as argument and
should return a list of strings explaining why the object is invalid.  These
strings will then be presented to the user.

Notice that this method will always get called outside of the GUI thread, so the
call will never block the GUI.

When the user tries to leave a form in an invalid state, a platform dependent dialog
box will appear.

  .. image:: ../_static/snippets/entity_validator.png

ApplicationAdmin
================

.. autoclass:: camelot.admin.application_admin.ApplicationAdmin

  .. literalinclude:: ../../../../example/application_admin.py