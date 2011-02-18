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
is calculated by the database::

  from elixir.properties import ColumnProperty
  from camelot.view.controls import delegates
  from sqlalchemy import sql, and_
	
  class Budget(Entity):
      lines = OneToMany('BudgetLine')
        
      @ColumnProperty
      def total(self):
          return sql.select([sql.func.sum(BudgetLine.amount)], 
                            and_(BudgetLine.budget_id==self.id))
	
      class Admin(EntityAdmin):
          verbose_name = 'Budgets'
          list_display = [ 'total', 'lines']
          field_attributes = {'total':{'delegate':delegates.FloatDelegate}} 

  class BudgetLine(Entity):
       budget = ManyToOne('Budget', required=True, ondelete='cascade', onupdate='cascade')
       amount = Field(Float(precision=2), default=0)
	
       class Admin(EntityAdmin):
           verbose_name = 'Budget lines'
           list_display = ['amount',] 
	    
When the user presses F9, all data in the application is refreshed from the database, and thus
all fields are recalculated.

An explanation of the lambda function inside the ColumnProperty can be found in the ElixirColumnProperty_ and
the SqlalchemyMappers_ documentation.

.. _ElixirColumnProperty: http://elixir.ematia.de/apidocs/elixir.properties.ColumnProperty.html

.. _SqlalchemyMappers: http://www.sqlalchemy.org/docs/04/mappers.html#advdatamapping_mapper_expressions
