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
logger = logging.getLogger('camelot.view.validator')
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from proxy.collection_proxy import fifo
logger.setLevel(logging.DEBUG)

class Validator(QtCore.QObject):
  """A validator class validates an entity before flushing it to the database and
  provides the user with feedback if the entity is not ready to flush"""
  
  def __init__(self, admin, model):
    self.admin = admin
    self.model = model
    self.message_cache = fifo(10)
    
  def isValid(self, row):
    """Verify if a row in a model is 'valid', meaning it could be flushed to the database"""
    entity_instance = self.model._get_object(row)
    messages = []
    logger.debug('is valid for row %s'%row)
    if entity_instance:
      for column in self.model.getColumns():
        value = getattr(entity_instance, column[0])
        if column[1]['nullable']!=True:
          is_null = False
          if value==None:
            is_null = True
          elif (column[1]['widget']=='code') and (sum(len(c) for c in value)==0):
            is_null = True
          if is_null:
            messages.append(u'%s is a required field'%(column[1]['name'])) 
      self.message_cache.add_data(row, entity_instance.id, messages)
    return len(messages)==0
  
  def validityMessages(self, row):
    try:
      return self.message_cache.get_data_at_row(row)
    except KeyError:
      raise Exception('Programming error : isValid should be called before calling validityMessage')
        
  def validityMessage(self, row, parent):
    """Inform the user about the validity of the data at row, by showing a message box, this function can only
    be called if isValid has been called and is finished within the model thread"""
    messages = self.validityMessages(row)
    QtGui.QMessageBox.information(parent, u'Validation', u'\n'.join(messages))
