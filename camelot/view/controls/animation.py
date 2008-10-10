#  ==================================================================================
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
#  ==================================================================================

import logging

logger = logging.getLogger('animation')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view import art

class MovieWidget(QtGui.QLabel):
  """Simulates a QMovie using a QLabel"""

  def __init__(self, icons, parent=None):
    logger.debug('creating movie widget')
    super(MovieWidget, self).__init__(parent)
    self.current_frame = 0
    self.last_frame = len(icons) - 1
    self.pixmaps = self._create_pixmaps(icons)
    self.started = False

  def _create_pixmaps(self, icons):
    result = []
    for ic in icons:
      px = QtGui.QPixmap(ic)
      # scale to 16 x 16
      #px = px.scaled(16, 16, Qt.KeepAspectRatio)
      result.append(px)
    return result

  def startMovie(self):
    logger.debug('movie started')
    if self.started:
      return
    self.timerId = self.startTimer(80) # 80 milliseconds
    self.started = True

  def stopMovie(self):
    logger.debug('movie stopped')
    if self.started:
      self.killTimer(self.timerId)
      self.started = False

  def timerEvent(self, event):
    #logger.debug('changing movie frame')
    self.setPixmap(self.pixmaps[self.current_frame])
    self.current_frame += 1
    if self.current_frame > self.last_frame:
      self.current_frame = 0

class Throbber(MovieWidget):
  """Spinning widget subclassing MovieWidget"""
  
  def __init__(self, parent):
    logger.debug('creating throbber')

    icons = [art.file_('Throbber-small-anim1.png'), 
             art.file_('Throbber-small-anim2.png'),
             art.file_('Throbber-small-anim3.png'),
             art.file_('Throbber-small-anim4.png'),
             art.file_('Throbber-small-anim5.png'),
             art.file_('Throbber-small-anim6.png'),
             art.file_('Throbber-small-anim7.png'),
             art.file_('Throbber-small-anim8.png')]

    super(Throbber, self).__init__(icons, parent)
    
    self.idle_pixmap = QtGui.QPixmap(art.file_('Throbber-small.png'))
    self._idle_state()
    parent.resize(parent.size())

  def _idle_state(self):
    self.setPixmap(self.idle_pixmap)

  def process_working(self):
    logger.debug('Process is working')
    self.startMovie()

  def process_idle(self):
    logger.debug('Process is idle')
    self.stopMovie()
    self._idle_state()

