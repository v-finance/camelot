
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

# dummy variable to prevent pycheckers warnings on unused imports
__model__ = [authentication, 
             fixture, 
             i18n, 
             memento, 
             synchronization, 
             type_and_status,
             batch_job]