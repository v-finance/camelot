.. _views:

=====
Views
=====

Traditionally, in database land, **views** are queries defined at the database
level that act like read-only tables.  They allow reuse of common queries
across an application, and are very suitable for reporting.

Using **SQLAlchemy** this traditional approach can be used, but a more dynamic
approach is possible as well.  We can map arbitrary queries to an object,
and then visualize these objects with **Camelot**.

The model to start from
=======================

.. image:: ../_static/entityviews/table_view_visitorreport.png

In the example movie project, we can take three parts of the model : Person,
Movie and VisitorReport:

.. literalinclude:: ../../../../camelot/model/party.py
   :start-after: begin short person definition
   :end-before: end short person definition

There is a relation between Person and Movie through the director attribute:

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin short movie definition
   :end-before: end short movie definition

And a relation between Movie and VisitorReport:

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin visitor report definition
   :end-before: end visitor report definition

.. image:: ../_static/entityviews/table_view_visitorreport.png

Definition of the view
======================

Suppose, we now want to display a table with the total numbers of visitors
for all movies of a director.

We first define a plain old Python class that represents the expected results :

.. literalinclude:: ../../../../camelot_example/view.py
   :pyobject: VisitorsPerDirector

Then define a function that maps the query that calculates those results 
to the plain old Python object :

.. literalinclude:: ../../../../camelot_example/view.py
   :pyobject: setup_views

Put all this in a file called view.py

Put into action
===============

Then make sure the plain old Python object is mapped to the query, just after
the Elixir model has been setup, by modifying the setup_model function in 
settings.py:

.. literalinclude:: ../../../../camelot_example/main.py
   :pyobject: ExampleSettings.setup_model

And add the plain old Python object to a section in the **ApplicationAdmin**:

.. literalinclude:: ../../../../camelot_example/application_admin.py
   :start-after: begin sections
   :end-before: end sections

.. image:: ../_static/entityviews/table_view_visitorsperdirector.png
