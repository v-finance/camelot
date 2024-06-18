import logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('database administrator')

from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.action.application import Application
from camelot.admin.action.application_action import SelectProfile
from camelot.view import action_steps
from camelot.core.profile import ProfileStore
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.view.main import main_action

from sqlalchemy import MetaData, Table, orm

# begin app admin definition

app_admin = ApplicationAdmin(name='Database Administrator',
                             author='Conceptive Engineering',
                             domain='app_admin.python-camelot.com')
# end app admin definition

# begin app definition

class DatabaseAdministrator(Application):
    """Application that alows the user to view and modify table data
    in a database"""


    def model_run(self, model_context, mode):
        yield action_steps.UpdateProgress('Start Database Administrator')
# end app definition
# begin profile selection
        profile_store = ProfileStore()
        profile = yield SelectProfile(profile_store)
# end profile selection
# begin engine creation
        engine = profile.create_engine()
# begin end engine creation
        metadata = MetaData()
        metadata.reflect(engine)
        tables = list(metadata.tables.values())
        LOGGER.info('got {0} tabes'.format(len(tables)))
        
        class TableAdmin(ObjectAdmin):
            list_display = ['description']

        table_admin = TableAdmin(model_context.admin, Table)
        while True:
            LOGGER.info('show all tables')
            selected_tables = yield action_steps.SelectObjects(table_admin, value=tables)
            for table in selected_tables:
                LOGGER.info('table {0.name} was selected'.format(table))
                
                class TableClass(object):
                    pass
                
                orm.mapper(TableClass, table)

                admin = EntityAdmin(model_context.admin, TableClass)
                #admin = model_context.admin.get_related_admin(TableClass)
                query = model_context.session.query(TableClass)
                LOGGER.info('open table view')
                yield action_steps.OpenTableView(admin, query)

# begin application start magic

if __name__=='__main__':
    db_admin = DatabaseAdministrator(app_admin)
    main_action(db_admin)
# end application start magic



