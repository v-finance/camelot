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

In this tutorial, selecting a database will be demonstrated, other customizations follow a similar
pattern.

Introduction
============

When a Camelot application starts, it starts executing the :meth:`model_run` method of the
:class:`camelot.admin.application.Application` action. The very last thing this :meth:`model_run`
method does is the creation of the main window using the 
:class:`camelot.view.action_steps.application.MainWindow` action step.

So customizing the startup process boils down to customizing the main action, the inner workings
of actions are descrebed in :ref:`doc-actions`.

Database profiles
=================

