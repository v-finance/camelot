.. _doc-models:

#################
 Creating models
#################

*Camelot* makes it easy to create views for any type of *Python* objects.  An important part of Camelot
is introspection on Python objects mapped to a database with *SQLAlchemy*.  This allows a developer to
only define his SQLAlchemy model and the views will reflect all properties defined in the model, such
as field types and relations.

.. index:: SQLALchemy

SQLAlchemy is a very powerful Object Relational Mapper (ORM) with lots of possibilities for handling
complex and large datastructures. The `SQLAlchemy website <http://www.sqlalchemy.org>`_ has extensive
documentation on all these features.

.. index:: Elixir

To facilitate the use of SQLAlchemy in less advanced use cases, like the Active Record Pattern, layers
exist on top SQLAlchemy to make those things easy and the complex things still possible.  One such
layer is *Elixir*.  Most of the code samples in the documentation make use of Elixir, an Elixir model
definition is very simple:

.. literalinclude:: ../../../../camelot/model/authentication.py
   :pyobject: GeographicBoundary
   
The code above defines the model for a `GeographicBoundary` class, a base class that will be used later
on to subclass into `Countries` and `Cities`, and is part of the default :ref:`model-persons` data
model of Camelot.  This code has some things to notice :

 * `GeographicBoundary` is a subclass of `Entity`, `Entity` is the base class for all classes that are mapped
   to the database
   
 * the `using_options` statement allows us to fine tune the ORM, in this case the `GeographicBoundary` class
   will be mapped to the `geographic_boundary` table
   
 * The `Field` statement add fields of a certain type, in this case `Unicode`, to the `GeographicBoundary` class
   as well as to the `geographic_boundary` table
   
 * The `ColumnProperty` `full_name` is a more advanced feature of the ORM, when an `GeographicBoundary` object
   is read from the database, the ORM will ask the database to concatenate the fields code and name, and
   map the result to the `full_name` attribute of the object
   
 * The `__unicode__` method is implemented, this method will be called within Camelot whenever a textual
   representation of the object is needed, eg in a window title or a many to one widget

The `Elixir website <http://elixir.ematia.de/trac/wiki/TutorialDivingIn>`_ provides a complete overview of 
the creation of models with elixir.

When a new Camelot project is created, the :ref:`camelot-admin` tool creates an empty ``models.py`` file that
can be used as a place to start the model definition.

   
.. toctree::

   fields.rst
   calculated_fields.rst
   views.rst
   under_the_hood.rst
