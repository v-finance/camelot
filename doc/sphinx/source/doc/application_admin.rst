.. _doc-admin-application_admin:

#############################
  Customizing the Application
#############################

The **ApplicationAdmin** controls how the application behaves, it determines
the sections in the left pane, the availability of help, the about box,
the menu structure, etc.

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin application admin
   :end-before: end application admin
     
Overview
========

Each Camelot application should subclass the **ApplicationAdmin** and overwrite
some of its methods.

.. autoclass:: camelot.admin.application_admin.ApplicationAdmin
   :members: get_sections, get_actions, get_name, get_version, get_icon, get_splashscreen, get_organization_name, get_organization_domain, get_stylesheet, get_translator, get_about, get_toolbar_actions, get_main_menu

Example of a reduced application
================================

By reimplementing the default :meth:`get_sections`, :meth:`get_main_menu` and
:meth:`get_toolbar_actions`, it is possible to create a completely differently
looking Camelot application.

.. image:: /_static/controls/reduced_main_window.png

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin mini admin
   :end-before: end mini admin

