#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

# begin session setup
import elixir

from sqlalchemy import MetaData

from sqlalchemy.orm import scoped_session, create_session

elixir.session = scoped_session( create_session )

from camelot.core.conf import settings

metadata = MetaData()

__metadata__ = metadata

__metadata__.bind = settings.ENGINE()
__metadata__.autoflush = False
__metadata__.transactional = False

# end session setup

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

