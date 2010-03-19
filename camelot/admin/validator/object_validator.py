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
        from camelot.view.controls import delegates
        messages = []
        fields_and_attributes = dict(self.admin.get_columns())
        fields_and_attributes.update(dict(self.admin.get_fields()))
        for field, attributes in fields_and_attributes.items():
            # if the field was not editable, don't waste any time
            if attributes['editable']:
                value = getattr(entity_instance, field)
                #@todo: check if field is a primary key instead of checking 
                # whether the name is id, but this should only happen in the entity validator
                if attributes['nullable']!=True and field!='id':
                    logger.debug('column %s is required'%(field))
                    if 'delegate' not in attributes:
                        raise Exception('no delegate specified for %s'%(field))
                    is_null = False
                    if value==None:
                        is_null = True
                    elif (attributes['delegate'] == delegates.CodeDelegate) and \
                         (sum(len(c) for c in value) == 0):
                        is_null = True
                    elif (attributes['delegate'] == delegates.PlainTextDelegate) and (len(value) == 0):
                        is_null = True
                    elif (attributes['delegate'] == delegates.Many2OneDelegate) and (not value.id):
                        is_null = True
                    elif (attributes['delegate'] == delegates.VirtualAddressDelegate) and (not value[1]):
                        is_null = True                    
                    if is_null:
                        messages.append(u'%s is a required field' % (attributes['name']))
        logger.debug(u'messages : %s'%(u','.join(messages)))
        return messages

    def has_invalid_rows(self):
        """Verify all rows in the model
        :return: True if the model has invalid rows
        """
        for row in range(self.model.getRowCount()):
            if not self.isValid(row):
                return True
        return False
        
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
                self.message_cache.add_data(row, entity_instance, messages)
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
        from camelot.core.utils import ugettext as _
        return QtGui.QMessageBox(
            QtGui.QMessageBox.Warning,
            _('Invalid form'),
            '\n'.join(self.validityMessages(row)),
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Discard,
            parent
        )
