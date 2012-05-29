.. _calculated_fields:

=================
Calculated Fields
=================

To display fields in forms that are not stored into the database but, are
calculated at run time, two main options exist.  Either those fields are
calculated within python or they are calculated by Python.  Normal Python
properties can be used to do the calculation in Python, whereas ColumnProperties
can be used to do the logic in the database.

Python properties as fields
===========================

Normal python properties can be used as fields on forms as well.  In that case, there
will be no introspection to find out how to display the property.  Therefore the delegate 
(:ref:`specifying-delegates`) attribute should be specified explicitly.

  .. literalinclude:: ../../../../test/snippet/properties_as_fields.py

By default, python properties are read-only.  They have to be set to editable through
the field attributes to make them writeable by the user.

Properties are also used to summarize information from multiple attributes and
put them in a single field.
  
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
done by the database, a `column_property` needs to be defined in the Declarative model.  In this 
`column_property`, the sql query can be defined using SQLAlchemy statements.  In this example, the `Movie` class gains the
`total_visitors` attribute which contains the sum of all visitors that went to a movie.

.. literalinclude:: ../../../../camelot_example/model.py
   :start-after: begin column_property
   :end-before: end column_property

It's important to notice that the value of this field is calculated when the object is fetched from the database. When the user presses F9, 
all data in the application is refreshed from the database, and thus all column properties are recalculated.
