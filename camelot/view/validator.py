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

import logging
logger = logging.getLogger('camelot.view.validator')

from fifo import fifo

class Validator(object):
  """A validator class validates an entity before flushing it to the database
  and provides the user with feedback if the entity is not ready to flush
  """

  def __init__(self, admin, model):
    self.admin = admin
    self.model = model
    self.message_cache = fifo(10)

  def objectValidity(self, entity_instance):
    """@return: list of messages explaining invalid data
    empty list if object is valid
    """
    from camelot.view.controls import delegates
    messages = []
    for column in self.model.getColumns():
      value = getattr(entity_instance, column[0])
      if column[1]['nullable']!=True:
        if 'delegate' not in column[1]:
          raise Exception('no delegate specified for %s'%(column[0]))
        is_null = False
        if value==None:
          is_null = True
        elif (column[1]['delegate'] == delegates.CodeColumnDelegate) and \
             (sum(len(c) for c in value) == 0):
          is_null = True
        elif (column[1]['delegate'] == delegates.PlainTextColumnDelegate) and (len(value) == 0):
          is_null = True
        elif (column[1]['delegate'] == delegates.Many2OneColumnDelegate) and (not value.id):
          is_null = True
        if is_null:
          messages.append(u'%s is a required field' % (column[1]['name']))
    return messages

  def isValid(self, row):
    """Verify if a row in a model is 'valid' meaning it could be flushed to
    the database
    """
    messages = []
    logger.debug('is valid for row %s' % row)
    try:
      entity_instance = self.model._get_object(row)
      if entity_instance:
        messages = self.objectValidity(entity_instance)
        self.message_cache.add_data(row, entity_instance.id, messages)
    except Exception, e:
      logger.error('programming error while validating object', exc_info=e)
    return len(messages) == 0

  def validityMessages(self, row):
    try:
      return self.message_cache.get_data_at_row(row)
    except KeyError:
      raise Exception('Programming error : isValid should be called ' \
                      'before calling validityMessage')

  def validityDialog(self, row, parent):
    """Return a QDialog that asks the user to discard his changes or continue
    to edit the row until it is valid.
    """
    from PyQt4 import QtGui
    return QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                             'Invalid form',
                             '\n'.join(self.validityMessages(row)),
                             QtGui.QMessageBox.Ok | QtGui.QMessageBox.Discard,
                             parent
                             )

