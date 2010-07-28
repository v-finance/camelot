.. _validators:

==========
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
