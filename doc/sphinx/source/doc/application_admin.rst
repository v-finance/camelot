.. _doc-admin-application_admin:

#############################
  Customizing the Application
#############################

The **ApplicationAdmin** controls how the application behaves, it determines
the sections in the left pane, the availability of help, the about box,
the menu structure, etc.

  .. literalinclude:: ../../../../camelot_example/application_admin.py

Each Camelot application should subclass the **ApplicationAdmin** and overwrite
some of its methods.

.. autoclass:: camelot.admin.application_admin.ApplicationAdmin
   :members: get_sections, get_actions, get_name, get_version, get_icon, get_splashscreen, get_organization_name, get_organization_domain, get_stylesheet, get_translator, get_about

