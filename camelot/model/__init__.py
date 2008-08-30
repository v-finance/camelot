from elixir import *
from sqlalchemy import *
import settings

metadata = MetaData()

__metadata__ = metadata

__metadata__.bind = settings.ENGINE()
__metadata__.autoflush = True
__metadata__.transactional = False