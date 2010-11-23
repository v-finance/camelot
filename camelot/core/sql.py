#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
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
            logger.error('Unhandled exception, rolling back transaction', 
                         exc_info=e)
            session.rollback()
            raise e
        return result
    
    return decorated_function

def update_database_from_model():
    """Introspection the model and add missing columns in the database
    
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


