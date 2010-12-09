===========
ObjectAdmin
===========

The base type of EntityAdmin, is ObjectAdmin, which specifies most of the class attributes
that can be used to customize the interface.  

.. autoclass:: camelot.admin.object_admin.ObjectAdmin

Other Admin classes can inherit ObjectAdmin if they want to provide additional functionallity,
like introspection to set default field_attributes.

.. note::
  While EntityAdmin can only be used for classes
  that are mapped by Sqlalchemy, ObjectAdmin can be used for plain old python objects as well.
  
A typical use case of an ObjectAdmin, is to display properties of Entity classes
that return lists::

  class B(object)
    ...
    class Admin(ObjectAdmin):
      ...

  class A(Entity)
    ...
    @property
    def list_of_b(self):
        return [b1, b2, b3]

    class Admin(EntityAdmin):
      form_display = ['list_of_b']
      field_attributes = {'list_of_b': {'delegate':delegates.One2ManyDelegate,
                                        'target':B}}