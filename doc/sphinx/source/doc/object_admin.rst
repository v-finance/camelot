===========
ObjectAdmin
===========

The base type of EntityAdmin, is ObjectAdmin, which specifies most of the class attributes
that can be used to customize the interface.  

.. autoclass:: camelot.admin.object_admin.ObjectAdmin

Other Admin classes can inherit ObjectAdmin if they want to provide additional functionallity,
like introspection to set default field_attributes.

.. note::
  While EntityAdmin can only be used for classes
  that are mapped by Sqlalchemy, ObjectAdmin can be used for plain old python objects as well.