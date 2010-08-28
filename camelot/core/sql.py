import logging
from functools import wraps

import sqlalchemy.sql.operators

def like_op(column, string):
    return sqlalchemy.sql.operators.like_op(column, '%%%s%%'%string)

def transaction(original_function):
    """Decorator for methods on an entity, to make them transactional"""

    logger = logging.getLogger('camelot.core.sql.transaction')
    
    @wraps( original_function )
    def decorated_function(cls, *args, **kwargs):
        session = cls.query.session
        session.begin()
        try:
            result = original_function(cls, *args, **kwargs)
            session.commit()
        except Exception, e:
            logger.error('Unhandled exception, rolling back transaction', exc_info=e)
            session.rollback()
            raise e
        return result
    
    return decorated_function

def update_database_from_model():
    """Do some introspection on the model and add missing columns in the database
    
    this function can be ran in setup_model after setup_all(create_tables=True)
    """
    import settings
    migrate_engine = settings.ENGINE()
    migrate_connection = migrate_engine.connect()
    
    from camelot.model import metadata
    from migrate.versioning.schemadiff import SchemaDiff
    from migrate.changeset import create_column
    schema_diff = SchemaDiff(metadata, migrate_connection)
    
    for table_with_diff in schema_diff.tablesWithDiff:
        missingInDatabase, _missingInModel, _diffDecl = schema_diff.colDiffs[table_with_diff.name]
        for col in missingInDatabase:
            create_column(col, table_with_diff)

