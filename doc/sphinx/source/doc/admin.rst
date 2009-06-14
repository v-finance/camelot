.. _doc-admin:

##############################
  Customizing the Admin class
##############################

:Release: |version|
:Date: |today|

Each elixir Entity that is visualized within Camelot has an associated Admin
class which specifies how the entity or a list of entities should be visualized.

Those entities are subclasses of the EntityAdmin class in the module 
camelot/view/elixir_admin.

Usually the Admin class is bound to the Entity class by defining it as an
inner class of the Admin class::

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

Validators
==========

Before an object is written to the database it needs to be validated, and
the user needs to be informed in case the object is not valid.

By default Camelot does some introspection on the model to check the validity
of an object, to make sure it will be able to write the object to the
database.

But this might not be enough.  If more validation is needed, a custom Validator
class can be defined.  The default Validator class is located in 
camelot/view/validator::

  class MyValidator(Validator):
  
    def objectValidity(self, entity_instance):
      messages = super(MyValidator.self).objectValidity(entity_instance)
      if 'Star' not in entity_instance.title:
        messages.append("The movie title should always contain 'Star'.")
      return messages

Its most important method is objectValidity, which takes an object as argument and
should return a list of strings explaining why the object is invalid.  These
strings will then be presented to the user.

Notice that this method will always get called outside of the GUI thread, so the
call will never block the GUI.

Then tell the Admin interface to pickup the custom Validator ::

  class Movie(Entity):
    title = Field(Unicode(60), required=True)

    class Admin(EntityAdmin):
      name = 'Movies'
      list_display = ['title']
      validator = MyValidator
