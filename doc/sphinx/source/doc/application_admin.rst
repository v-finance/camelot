.. _doc-admin-application_admin:

###################
  Application Admin
###################

The application admin controls how the application behaves, it determines
the sections in the left pane, the availability of help, the about box,
the menu structure, etc.

Each Camelot application should subclass the Application Admin and overwrite
some of its methods.

.. autoclass:: camelot.admin.application_admin.ApplicationAdmin

  .. literalinclude:: ../../../../example/application_admin.py