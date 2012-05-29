.. _doc-delegates:

#############
  Delegates
#############

:Release: |version|
:Date: |today|

`Delegates` are a cornerstone of the Qt model/delegate/view framework.  A delegate is
used to display and edit data from a `model`.

In the Camelot framework, every field of an `Entity` has an associated delegate
that specifies how the field will be displayed and edited.  When a new form or
table is constructed, the delegates of all fields on the form or table will
construct `editors` for their fields and fill them with data from the model.
When the data has been edited in the form, the delegates will take care of
updating the model with the new data.

All Camelot delegates are subclasses of :class:`QAbstractItemDelegate`.

The `PyQT website <http://www.riverbankcomputing.com/static/Docs/PyQt4/html/classes.html>`_
provides detailed information the differenct classes involved in the 
model/delegate/view framework.

.. _specifying-delegates:

Specifying delegates
====================

The use of a specific delegate can be forced by using the ``delegate`` field
attribute.  Suppose ``rating`` is a field of type :c:type:`integer`, then it can
be forced to be visualized as stars::

  from camelot.view.controls import delegates
  
  class Movie( Entity ):
      title = Column( Unicode(50) )
      rating = Column( Integer )
  
      class Admin( EntityAdmin ):
          list_display = ['title', 'rating']
          field_attributes = {'rating':{'delegate':delegates.StarDelegate}}
	
The above code will result in:

.. image:: ../_static/editors/StarEditor_editable.png

If no `delegate` field attribute is given, a default one will be taken
depending on the sqlalchemy field type.

All available delegates can be found in :mod:`camelot.view.controls.delegates`

Available delegates
===================

.. automodule:: camelot.view.controls.delegates
   :noindex:
