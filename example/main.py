import settings
import logging


import gc
gc.disable()

logger = logging.getLogger('videostore.main')

if __name__ == '__main__':
  from camelot.view.main import main
  from application_admin import MyApplicationAdmin
  main(MyApplicationAdmin())
