#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""
This module complements the sqlalchemy sql module, and contains the `metadata` 
variable, which is a global :class:`sqlalchemy.Metadata` object to which all 
tables of the application can be added.
"""

import logging

from sqlalchemy import event, MetaData
import sqlalchemy.sql.operators

LOGGER = logging.getLogger('camelot.core.sql')

#
# Singleton metadata object, to be used in SQLAlchemy
# setups with only a single database
#
metadata = MetaData()
metadata.autoflush = False
metadata.transactional = False

def like_op(column, string):
    return sqlalchemy.sql.operators.like_op(column, '%%%s%%'%string)

