import logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('database administrator')

# begin app admin definition
from camelot.admin.application_admin import ApplicationAdmin

app_admin = ApplicationAdmin(name='Database Administrator',
                             author='Conceptive Engineering',
                             domain='app_admin.python-camelot.com')
# end app admin definition

# begin app definition
from camelot.admin.action.application import Application
from camelot.view import action_steps

class DatabaseAdministrator(Application):
    """Application that alows the user to view and modify table data
    in a database"""


    def model_run(self, model_context):
        yield action_steps.UpdateProgress('Start Database Administrator')
# end app definition
# begin profile selection
        from camelot.core.profile import ProfileStore
        from camelot.admin.action.application_action import SelectProfile
        profile_store = ProfileStore()
        profile = yield SelectProfile(profile_store)
# end profile selection
# begin engine creation
        engine = profile.create_engine()
# begin end engine creation
        from sqlalchemy import MetaData, Table, orm
        metadata = MetaData()
        metadata.reflect(engine)
        tables = list(metadata.tables.values())
        LOGGER.info('got {0} tabes'.format(len(tables)))

        from camelot.admin.object_admin import ObjectAdmin
        from camelot.view import action_steps
        
        class TableAdmin(ObjectAdmin):
            list_display = ['description']

        table_admin = TableAdmin(model_context.admin, Table)
        import wingdbstub
        while True:
            LOGGER.info('show all tables')
            selected_tables = yield action_steps.SelectObjects(table_admin, value=tables)
            for table in selected_tables:
                LOGGER.info('table {0.name} was selected'.format(table))
                
                class TableClass(object):
                    pass
                
                orm.mapper(TableClass, table)
                
                from camelot.admin.entity_admin import EntityAdmin
                admin = EntityAdmin(model_context.admin, TableClass)
                #admin = model_context.admin.get_related_admin(TableClass)
                query = model_context.session.query(TableClass)
                LOGGER.info('open table view')
                print admin.get_columns()
                yield action_steps.OpenTableView(admin, query)
        print 'exit'

# begin application start magic
from camelot.view.main import main_action

if __name__=='__main__':
    db_admin = DatabaseAdministrator(app_admin)
    main_action(db_admin)
# end application start magic



