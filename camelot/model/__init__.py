import elixir
from elixir import *
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, create_session

elixir.session = scoped_session(create_session)

import settings

metadata = MetaData()

__metadata__ = metadata

__metadata__.bind = settings.ENGINE()
__metadata__.autoflush = True
__metadata__.transactional = False