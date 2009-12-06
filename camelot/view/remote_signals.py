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

As a messaging server, Apache active MQ was tested in combination
with the stomp library (http://docs.codehaus.org/display/STOMP/Python)
"""

import logging
import re

logger = logging.getLogger('remote_signals')

from PyQt4.QtCore import *

class SignalHandler(QObject):
    def __init__(self):
        QObject.__init__(self)
        import settings
        self.entity_update_signal = SIGNAL("entity_update")
        self.entity_delete_signal = SIGNAL("entity_delete")
        self.entity_create_signal = SIGNAL("entity_create")
        self.update_expression = re.compile(r'^/topic/Camelot.Entity.(?P<entity>.*).update$')
        if hasattr(settings, 'CAMELOT_SERVER') and settings.CAMELOT_SERVER:
            from stomp import stomp
            self.connection = stomp.Connection(host_and_ports = [ (settings.CAMELOT_SERVER, 61613) ])
            self.connection.add_listener(self)
            self.connection.start()
            logger.debug('connection to servers started')
        else:
            self.connection = None
            logger.debug('not connected to a server')
    def on_error(self, headers, message):
        logger.error('received an error %s'%message)
    def on_message(self, headers, message):
        from elixir import entities
        logger.debug('received a message %s : %s'%(str(headers),message))
        match = self.update_expression.match(headers['destination'])
        if match:
            entity = match.group('entity')
            logger.debug(' decoded as update signal for entity %s'%entity)
            self.emit(self.entity_update_signal, self, [e for e in entities if e.__name__==entity][0].get(eval(message)))
    def on_connecting(self, server):
        logger.debug('try to connect to message service')
        self.connection.connect()
    def on_connected(self, *args, **kwargs):
        logger.debug('connected to message service %s, %s'%((str(args), str(kwargs))))
        self.connection.subscribe(destination='/topic/Camelot.Entity.>', ack='auto')
    def on_disconnected(self):
        logger.debug('stomp service disconnected')
    def send_entity_update(self, sender, entity, scope='local'):
        self.sendEntityUpdate(sender, entity, scope)    
    def sendEntityUpdate(self, sender, entity, scope='local'):
        # deprecated
        self.emit(self.entity_update_signal, sender, entity)
        if self.connection and scope=='remote':
            self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.update'%entity.__class__.__name__)
    def sendEntityDelete(self, sender, entity, scope='local'):
        if self.connection and scope=='remote':
            self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.delete'%entity.__class__.__name__)
    def sendEntityCreate(self, sender, entity, scope='local'):
        if self.connection and scope=='remote':
            self.connection.send(str([entity.id]), destination='/topic/Camelot.Entity.%s.create'%entity.__class__.__name__)

_signal_handler_ = []

def construct_signal_handler(*args, **kwargs):
    _signal_handler_.append(SignalHandler(*args, **kwargs))

def get_signal_handler():
    return _signal_handler_[-1]
