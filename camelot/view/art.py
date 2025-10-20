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

import logging

from ..core.qt import QtGui

logger = logging.getLogger(__name__)


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


