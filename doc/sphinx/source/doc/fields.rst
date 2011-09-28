======
Fields
======

SQLAlchemy comes with a default set of field types that can be used. These field types will trigger the
use of certain delegates and editors to visualize them in the views.  Camelot extends those SQLAlchemy
field types with some of its own. 

An overview of field types from SQLAlchemy and Camelot is given in the table below :

.. automodule:: camelot.view.field_attributes

SQLAlchemy field types
----------------------

SQLAlchemy provides a number of field types that map to available data types in SQL, more information on those
can be found on the `SQLAlchemy website <http://www.sqlalchemy.org/docs/reference/sqlalchemy/types.html>`_ .

The types used mosed common are :

.. autoclass:: sqlalchemy.types.Boolean
   :noindex:

.. autoclass:: sqlalchemy.types.Date
   :noindex:
   
.. autoclass:: sqlalchemy.types.DateTime
   :noindex:
   
.. autoclass:: sqlalchemy.types.Float
   :noindex:
   
.. autoclass:: sqlalchemy.types.Integer
   :noindex:
   
.. autoclass:: sqlalchemy.types.Numeric
   :noindex:
   
.. autoclass:: sqlalchemy.types.Time
   :noindex:
   
.. autoclass:: sqlalchemy.types.Unicode
   :noindex:
   
Camelot field types
-------------------

.. automodule:: camelot.types
   :members:
   :noindex: