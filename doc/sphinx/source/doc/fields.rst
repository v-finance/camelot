============
Column types
============

SQLAlchemy comes with a set of column types that can be used. These column types will trigger the
use of a certain :class:`QtGui.QDelegate` to visualize them in the views.  Camelot extends those SQLAlchemy
field types with some of its own. 

An overview of field types from SQLAlchemy and Camelot is given in the table below :

.. automodule:: camelot.view.field_attributes

All SQLAlchemy field types can be found in the :mod:`sqlalchemy:sqlalchemy.types` module.
All additional Camelot field types can be found in the :mod:`camelot.types` module.

