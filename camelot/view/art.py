#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

"""Manages icons and artworks"""

import os
import json

from ..core.qt import QtCore, QtGui, QtWidgets

import logging
logger = logging.getLogger('camelot.view.art')

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

    def __str__(self):
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
        qpm = QtGui.QPixmap()
        p = os.path.join('art', self._path)
        try:
            # For some reason this throws a unicode error if the path contains an accent (cf windows username)
            #  this happens only here, not for icons further on in the application
            #  so they see no splash screen, tant pis
            r = resource_string(self._module_name, p)
            qpm.loadFromData(r)
        except Exception as e:
            logger.warn(u'Could not load pixmap "%s" from module: %s, encountered exception' % (p, self._module_name), exc_info=e)
        self._cached_pixmap = qpm
        return qpm

class Icon(Pixmap):
    """Manages paths to the icons images"""

    def getQIcon(self):
        """QPixmaps can only be used in the gui thread"""
        return QtGui.QIcon(self.getQPixmap())


class IconFromImage(object):
    """:class:`QtGui.QImage` based icon
    
    :param image: a :class:`QtGui.QImage` object
    """
    
    def __init__(self, image):
        self.image = image
        
    def getQIcon(self):
        return QtGui.QIcon(QtGui.QPixmap.fromImage(self.image))


class FontIconEngine(QtGui.QIconEngine):

    def __init__(self):
        super().__init__()
        self.font_family = 'Font Awesome 5 Free'
        self.code = 'X'
        self.color = QtGui.QColor()

    def paint(self, painter, rect, mode, state):
        """
        :param painter: a :class:`QtGui.QPainter` object
        :param rect: a :class:`QtCore.QRect` object
        :param mode: a :class:`QtGui.QIcon.Mode` object
        :param state: a :class:`QtGui.QIcon.State` object
        """
        font = QtGui.QFont(self.font_family)
        font.setStyleStrategy(QtGui.QFont.StyleStrategy.NoFontMerging)
        drawSize = QtCore.qRound(rect.height() * 0.8)
        font.setPixelSize(drawSize)

        penColor = QtGui.QColor()
        if not self.color.isValid():
            penColor = QtWidgets.QApplication.palette("QWidget").color(QtGui.QPalette.Normal, QtGui.QPalette.ColorRole.ButtonText)
        else:
            penColor = self.color

        if mode == QtGui.QIcon.Mode.Disabled:
            penColor = QtWidgets.QApplication.palette("QWidget").color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText)

        if mode == QtGui.QIcon.Mode.Selected:
            penColor = QtWidgets.QApplication.palette("QWidget").color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.ButtonText)

        painter.save()
        painter.setPen(QtGui.QPen(penColor))
        painter.setFont(font)
        painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter, self.code)
        painter.restore()

    def pixmap(self, size, mode, state):
        """
        :param size: a :class:`QtCore.QSize` object
        :param mode: a :class:`QtGui.QIcon.Mode` object
        :param state: a :class:`QtGui.QIcon.State` object
        """
        pix = QtGui.QPixmap(size)
        pix.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pix)
        self.paint(painter, QtCore.QRect(QtCore.QPoint(0, 0), size), mode, state)
        painter.end()

        return pix


class FontIcon:

    _name_to_code = None

    def __init__(self, name, pixmap_size=32, color='#009999'):
        """
        The pixmap size is only used when calling getQPixmap().
        """
        self.name = name
        self.pixmap_size = pixmap_size
        self.color = color

        if FontIcon._name_to_code is None:
            FontIcon._load_name_to_code()

        if self.name not in FontIcon._name_to_code:
            raise Exception("Unknown font awesome icon: {}".format(self.name))

    @staticmethod
    def _load_name_to_code():
        content = read('awesome/name_to_code.json')
        FontIcon._name_to_code = json.loads(content)

    def getQIcon(self):
        # this method should not raise an exception, as it is used in slots
        engine = FontIconEngine()
        engine.font_family = 'Font Awesome 5 Free'
        engine.code = chr(int(FontIcon._name_to_code[self.name], 16))
        engine.color = QtGui.QColor(self.color)

        icon = QtGui.QIcon(engine)
        return icon

    def getQPixmap(self):
        # this method should not raise an exception, as it is used in slots
        engine = FontIconEngine()
        engine.font_family = 'Font Awesome 5 Free'
        engine.code = chr(int(FontIcon._name_to_code[self.name], 16))
        engine.color = QtGui.QColor(self.color)

        return engine.pixmap(QtCore.QSize(self.pixmap_size, self.pixmap_size), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)


class QrcIcon:
    """Icon loaded from Qt resource file"""

    def __init__(self, path):
        """
        :param: path: The Qt resource path.
        """
        self.path = path
        # Check if the resource path is valid
        #if not QtCore.QFile.exists(self.path):
        #    raise RuntimeError('Qt resource "{}" not found'.format(self.path))

    def getQIcon(self):
        return QtGui.QIcon(self.path)

    def getQPixmap(self):
        return QtGui.QPixmap(self.path)


def from_admin_icon(admin_icon):
    """Convert :class:`camelot.admin.icon.Icon` object to :class:`camelot.view.art.QrcIcon` or
    :class:`camelot.view.art.FontIcon`.

    If the name of the admin icon starts with ":/", a :class:`camelot.view.art.QrcIcon` object
    will be returned.
    """
    if admin_icon.name.startswith(':/'):
        return QrcIcon(admin_icon.name)
    else:
        return FontIcon(admin_icon.name, admin_icon.pixmap_size, admin_icon.color)


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


