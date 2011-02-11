.. _doc-faq:

###########################
 Frequently Asked Questions
###########################

:Date: |today|

After editing a record, it suddenly moves in or disappears from the table view ?
---------------------------------------------------------------------------------

It's all about sorting.  Camelot, nor SQLAlchemy or Elixir force a default
order on the objects displayed in the table view.  This means a simple
select query will be sent to the database::

    SELECT id, first_name, last_name FROM person
    
Notice that such a query doesn't tell the database in which order to return
the rows.  Most databases will return the dataset in the order it was inserted,
but this is not required !  Postgres for example will return the rows that have
been edited last as the last rows.  Thus editing a record moves the record in the
table view.

To prevent this behavior, a default sorting can be forced upon an Entity, for example,
by its primary key::

	class Person(Entity):
		using_options(tablename='person', order_by=['id'])
