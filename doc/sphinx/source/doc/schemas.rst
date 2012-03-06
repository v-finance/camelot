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
   
Upgrading from Camelot 11.12.30 to master
=========================================

There were some changes in the data model of Camelot, in the parts that track
change history and handle authentication.  Run this SQL script against your 
database to do the upgrade, after taking a backup.

On postgresql ::

    ALTER TABLE memento ADD memento_type INT;
    ALTER TABLE memento ADD COLUMN previous_attributes bytea;
    UPDATE memento SET
        memento_type = 1,
        previous_attributes = memento_update.previous_attributes
    FROM memento_update WHERE memento.id = memento_update.memento_id;
    UPDATE memento SET
        memento_type = 2,
        previous_attributes = memento_delete.previous_attributes
    FROM memento_delete WHERE memento.id = memento_delete.memento_id;
    UPDATE memento SET
        memento_type = 3
    FROM memento_create WHERE memento.id = memento_create.memento_id;
    ALTER TABLE memento ALTER COLUMN memento_type SET NOT NULL;
    ALTER TABLE memento DROP COLUMN row_type;
    DROP TABLE memento_update;
    DROP TABLE memento_delete;
    DROP TABLE memento_create;
    
Or simply drop these tables and have them recreated by Camelot and loose the
history information ::

    DROP TABLE memento_update;
    DROP TABLE memento_delete;
    DROP TABLE memento_create;
    DROP TABLE memento;
    
    
   
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

Where settings.REPOSITORY is the directory of the sqlalchemy-migrate 
repository.  For more source code, have a look at the source of 
:module:`camelot.bin.camelot_manage`.