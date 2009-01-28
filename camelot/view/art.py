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
import settings
import logging
logger = logging.getLogger('camelot.view.art')

file_ = lambda name:os.path.join(settings.CAMELOT_ART_DIRECTORY, '%s' % name)

def validate_or_listhead(el, lst):
  if el in lst: return el
  else: return lst[0]


class TangoIcon(object):
  """Manages paths to the Tango open arts icons"""
  
  FOLDERS = ['actions', 'animations', 'apps', 'categories', 'devices'
             'emblems', 'emotes', 'mimetypes', 'places', 'status']
  
  SIZES = ['16x16', '22x22', '24x24', '32x32', 'scalable']

  TANGO_PATH = os.path.join(settings.CAMELOT_ART_DIRECTORY, 'tango')
  TANGO_FOUND = True
  if not os.path.exists(TANGO_PATH):
    TANGO_FOUND = False
    logger.warning('Tango folder not found')

  def __init__(self, name, folder='actions', size='16x16'):
    self.name = '%s.png' % name
    self.size = validate_or_listhead(size, TangoIcon.SIZES)
    self.folder = validate_or_listhead(folder, TangoIcon.FOLDERS)

  def fullpath(self):
    empty = ''
    if not TangoIcon.TANGO_FOUND: return empty
    pth = os.path.join(TangoIcon.TANGO_PATH, self.size, self.folder, self.name)
    return os.path.normpath(pth)

  def __str__(self):
    return 'TangoIcon %s' % self.name


class QTangoIcon(TangoIcon):
  """Decorates TangoIcon with PyQT4 QIcon"""

  def __init__(self, *a, **kw):
    super(QTangoIcon, self).__init__(*a, **kw)

  def getQIcon(self):
    from PyQt4.QtGui import QIcon
    return QIcon(self.fullpath())
