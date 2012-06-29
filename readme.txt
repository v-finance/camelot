##########
 Camelot
##########

Camelot provides components for building business applications on top of **Python**, **SQLAlchemy** and **Qt**.  
It is inspired by the Django admin interface.  
A simple piece of code as this::

  class Task( Entity ):
      short_description = Column( Unicode( 60 ), nullable = False )
      due_date = Column( Date() )
      long_description = Column( RichText() )
  
      class Admin( EntityAdmin ):
          list_display = ['short_description', 'due_date']
      
Is enough to define your database schema, define the mapping between the
database and objects, and to create a user friendly desktop GUI.

Building applications with Camelot has these advantages :

  *  Use high quality editors together with the *Qt* Model-View framework
  
  *  Editors are bound to the model without writing binding code
  
  *  User friendliness and performance out of the box
  
  *  Tons of built in functions such as data import and export, printing, 
     backup and restore
     
  *  Documentation on creating the various parts of an application like wizards
     and reports

For more information, refer to :

 - `Home page <http://www.python-camelot.com>`_.
 - `Screenshots <http://www.python-camelot.com>`_.
 - `Documentation <http://www.python-camelot.com/docs.html>`_.
