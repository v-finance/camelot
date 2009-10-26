import settings
import logging

logger = logging.getLogger('main')

if __name__ == '__main__':
    from camelot.view.main import main
    from application_admin import MyApplicationAdmin
    main(MyApplicationAdmin())
