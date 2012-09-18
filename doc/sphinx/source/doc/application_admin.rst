.. _doc-admin-application_admin:

#############################
  Customizing the Application
#############################

The **ApplicationAdmin** controls how the application behaves, it determines
the sections in the left pane, the availability of help, the about box,
the menu structure, etc.
     
The Application Admin
=====================

Each Camelot application should subclass 
:class:`camelot.admin.application_admin.ApplicationAdmin` and overwrite some of 
its methods.

The look of the main window
---------------------------

Most of these methods are based on the concept of :ref:`doc-actions`.

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_sections`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_actions`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_toolbar_actions`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_main_menu`

Interaction with the Operating System
-------------------------------------

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_organization_name`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_organization_domain`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_name`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_version`

The look of the application
---------------------------

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_splashscreen`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_stylesheet`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_translator`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_icon`

The content of the help menu
----------------------------

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_about`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_help_url`

Default behavior of the application
-----------------------------------

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_related_admin`
  
The look of the form views
--------------------------

  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_related_toolbar_actions`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_form_actions`
  * :meth:`camelot.admin.application_admin.ApplicationAdmin.get_form_toolbar_actions`

Example
-------

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin application admin
   :end-before: end application admin

Example of a reduced application
================================

By reimplementing the default :meth:`get_sections`, :meth:`get_main_menu` and
:meth:`get_toolbar_actions`, it is possible to create a completely differently
looking Camelot application.

.. image:: /_static/controls/reduced_main_window.png

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin mini admin
   :end-before: end mini admin
