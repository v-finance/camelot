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

"""Manages icons and artworks"""

import os
import logging
logger = logging.getLogger('camelot.view.art')

from PyQt4 import QtGui

def file_(name):
    from camelot.core.resources import resource_filename
    import camelot
    return resource_filename(camelot.__name__, 'art/%s'%name)

def read(fname):
    import camelot
    from camelot.core.resources import resource_string
    return resource_string(
        camelot.__name__,
        'art/%s' % fname,
    )

class Pixmap(object):
    """Load pixmaps from the camelot art library"""

    def __init__(self, path, module=None):
        """:param path: the path of the pixmap relative to the art directory, use
    '/' as a path separator
    :param module: the module that contains the art directory, if None is given
    this will be camelot"""
        self._path = path
        self._cached_pixmap = None
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
        from camelot.core.resources import resource_filename
        pth = resource_filename(self._module_name, 'art/%s'%(self._path))
        if os.path.exists(pth):
            return pth
        else:
            return ''

    def getQPixmap(self):
        """QPixmaps can only be used in the gui thread"""
        if self._cached_pixmap:
            return self._cached_pixmap
        from camelot.core.resources import resource_string
        from PyQt4.QtGui import QPixmap
        qpm = QPixmap()
        p = os.path.join('art', self._path)
        try:
            # For some reason this throws a unicode error if the path contains an accent (cf windows username)
            #  this happens only here, not for icons further on in the application
            #  so they see no splash screen, tant pis
            r = resource_string(self._module_name, p)
            qpm.loadFromData(r)
        except Exception, e:
            logger.warn(u'Could not load pixmap "%s" from module: %s, encountered exception' % (p, self._module_name), exc_info=e)
        self._cached_pixmap = qpm
        return qpm

class Icon(Pixmap):
    """Manages paths to the icons images"""

    def getQIcon(self):
        """QPixmaps can only be used in the gui thread"""
        from PyQt4.QtGui import QIcon
        return QIcon(self.getQPixmap())

class ColorScheme(object):
    """The default color scheme for camelot, based on the Tango icon set
    see http://tango.freedesktop.org/Generic_Icon_Theme_Guidelines
    """
    yellow      = QtGui.QColor('#ffff00')
    yellow_0    = yellow
    yellow_1    = QtGui.QColor('#fce94f')
    yellow_2    = QtGui.QColor('#edd400')
    yellow_3    = QtGui.QColor('#c4a000')
    orange_1    = QtGui.QColor('#fcaf3e')
    orange_2    = QtGui.QColor('#f57900')
    orange_3    = QtGui.QColor('#cd5c00')
    brown_1     = QtGui.QColor('#e9b96e')
    brown_2     = QtGui.QColor('#c17d11')
    brown_3     = QtGui.QColor('#8f5902')
    red         = QtGui.QColor('#ff0000')
    red_0       = red
    red_1       = QtGui.QColor('#ef2929')
    red_2       = QtGui.QColor('#cc0000')
    red_3       = QtGui.QColor('#a40000')
    blue        = QtGui.QColor('#0000ff')
    blue_0      = blue
    blue_1      = QtGui.QColor('#000080')
    green       = QtGui.QColor('#00ff00')
    green_0     = green
    cyan        = QtGui.QColor('#00ffff')
    cyan_0      = cyan
    cyan_1      = QtGui.QColor('#008080')
    magenta     = QtGui.QColor('#ff00ff')
    magenta_0   = magenta
    magenta_1   = QtGui.QColor('#800080')
    pink_1      = QtGui.QColor('#f16c6c')
    pink_2      = QtGui.QColor('#f13c3c')
    aluminium_0 = QtGui.QColor('#eeeeec')
    aluminium_1 = QtGui.QColor('#d3d7cf')
    aluminium_2 = QtGui.QColor('#babdb6')
    aluminium   = aluminium_0
    grey_0      = QtGui.QColor('#eeeeee')
    grey_1      = QtGui.QColor('#cccccc')
    grey_2      = QtGui.QColor('#333333')
    grey_3      = QtGui.QColor('#666666')
    grey_4      = QtGui.QColor('#999999')
    grey        = grey_0

    VALIDATION_ERROR = red_1
    NOTIFICATION = yellow_1
    """
    for consistency with QT:
    Qt::white	3	 White (#ffffff)
    Qt::black	2	Black (#000000)
    Qt::red	7	Red (#ff0000)
    Qt::darkRed	13	Dark red (#800000)
    Qt::green	8	Green (#00ff00)
    Qt::darkGreen	14	Dark green (#008000)
    Qt::blue	9	Blue (#0000ff)
    Qt::darkBlue	15	Dark blue ()
    Qt::cyan	10	Cyan (#00ffff)
    Qt::darkCyan	16	Dark cyan (#008080)
    Qt::magenta	11	Magenta (#ff00ff)
    Qt::darkMagenta	17	Dark magenta (#800080)
    Qt::yellow	12	Yellow (#ffff00)
    Qt::darkYellow	18	Dark yellow (#808000)
    Qt::gray	5	Gray (#a0a0a4)
    Qt::darkGray	4	Dark gray (#808080)
    Qt::lightGray	6	Light gray (#c0c0c0)
    Qt::transparent	19	a transparent black value (i.e., QColor(0, 0, 0, 0))
    Qt::color0	0	0 pixel value (for bitmaps)
    Qt::color1	1	1 pixel value (for bitmaps)
    """
