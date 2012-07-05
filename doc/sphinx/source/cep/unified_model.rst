.. _cep-unified-model:

##########################
 Unified Model Definition
##########################

status : draft

.. note::
   This Camelot enhancement proposal is a work in progress and implementation
   has not started.

Introduction
============

When Camelot is used to display objects that are mapped to the database through SQLAlchemy, Camelot uses introspection to create default views.

When displaying objects that are not mapped to the database, such introspection is not possible.
This often leads to a rather verbose definition of the model and the view ::

    class Task( object ):

        def __init__( self ):
            self.description = ''
            self.creation_date = datetime.date.today()

        class Admin( ObjectAdmin ):
            list_display = ['description', 'due_date']
            field_attributes = { 'description': {'delegate':delegates.TextLineDelegate,
                                                 'editable':True},
                                 'due_date': {'delegate':delegates.DateDelegate,
                                              'editable':True}, }

This proposal aims to find a way to create a less descriptive way to define model and view in the case of simple Python objects.

Summary
=======

Fields on objects can be defined in a uniform way wether they are mapped to the database or not.  
The definition of the unmapped `Task` class would be ::

    class Task( object ):
        description = Field( unicode, default = 0 )
        due_date = Field( datetime.date, default = 0 )
        
While the definition of the mapped `Task` class would be ::

    class Task( Entity ):
        description = Field( sqlalchemy.types.Unicode, default = 0 )
        due_date = Field( sqlalchemy.types.Date, default = 0 )
        
Both definitions should be enough for Camelot to create a view and make the object usable in the model.
        
Fields
======

Default views
=============

Field attributes
================

Relations
=========
