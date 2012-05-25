.. _under_the_hood:

==============
Under the hood
==============

A lot of things happen when a Camelot application starts up.  
In this section we give a brief overview of those which might need to be adapted for more complex applications

Setting up the ORM
==================

When the application starts up, the `setup_model` function in the `settings.py` file
is called.  In this function, all model files should be imported, to make sure the
model has been completely setup.  The importing of these files is enough to define
the mapping between objects and tables.

.. literalinclude:: ../../../../new_project/settings.py
   :pyobject: ENGINE
   
The import of these model definitions should happen before the call to `create_all` to
make sure all models are known before the tables are created.

Setting up the Database
=======================

Engine
------

The :file:`settings.py` file should contain a function named ENGINE that returns a
connection to the database.  Whenever a connection to the database is needed, this function will be called.

.. literalinclude:: ../../../../new_project/settings.py
   :pyobject: ENGINE

Metadata
--------

*SQLAlchemy* defines the :class:`MetaData` class.  A `MetaData` object contains all the information about a database schema, such
as Tables, Columns, Foreign keys, etc.  The :mod:`camelot.core.sql` contains the singleton `metadata` object which is the
default :class:`MetaData` object used by Camelot.
In the `setup_model` function, this `metadata` object is bound to the database engine.


.. literalinclude:: ../../../../new_project/settings.py
   :pyobject: setup_model
   
In case an application works with multiple database schemas in parallel, this step needs to be adapted.

Creating the tables
-------------------

By simply importing the modules which contain parts of the model definition, the needed table information
is added to the `metadata` object.  At the end of the `setup_model` function, the `create_all` method is called on the metadata, which
will create the tables in the database if they don't exist yet.

.. literalinclude:: ../../../../new_project/settings.py
   :pyobject: setup_model
   
Working without the default model
=================================

Camelot comes with a default model for Persons, Organizations, History tracking, etc.

To turn this off, simply remove the import statements of those modules from the
`setup_model` method in `settings.py`.

Transactions
============

Transactions in Camelot can be used just as in normal SQLAlchemy.  
This means that inside a :meth:`camelot.admin.action.Action.model_run` method a transaction can be started and committed ::

    model_context.session.begin()
    ...do some modifications...
    model_context.session.commit()
    
More information on the transactional behavior of the session can be found in the `SQLAlchemy documentation <http://docs.sqlalchemy.org/en/latest/orm/session.html#committing>`_

Camelot contains a method decorator (:func:`camelot.core.sql.transaction` to decorate methods on the model definition to be executed within a transaction ::

    class Person( Entity ):
 
         @transaction
         def merge_with( self, other_person ):
             ...

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

