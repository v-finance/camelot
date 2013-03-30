.. _doc-admin:

#################
  Admin classes
#################

The Admin classes are the classes that specify how objects should be visualized, they define the look, feel and behaviour of the Application.  
Most of the behaviour of the Admin classes can be tuned by changing their class attributes.  
This makes it easy to subclass a default Admin class and tune it to your needs.

  .. image:: ../_static/admin_classes.png
  
ObjectAdmin
===========

Camelot is able to visualize any Python object, through the use of the :class:`camelot.admin.object_admin.ObjectAdmin`
class.  However, subclasses exist that use introspection to facilitate the visualisation.

Each class that is visualized within Camelot has an associated Admin class which specifies how the object or a list of objects should be visualized.

Usually the Admin class is bound to the model class by defining it as an inner class of the model class:
  
.. literalinclude:: ../../../../camelot_example/change_rating.py
   :pyobject: Options
   
Most of the behaviour of the Admin class can be customized by changing the class attributes like `verbose_name`, `list_display` and `form_display`.

Other `Admin` classes can inherit `ObjectAdmin` if they want to provide additional functionallity, like introspection to set default field attributes.

EntityAdmin
===========

The :class:`camelot.admin.entity_admin.EntityAdmin` class is a subclass of `ObjectAdmin` that can be used to visualize objects mapped to a database using SQLAlchemy.

The `EntityAdmin` uses introspection of the model to guess the default field attributes.  
This makes the definition of an `Admin` class less verbose.

.. literalinclude:: ../../../../camelot_example/model.py
   :pyobject: Tag

The :class:`camelot.admin.entity_admin.EntityAdmin` provides some additonal attributes on top of those 
provided by :class:`camelot.admin.object_admin.ObjectAdmin`, such as `list_filter` and `list_search`

Others
======

.. toctree::

   field_attributes.rst
   validators.rst
