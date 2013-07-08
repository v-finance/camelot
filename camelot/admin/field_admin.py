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

from sqlalchemy import schema

class FieldAdmin(schema.SchemaItem):
    """Admin class to assign specific field attributes to SQLAlchemy columns
    within the column definition ::
    
        rating = schema.Column(types.Integer(), FieldAdmin(maximum=10))

    """
    
    def __init__( self, **field_attributes ):
        self.fa = field_attributes
        
    def _set_parent(self, parent):
        setattr(parent, '_field_admin', self)

    def get_field_attributes(self):
        return self.fa
