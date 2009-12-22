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

"""wrapper around pkg_resources, with fallback to using directories specified
in the settings file if pkg_resources cannot be used.

to allow fallback to the settings file, specify the settings_attribute method,
this is the attribute in the settings file that contains the folder with the
resources as opposed to the folder containing the module itself.

this mechanism will probably be rewritten to support the loading of resources
from zip files instead of falling back to settings.
"""

import pkg_resources
import sys
import os
import logging

logger = logging.getLogger('camelot.core.resources')

def resource_filename(module_name, filename, settings_attribute=None):
    """Return the absolute path to a file in a directory
    if the directory for the module cannot be accessed through pkg_resources,
    fall back to the settings attribute 
    """
    import settings
    if sys.path[0].endswith('.zip'):
        # we're running from a zip file, pkg_resources won't work
        if not settings_attribute:
            logger.error('resources of module %s cannot be loaded because no settings_attribute is specified and the module is inside a zip file')
            return ''
        directory = getattr(settings, settings_attribute)
        if not os.path.exists(directory):
            logger.error('resources of module %s cannot be loaded because %s does not exist'%directory)
            return ''
        return os.path.join(directory, filename)
    else:
        return pkg_resources.resource_filename(module_name, filename)
    
def resource_string(module_name, filename, settings_attribute):
    if sys.path[0].endswith('.zip'):
        return open(resource_filename(module_name, filename, settings_attribute), 'rb').read()
    else:
        return pkg_resources.resource_string(module_name, filename)