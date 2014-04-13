.. _tutorial-startup:

################################
 Customizing the startup process
################################

The default startup process pops up a splash screen, sets up the connection to the database, loads
translations and at the end puts the main window on the screen.  An application might want to do
various things before or right after the actual main window is shown.  Such as :

 * Selecting the database to work with
 * Select the working directory of an application
 * Run a configuration wizard
 * Require the user to authenticate (by default the authentication of the OS is used)
 * Check for updates of the application or data

In this tutorial, selecting a database will be demonstrated, other customizations follow a similar pattern.

Introduction
============

The basic anatomy of a **Camelot** application is described in the :ref:`hello world tutorial <tutorial-hello-world>`.

When a Camelot application starts, it starts executing the :meth:`model_run` method of the :class:`camelot.admin.application.Application` action.
The very last thing this :meth:`model_run` method does is the creation of the main window using the :class:`camelot.view.action_steps.application.MainWindow` action step.

.. literalinclude:: ../../../../camelot/admin/action/application.py
   :pyobject: Application.model_run

So customizing the startup process boils down to customizing the application action, the inner workings of actions are descrebed in :ref:`doc-actions`.

Database profiles
=================

A database profile is all the information needed to connect to a specific database, such as server address, username and password.

Working with database profiles instead of hardcoding these settings in the application, allows end users to select the database to
which they connect, and enables system administrators to deploy the application with minimal effort.

**Camelot** has a number of modules and classes to deal with database profiles :

  * :mod:`camelot.core.profile` includes a :class:`Profile` class and :class:`ProfileStore` to store the database profiles,
    either in the Windows registry or in the Unix :file:`.settings` directory.

  * The :class:`camelot.admin.action.application_action.SelectProfile` is an action that allows the user to select a database profile,
    create a new profile, store the profiles to a file, load previously stored profiles from a file.

  * :mod:`camelot.view.action_steps.profile` has action steps used in the select profile action.
    Those steps can be reused in other parts of the application.

.. note::

   The :class:`camelot.core.profile.ProfileStore` requires the :mod:`Crypto` module to store and load profiles.
   If you are using the `Conceptive Python SDK <http://www.conceptive.be/python-sdk.html>`_, this module is already installed.