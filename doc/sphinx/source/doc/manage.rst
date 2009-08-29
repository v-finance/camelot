.. _doc-manage:

############################
 Managing a Camelot project
############################

:Release: |version|
:Date: |today|

Once a project has been created and set up as described in the tutorial
:ref:`tutorial-videostore`, it needs to be maintained and managed over time.

.. seealso:: :ref:`doc-schemas`

Two tools exist to assist in the management of Camelot projects:
:program:`camelot_admin.py` and :program:`camelot_manage.py`.

camelot_admin.py
================

:program:`camelot_admin.py` is oriented towards the developers of the project.
It is used for the creation of projects and the creation of schema revisions.

Command line options are:

.. program:: camelot_admin.py

.. cmdoption:: -h, --help
   
   Provides a list of available commands.

.. cmdoption:: startproject project

   Starts a new project

camelot_manage.py
=================

:program:`camelot_manage.py` is oriented towards administrators of an installed
camelot project. It is used for interacting with and migration of the database
to a certain schema revision.

Available options are:

.. program:: camelot_manage.py

.. cmdoption:: console

   Launches a python console with the model all setup for interaction.

   Within the :ref:`example movie <tutorial-videostore>` project one could do
   the following to print a list of all movie titles to the screen::

     from model import Movie
     for movie in Movie.query.all():
     print movie.title
   
.. cmdoption:: db_version

.. cmdoption:: version

.. cmdoption:: upgrade

.. cmdoption:: version_control

   Put the database under version control
   
.. cmdoption:: schema_display

   Generate a graph of the database schema.  The result is stored in schema.png.  This
   option requires pydot to be installed.
   
   .. image:: ../_static/schema.png
      :width: 1000
