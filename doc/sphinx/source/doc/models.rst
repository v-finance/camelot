.. _doc-models:

#################
 Creating models
#################

*Camelot* makes it easy to create views for any type of *Python* objects.  

.. index:: SQLALchemy

SQLAlchemy is a very powerful Object Relational Mapper (ORM) with lots of possibilities for handling
simple or sophisticated datastructures. The `SQLAlchemy website <http://www.sqlalchemy.org>`_ has extensive
documentation on all these features.  An important part of Camelot is providing an easy way to
create views for objects mapped through SQLAlchemy.

SQLAlchemy comes with the *Declarative* extension to make it easy to define an ORM mapping using
the Active Record Pattern.  This is used through the documentation and in the example code.
An alternative to *Declarative* is `Elixir <http://elixir.ematia.de/trac/wiki/TutorialDivingIn>`_, 
which was used in previous *Camelot* versions, and is still supported.

To use *Declarative*, threre are some base classes that should be imported:

.. literalinclude:: /../../../camelot_example/model.py
   :start-after: begin basic imports
   :end-before: end basic imports
   
Those are :

 * :class:`camelot.core.orm.Entity` is the base class for all classes that are mapped to the database
 
 * :class:`camelot.admin.entity_admin.EntityAdmin` is the base class that describes how an `Entity` subclass should be represented in the GUI
 
 * `Column` describes a column in the database and a field in the model
 
 * `sqlalchemy.types` contains the various column types that can be used
 
Next a model can be defined:
   
.. literalinclude:: /../../../camelot_example/model.py
   :pyobject: Tag
   
The code above defines the model for a `Tag` class, an object with only a name that can be related to other
ojbects later on.  This code has some things to notice :

 * `Tag` is a subclass of :class:`camelot.core.orm.Entity`, 
   
 * the `__tablename__` class attribute allows us to specify the name of the table in the database in which
   the tags will be stored.
   
 * The `Column` statement add fields of a certain type, in this case `Unicode`, to the `Tag` class
   as well as to the `tags` table
   
 * The `__unicode__` method is implemented, this method will be called within Camelot whenever a textual
   representation of the object is needed, eg in a window title or a many to one widget.  It's good 
   practice to always implement the `__unicode__` method for all `Entity` subclasses.

When a new Camelot project is created, the :ref:`camelot-admin` tool creates an empty ``models.py`` file that
can be used as a place to start the model definition.

.. toctree::

   fields.rst
   calculated_fields.rst
   views.rst
