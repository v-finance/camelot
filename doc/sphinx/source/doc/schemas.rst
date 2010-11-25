.. _doc-schemas:

#################################
 Schema Revisions and Migrations
#################################

Schema revisions and migrations is a serious issue when you develop
a application beyond a certain scale.

there is no functionallity in Camelot as such for handling this
'automagically'.

The recommended approach is to use sqlalchemy-migrate http://code.google.com/p/sqlalchemy-migrate/
It requires a bit of an effort to set it up and understand it, but once you got it up and running, 
it's well worth the effort.

There are 2 approaches, depending on the needs of your project :

Leave it all to sqlalchemy-migrate
==================================
Let sqlalchemy-migrate do a diff between your model and your db and add tables / columns 
as needed.  This is easy to implement, but not very powerfull and will fail on complex
migrations.

Camelot comes with a function that uses sqlalchemy-migrate to perform such action :

.. function:: camelot.core.sql.update_database_from_model

Call this function in the setup_model function in settings.py, right after
the setup_all function.

.. literalinclude:: ../../../../camelot/empty_project/settings.py
   :pyobject: setup_model
   
Use schema revisions
====================

Work with database revisions (takes some work to get up and
running, but very nice), you can even create database views and
update those views as well, and migrate data to the next
schema revision etc.

