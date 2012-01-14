#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

"""wrapper around pkg_resources, with fallback to using directories specified
in the settings file if pkg_resources cannot be used.

to allow fallback to the settings file, specify the settings_attribute method,
this is the attribute in the settings file that contains the folder with the
resources as opposed to the folder containing the module itself.

this mechanism will probably be rewritten to support the loading of resources
from zip files instead of falling back to settings.

when running from a bootstrapper, we'll try to use pgk_resources, even when
runnin from within a zip file.
"""

import pkg_resources
import logging

logger = logging.getLogger('camelot.core.resources')
        
def resource_filename(module_name, filename):
    """Return the absolute path to a file in a directory
    using pkg_resources
    """
    return pkg_resources.resource_filename(module_name, filename.encode('utf-8'))

def resource_string(module_name, filename):
    """load a file as a string using pkg_resources"""
    return pkg_resources.resource_string(module_name, filename.encode('utf-8'))



