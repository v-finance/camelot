#  ==================================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ==================================================================================
from camelot.model import metadata
from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from sqlalchemy.types import Unicode, Integer, DateTime
from elixir.ext.associable import associable
"""Functionallity to synchronize elements from the camelot database against
other databases
"""

__metadata__ = metadata

import datetime

class Synchronized( Entity ):
    using_options( tablename = 'synchronized' )
    database = Field( Unicode( 30 ), index = True )
    tablename = Field( Unicode( 30 ), index = True )
    primary_key = Field( Integer(), index = True )
    last_update = Field( DateTime(), index = True,
                          default = datetime.datetime.now,
                           onupdate = datetime.datetime.now )

is_synchronized = associable( Synchronized )
