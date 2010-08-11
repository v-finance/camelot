===========
EntityAdmin
===========

EntityAdmin is a specialization of ObjectAdmin, to be used for classes that are mapped by
Sqlalchemy.  EntityAdmin will use introspection to determine field types and assign 
according delegates and editors.

.. autoclass:: camelot.admin.entity_admin.EntityAdmin
