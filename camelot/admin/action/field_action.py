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

"""ModelContext, GuiContext and Actions that are used in the context of
editing a single field on a form or in a table.
"""

from .application_action import ApplicationActionModelContext

class FieldActionModelContext( ApplicationActionModelContext ):
    """The context for a :class:`Action` on a field.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: obj

       the object of which the field displays a field
       
    .. attribute:: field
    
       the name of the field that is being displayed
       
    """
    pass
