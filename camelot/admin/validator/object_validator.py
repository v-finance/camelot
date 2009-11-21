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
logger = logging.getLogger('camelot.admin.validator.object_validator')

from camelot.view.fifo import fifo


class ObjectValidator(object):
    """A validator class for normal python objects.  By default this validator
    declares all objects valid.  Subclass this class and overwrite it's
    objectValidity method to change it's behaviour.
    """

    def __init__(self, admin, model):
        self.admin = admin
        self.model = model
        self.message_cache = fifo(10)

    def objectValidity(self, entity_instance):
        """:return: list of messages explaining invalid data
        empty list if object is valid
        """
        return []

    def isValid(self, row):
        """Verify if a row in a model is 'valid' meaning it could be flushed to
        the database
        """
        messages = []
        logger.debug('isValid for row %s' % row)
        try:
            entity_instance = self.model._get_object(row)
            if entity_instance:
                messages = self.objectValidity(entity_instance)
                self.message_cache.add_data(row, entity_instance.id, messages)
        except Exception, e:
            logger.error(
                'programming error while validating object',
                exc_info=e
            )
        valid = (len(messages) == 0)
        logger.debug('valid : %s' % valid)
        return valid

    def validityMessages(self, row):
        try:
            return self.message_cache.get_data_at_row(row)
        except KeyError:
            raise Exception(
                'Programming error : isValid should be called '
                'before calling validityMessage'
            )

    def validityDialog(self, row, parent):
        """Return a QDialog that asks the user to discard his changes or
        continue to edit the row until it is valid.
        """
        from PyQt4 import QtGui
        return QtGui.QMessageBox(
            QtGui.QMessageBox.Warning,
            'Invalid form',
            '\n'.join(self.validityMessages(row)),
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Discard,
            parent
        )
