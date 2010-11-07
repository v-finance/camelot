import settings
import logging

logger = logging.getLogger('videostore.main')

try:
    import matplotlib
except:
    logger.error('Charts will not work because of missing matplotlib')

if __name__ == '__main__':
    from camelot.view.main import main
    from application_admin import MyApplicationAdmin
    main(MyApplicationAdmin())
