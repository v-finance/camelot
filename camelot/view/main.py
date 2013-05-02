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

"""Main function, to be called to start the GUI interface"""

from camelot.art import resources # Required for tooltip visualization
resources.__name__ # Dodge PyFlakes' attack

from ..admin.action.application import Application

def main(application_admin):
    """shortcut main function, call this function to start the GUI interface 
    with minimal hassle and without the need to construct a 
    :class:`camelot.admin.action.application.Application` object.  
    
    If you need to customize the initialization process, construct an 
    `Application` subclass and call its `gui_run` method to start the 
    application.

    :param application_admin: a :class:`camelot.admin.application_admin.ApplicationAdmin` object
        that specifies the look of the GUI interface
    """
    app = Application(application_admin)
    app.gui_run()
