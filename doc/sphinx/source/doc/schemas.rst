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

A possible scenario is to create a :meth:`migrate_model` method.  This
:meth:`migrate_model` needs to be called inside the :meth:`setup_model` of
settings.py before anything else happens::

    def controlled_schema(engine):
        """Get or create a ControlledSchema for an engine"""
        import settings
        from migrate.versioning.schema import ControlledSchema
        from migrate import exceptions
        try:
            schema = ControlledSchema.create(engine, 
                                             settings.REPOSITORY, 
                                             0)
        except exceptions.DatabaseAlreadyControlledError:
            schema = ControlledSchema(engine, settings.REPOSITORY)
            logger.info('current database version : %s'%schema.version)
        return schema
    
    def migrate_model():
        import settings
        migrate_engine = settings.ENGINE()
        migrate_connection = migrate_engine.connect()
            
        schema = controlled_schema(migrate_engine)
            
        from migrate.versioning.repository import Repository
        repository = Repository(settings.REPOSITORY)
        logger.info('latest available version : %s'%str(repository.latest))
        version = repository.latest        
        schema.upgrade(version)
        migrate_connection.close()
