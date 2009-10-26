#  ============================================================================
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
#  ============================================================================

"""Class decorator to make all fields visualized with the Admin into read-only
fields"""

def notEditableAdmin(original_admin):
    """Turn all fields visualized with original_admin into read only fields
  :param original_admin: an implementation of ObjectAdmin

  usage ::

    class Movie(Entity):
      name = Field(Unicode(50))

      class Admin(EntityAdmin):
        list_display = ['name']

      Admin = notEditableAdmin(Admin)
    """

    class NewAdmin(original_admin):

#    def get_related_entity_admin(self, entity):
#      admin = original_admin.get_related_entity_admin(self, entity)
#      return notEditableAdmin(admin)

        def get_field_attributes(self, field_name):
            attribs = original_admin.get_field_attributes(self, field_name)
            attribs['editable'] = False
            return attribs

    return NewAdmin
