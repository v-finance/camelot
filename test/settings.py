import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] [%(name)-35s] - %(message)s')
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def setup_model():
  import camelot.model
  from elixir import setup_all
  from camelot.model.authentication import updateLastLogin
  setup_all(create_tables=True)
  updateLastLogin()

CAMELOT_MEDIA_ROOT = 'media'

ENGINE = lambda:'sqlite:///'
