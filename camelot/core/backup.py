import logging

import sqlalchemy

from camelot.core.utils import ugettext as _

logger = logging.getLogger('camelot.core.backup')

class BackupMechanism(object):
    """Create a backup of the current database to an sqlite database stored in 
    filename.
    
    The backupmechanism always considers the schema of the backed up database
    as the master, and never that of the backup.  This means that when a backup
    is made, the backup file is first removed, and then filled with the tables
    from the the database to backup.  When a restore is done, the schema of the
    database is not touched, but the tables are emptied and the data from the
    backup is copied into the existing schema.
    """
    
    def __init__(self, filename):
        """Backup and restore to a local file using it as an sqlite database
        """
        self._filename = unicode(filename)
        
    def backup_table_filter(self, from_table):
        """
        Method used to filter which tables should be backed up, overwrite this method
        for taking into account specific schema issues.
        
        :from_table: the table that is considered for backup
        :return: True when the table should be backed up
        """
        return True
    
    def restore_table_filter(self, from_table):
        """
        Method used to filter which tables should be restored, overwrite this method
        for taking into account specific schema issues.  restore_table_filter is different
        from backup_table_filter, since we might want to store data in the backup that 
        should not be restored, like schema version information.
        
        :from_table: the table that is considered for backup
        :return: True when the table should be restored
        """
        return True
    
    def prepare_schema_for_restore(self, from_engine, to_engine):
        """This method will be called before the actual restore starts.  It allows bringing
        the schema at the same revision as the backed up data.
        """
        pass

    def update_schema_after_restore(self, from_engine, to_engine):
        """This method will be called after the restore has been done.  It allows bringing
        the schema at the revision the application expects.
        """
        pass
        
    def backup(self):
        """Generator function that yields tuples :
        (numer_of_steps_completed, total_number_of_steps, description_of_current_step)
        while performing a backup.
        """
        import os
        from sqlalchemy import create_engine, MetaData
        import settings
        
        yield (0, 0, _('Analyzing database structure'))
        from_engine = settings.ENGINE()
        from_meta_data = MetaData()
        from_meta_data.bind = from_engine
        from_meta_data.reflect()
                
        yield (0, 0, _('Preparing backup file'))
        logger.info("preparing backup to '%s'"%self._filename)
        if os.path.exists(self._filename):
            os.remove(self._filename)
        to_engine   = create_engine(u'sqlite:///%s'%self._filename)       
        to_meta_data = MetaData()
        to_meta_data.bind = to_engine
        #
        # Only copy tables, to prevent issues with indices and constraints
        #
        from_and_to_tables = []
        for from_table in from_meta_data.sorted_tables:
            if self.backup_table_filter(from_table):
                to_table = from_table.tometadata(to_meta_data)
                to_table.create(to_engine)
                from_and_to_tables.append((from_table, to_table))
        
        number_of_tables = len(from_and_to_tables)
        for i,(from_table, to_table) in enumerate(from_and_to_tables):
            yield (i, number_of_tables, _('Copy data of table %s')%from_table.name)
            self.copy_table_data(from_table, to_table)
        yield (number_of_tables, number_of_tables, _('Backup completed'))
    
    def restore(self):
        """Generator function that yields tuples :
        (numer_of_steps_completed, total_number_of_steps, description_of_current_step)
        while performing a restore.
        """
        import os
        from sqlalchemy import create_engine, MetaData
        import settings

        yield (0, 0, _('Open backup file'))
        if not os.path.exists(self._filename):
            raise Exception('Backup file does not exist')
        from_engine   = create_engine('sqlite:///%s'%self._filename)       

        yield (0, 0, _('Prepare database for restore'))
        to_engine = settings.ENGINE()
        self.prepare_schema_for_restore(from_engine, to_engine)
          
        yield (0, 0, _('Analyzing backup structure'))
        from_meta_data = MetaData()
        from_meta_data.bind = from_engine
        from_meta_data.reflect()
        
        yield (0, 0, _('Analyzing database structure'))     
        to_meta_data = MetaData()
        to_meta_data.bind = to_engine
        to_meta_data.reflect()
        to_tables = list(table for table in to_meta_data.sorted_tables if self.restore_table_filter(table))
        number_of_tables = len(to_tables)
        steps = number_of_tables * 2 + 2
        
        for i,to_table in enumerate(reversed(to_tables)):
            yield (i, steps, _('Delete data from table %s')%to_table.name)
            self.delete_table_data(to_table)
        
        for i,to_table in enumerate(to_tables):
            if to_table.name in from_meta_data.tables:
                yield (number_of_tables+i, steps, _('Copy data from table %s')%to_table.name)
                self.copy_table_data(from_meta_data.tables[to_table.name], to_table)
                
        yield (number_of_tables * 2 + 1, steps, _('Update schema after restore'))
        self.update_schema_after_restore(from_engine, to_engine)
        
        yield (number_of_tables * 2 + 2, steps, _('Expire current session'))
        from sqlalchemy.orm.session import _sessions
        for session in _sessions.values():
            session.expire_all()
        
        yield (1, 1, _('Restore completed'))
                          
    def delete_table_data(self, to_table):
        """This method might be subclassed to turn off/on foreign key checks"""
        to_connection = to_table.bind.connect()
        to_connection.execute(to_table.delete())
        to_connection.close()
        
    def copy_table_data(self, from_table, to_table):
        from_connection = from_table.bind.connect()
        to_connection = to_table.bind.connect()
        query = sqlalchemy.select([from_table])
        for row in from_connection.execute(query).fetchall():
            data = dict((key, getattr(row, key)) for key in row.keys())
            to_connection.execute(to_table.insert(values=data))
        from_connection.close()
        to_connection.close()