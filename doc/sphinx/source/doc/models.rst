.. _doc-models:

#################################################
 Creating models with Elixir/SQLAlchemy/Camelot
#################################################

:Release: |version|
:Date: |today|

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

Where to define the model
=========================

When a new Camelot project is created, the :ref:`camelot-admin` tool creates an empty ``models.py`` file that
can be used as a place to start the model definition.

Which field types can be used
=============================

SQLAlchemy comes with a default set of field types that can be used. These field types will trigger the
use of certain delegates and editors to visualize them in the views.  Camelot extends those SQLAlchemy
field types with some of its own. 

An overview of field types from SQLAlchemy and Camelot is given in the table below :

.. automodule:: camelot.view.field_attributes


SQLAlchemy field types
----------------------

SQLAlchemy provides a number of field types that map to available data types in SQL, more information on those
can be found on the `SQLAlchemy website <http://www.sqlalchemy.org/docs/reference/sqlalchemy/types.html>`_ .
   
Camelot field types
-------------------

.. automodule:: camelot.types
   :members:
   
Python properties as fields
===========================

Normal python properties can be used as fields on forms as well.  In that case, there
will be no introspection to find out how to display the property.  Therefore the delegate 
(:ref:`specifying-delegates`) attribute should be specified explicitly.

  .. literalinclude:: ../../../../test/snippet/properties_as_fields.py
  
Attach actions to field changes
===============================

Whenever the value of a field is changed, an action on the model can be triggered by
using properties to manipulate the field instead of manipulating it directly.  The
example below demonstrates how the value of y should be chopped when x is changed.

  .. literalinclude:: ../../../../test/snippet/fields_with_actions.py
  
  .. image:: ../_static/snippets/fields_with_actions.png

Fields calculated by the database
=================================

Having certain summary fields of your models filled by the database has the advantage
that the heavy processing is moved from the client to the server.  Moreover if the 
summary builds on information in related records, having the database build the summary
reduces the need to transfer additional data from the database to the server.

To display fields in the table and the form view that are the result of a calculation 
done by the database, a ColumnProperty needs to be defined in the Elixir model.  In this 
ColumnProperty, the sql query can be defined using SQLAlchemy statements.  Then use the 
field attributes mechanism to specify which delegate needs to be used to render the field.

.. image:: ../_static/budget.png

As an example we will create a budget with multiple budget lines, where the total budget 
is calculated by the database ::

	from elixir.properties import ColumnProperty
	from camelot.view.controls import delegates
	from sqlalchemy import sql, and_
	
	class Budget(Entity):
	  lines = OneToMany('BudgetLine')
	  total = ColumnProperty(lambda c:sql.select([sql.func.sum(BudgetLine.amount)], and_(BudgetLine.budget_id==Budget.id)))
	
	   class Admin(EntityAdmin):
	    name = 'Budgets'
	    list_display = [ 'total', 'lines']
	    field_attributes = {'total':{'delegate':delegates.FloatDelegate}} 
	
	class BudgetLine(Entity):
	  budget = ManyToOne('Budget', required=True, ondelete='cascade', onupdate='cascade')
	  amount = Field(Float(precision=2), default=0)
	
	  class Admin(EntityAdmin):
	    name = 'Budget lines'
	    list_display = ['amount',] 
	    
When the user presses F9, all data in the application is refreshed from the database, and thus
all fields are recalculated.

An explanation of the lambda function inside the ColumnProperty can be found in the ElixirColumnProperty_ and
the SqlalchemyMappers_ documentation.

.. _ElixirColumnProperty: http://elixir.ematia.de/apidocs/elixir.properties.ColumnProperty.html

.. _SqlalchemyMappers: http://www.sqlalchemy.org/docs/04/mappers.html#advdatamapping_mapper_expressions

Under the hood
==============

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
