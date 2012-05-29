===========
EntityAdmin
===========

:class:`camelot.admin.entity_admin.EntityAdmin` is a specialization of :class:`camelot.admin.object_admin.ObjectAdmin`, to be used for classes that are mapped by
SQLAlchemy.  `EntityAdmin` will use introspection to determine field types and assign according delegates and editors.

.. autoclass:: camelot.admin.entity_admin.EntityAdmin
