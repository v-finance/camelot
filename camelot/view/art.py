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

"""Manages icons and artworks"""

import os
import logging
logger = logging.getLogger('camelot.view.art')

from camelot.view.model_thread import gui_function


def file_(name):
    from pkg_resources import resource_filename
    import camelot
    return resource_filename(camelot.__name__, 'art/%s'%name)

class Pixmap(object):
    """Load pixmaps from the camelot art library"""

    def __init__(self, path, module=None):
        """:param path: the path of the pixmap relative to the art directory, use
    '/' as a path separator
    :param module: the module that contains the art directory, if None is given
    this will be camelot"""
        self._path = path
        if not module:
            import camelot
            self._module_name = camelot.__name__
        else:
            self._module_name = module.__name__

    def __unicode__(self):
        return self._path

    def __repr__(self):
        return self.__class__.__name__ + "('" + self._path + "')"

    def fullpath(self):
        """Obsolete : avoid this method, since it will copy the resource file
        from its package and copy it to a temp folder if the resource is
        packaged."""
        from pkg_resources import resource_filename
        pth = resource_filename(self._module_name, 'art/%s'%(self._path))
        if os.path.exists(pth):
            return pth
        else:
            return ''

    @gui_function
    def getQPixmap(self):
        """QPixmaps can only be used in the gui thread"""
        from pkg_resources import resource_string
        from PyQt4.QtGui import QPixmap
        qpm = QPixmap()
        success = qpm.loadFromData(resource_string(self._module_name,
                                                   'art/%s'%(self._path)))
        if not success:
            msg = u'Could not load pixmap %s from camelot art library'
            logger.warn(msg % self._path)
        return qpm

class Icon(Pixmap):
    """Manages paths to the icons images"""

    @gui_function
    def getQIcon(self):
        """QPixmaps can only be used in the gui thread"""
        from PyQt4.QtGui import QIcon
        return QIcon(self.getQPixmap())
