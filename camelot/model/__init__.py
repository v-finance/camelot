import elixir
from elixir import *
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, create_session

elixir.session = scoped_session( create_session )

import settings

metadata = MetaData()

__metadata__ = metadata

__metadata__.bind = settings.ENGINE()
__metadata__.autoflush = False
__metadata__.transactional = False

import authentication
import fixture
import i18n
import memento
import synchronization
import type_and_status
import batch_job

__all__ = [authentication.__name__,
           fixture.__name__,
           i18n.__name__,
           memento.__name__,
           synchronization.__name__,
           type_and_status.__name__,
           batch_job.__name__,
           ]
