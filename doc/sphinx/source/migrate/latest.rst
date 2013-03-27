.. _migrate-latest:

Migrate from Camelot 12.06.29 to the latest version
===================================================

 * Replace all imports from `elixir` with import from `camelot.core.orm`.
   This should cover most use cases of Elixir, use cases that are not
   covered in the new module (inheritance, elixir extensions) should be
   rebuild using Declarative.  Notice that it is still possible to continue
   using Elixir, but not encouraged.  This is a good time to move your code
   base over to Declarative.
   
 * If the `embedded=True` field attribute is in use, this should be removed, as
   it is no longer supported.  The proposed alternative is to use the 
   :meth:`camelot.admin.object_admin.ObjectAdmin.get_compounding_objects` method
   on the admin to display multiple objects in the same form.
   