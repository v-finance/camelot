import logging
import time

from dataclasses import field
from camelot.admin.dataclass_admin import DataclassAdmin
from camelot.core.utils import ugettext_lazy as _
from camelot.admin.icon import Icon
from camelot.admin.action.base import Action
from camelot.core.dataclasses import dataclass

LOGGER = logging.getLogger( 'camelot.admin.action.logging' )

#
# Some actions to assist the debugging process
#
@dataclass
class ChangeLoggingOptions( object ):
    
    level: int = field(default = logging.INFO, init = False)
    queries: bool = field(default = False, init = False)
    pool: bool = field(default = False, init = False)
        
    class Admin( DataclassAdmin ):
        list_display = ['level', 'queries', 'pool']
        form_display = list_display
        field_attributes = { 'level':{ 'choices':[(l,logging.getLevelName(l)) for l in [logging.DEBUG, 
                                                                                        logging.INFO, 
                                                                                        logging.WARNING,
                                                                                        logging.ERROR,
                                                                                        logging.CRITICAL]]},
                             'queries':{'tooltip': _('Log and time queries send to the database'),},
                             'pool':{ 'tooltip': _('Log database connection checkin/checkout'),}

                             }

class ChangeLogging( Action ):
    """Allow the user to change the logging configuration"""

    name = 'change_logging'
    verbose_name = _('Change logging')
    icon = Icon('wrench') # 'tango/16x16/emblems/emblem-photos.png'
    tooltip = _('Change the logging configuration of the application')

    @classmethod
    def before_cursor_execute(cls, conn, cursor, statement, parameters, context,
                              executemany):
        context._query_start_time = time.time()
        LOGGER.info("start query:\n\t%s" % statement.replace("\n", "\n\t"))
        LOGGER.info("parameters: %r" % (parameters,))

    @classmethod
    def after_cursor_execute(cls, conn, cursor, statement, parameters, context,
                             executemany):
        total = time.time() - context._query_start_time
        LOGGER.info("query Complete in %.02fms" % (total*1000))

    @classmethod
    def begin_transaction(cls, conn):
        LOGGER.info("begin transaction")

    @classmethod
    def commit_transaction(cls, conn):
        LOGGER.info("commit transaction")

    @classmethod
    def rollback_transaction(cls, conn):
        LOGGER.info("rollback transaction")

    @classmethod
    def connection_checkout(cls, dbapi_connection, connection_record, 
                            connection_proxy):
        LOGGER.info('checkout connection {0}'.format(id(dbapi_connection)))

    @classmethod
    def connection_checkin(cls, dbapi_connection, connection_record):
        LOGGER.info('checkin connection {0}'.format(id(dbapi_connection)))

    def model_run( self, model_context, mode ):
        from camelot.view import action_steps
        
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        from sqlalchemy.pool import Pool
            
        options = ChangeLoggingOptions()
        options_admin = model_context.admin.get_related_admin(ChangeLoggingOptions)
        yield action_steps.ChangeObject(options, options_admin)
        logging.getLogger().setLevel(options.level)
        if options.queries == True:
            event.listen(Engine, 'before_cursor_execute',
                         self.before_cursor_execute)
            event.listen(Engine, 'after_cursor_execute',
                         self.after_cursor_execute)
            event.listen(Engine, 'begin',
                         self.begin_transaction)
            event.listen(Engine, 'commit',
                         self.commit_transaction)
            event.listen(Engine, 'rollback',
                         self.rollback_transaction)
        if options.pool == True:
            event.listen(Pool, 'checkout',
                         self.connection_checkout)
            event.listen(Pool, 'checkin',
                         self.connection_checkin)