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

"""
Classes to connect the QT event loop with a messaging
server.  To enable multiple clients to push model updates
to each other or messages for the users.
"""

import settings
import logging

logger = logging.getLogger('response_signals')

from PyQt4.QtCore import *
  
class SignalHandler(QObject):
  def __init__(self):
    QObject.__init__(self)
    self.entity_update_signal = SIGNAL("entity_update")
    self.entity_delete_signal = SIGNAL("entity_delete")
    self.entity_create_signal = SIGNAL("entity_create")
    if hasattr(settings, 'CAMELOT_SERVER') and settings.CANTATE_SERVER:
      from stomp import stomp
      self.connection = stomp.Connection(host_and_ports = [ (settings.CAMELOT_SERVER, 61613) ])
      self.connection.add_listener(self)
      self.connection.start()
      self.connection.connect()
      self.connection.subscribe(destination='/topic/Camelot.Entity.>', ack='auto')
      logger.debug('connected to message service')
    else:
      self.connection = None
      logger.warn('not connected to a server')
  def on_error(self, headers, message):
      logger.error('received an error %s'%message)
  def on_message(self, headers, message):
      logger.debug('received a message %s : %s'%(str(headers),message))
      self.emit(self.entity_signal)
  def sendEntityUpdate(self, entity):
    if self.connection:
      self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.update'%entity.__class__.__name__)
    self.emit(self.entity_update_signal, entity.__class__, [entity.id])
  def sendEntityDelete(self, entity):
    if self.connection:
      self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.delete'%entity.__class__.__name__)
  def sendEntityCreate(self, entity):
    if self.connection:
      self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.create'%entity.__class__.__name__)        

_signal_handler_ = []
        
def construct_signal_handler(*args, **kwargs):
  _signal_handler_.append(SignalHandler(*args, **kwargs))
  
def get_signal_handler():
  return _signal_handler_[0]    