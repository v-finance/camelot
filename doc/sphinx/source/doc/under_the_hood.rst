.. _under_the_hood:

==============
Under the hood
==============

Setting up the model
====================

A lot of things happen under the hood when a model is defined using Elixir, and
picked up by Camelot :

Metadata
--------

Each file that contains a part of the model definition should contain these lines :

.. literalinclude:: ../../../../camelot/empty_project/model.py
   :start-after: begin meta data setup
   :end-before: end meta data setup
   
They associate the Entities defined in this file with the default metadata.  The
metadata is a datastructure that contains information about the database in which
the tables for the model will be created.

Engine
------

The settings.py file should contain a function named ENGINE that returns a
connection to the database.  This connection will be associated with the default
metadata used in the model definition.

.. literalinclude:: ../../../../camelot/empty_project/settings.py
   :pyobject: ENGINE

As such, all defined models are associated with this database.

Setup model
-----------

When the application starts up, the setup_model function in the settings.py file
is called.  In this function, all model files should be imported, to make sure the
model has been completely setup.

.. literalinclude:: ../../../../camelot/empty_project/settings.py
   :pyobject: setup_model
   
Working without the default model
=================================

Camelot comes with a default model for Persons, Organizations, History tracking, etc.

You might want to turn this off, here's how to do so :

1. In your settings.py, remove the line 'import camelot.model' and the line
   'from camelot.model.authentication import updateLastLogin', this will make sure
   no tables are created for the default Camelot model.  Tables are only created for
   the models that have been imported before the call to 'setup_all()'
  
.. literalinclude:: ../../../../camelot/empty_project/settings.py
   :pyobject: setup_model
    
2. Have a look in 'camelot/model/__init__.py' and copy the lines that do
   the initialization of the elixir session and metadata to the top of your
   own model file, imported first in the 'setup_model()' function.

.. literalinclude:: ../../../../camelot/model/__init__.py
   :start-after: begin session setup
   :end-before: end session setup

Using Camelot without the GUI
=============================

Often a Camelot application also has a non GUI part, like batch scripts, server side
scripts, etc.

It is of course perfectly possible to reuse the whole model definition in those non
GUI parts.  The easiest way to do so is to leave the Camelot GUI application as it
is and then in the non GUI script, initialize the model first ::

import settings
settings.setup_model()

From that point, all model manipulations can be done.  Access to the session can
be obtained via any Entity subclass, such as Person ::

session = Person.query.session

After the manipulations to the model have been done, they can be flushed to the db ::

session.flush()

