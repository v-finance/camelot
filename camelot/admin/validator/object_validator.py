#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from copy import copy
import logging
logger = logging.getLogger('camelot.admin.validator.object_validator')

from PyQt4 import QtCore

from camelot.view.fifo import Fifo
from camelot.view.model_thread import post
from camelot.core.utils import ugettext as _


class ObjectValidator(QtCore.QObject):
    """A validator class for normal python objects.  By default this validator
    declares all objects valid.  Subclass this class and overwrite it's
    objectValidity method to change it's behaviour.
    """

    validity_changed_signal = QtCore.pyqtSignal(int)

    def __init__(self, admin, model = None, initial_validation = False):
        """
        :param mode: a collection proxy the validator should inspect, or None if only the objectValidity method is going
        to get used.
        :param verifiy_initial_validity: do an inital check to see if all rows in a model are valid, defaults to False,
        since this might take a lot of time on large collections.
        """
        super(ObjectValidator, self).__init__()
        self.admin = admin
        self.model = model
        self.message_cache = Fifo(10)
        if model:
            model.dataChanged.connect( self.data_changed )
            model.layoutChanged.connect( self.layout_changed )
        self._invalid_rows = set()

        if initial_validation:
            post(self.validate_all_rows)

    def validate_all_rows(self):
        """Force validation of all rows in the model"""
        for row in range(self.model.getRowCount()):
            self.isValid(row)

    def validate_invalid_rows(self):
        for row in copy(self._invalid_rows):
            self.isValid(row)

    @QtCore.pyqtSlot()
    def layout_changed(self):
        post(self.validate_invalid_rows)

    @QtCore.pyqtSlot( QtCore.QModelIndex, QtCore.QModelIndex )
    def data_changed(self, from_index, thru_index):

        def create_validity_updater(from_row, thru_row):

            def validity_updater():
                for i in range(from_row, thru_row+1):
                    self.isValid(i)

            return validity_updater

        post(create_validity_updater(from_index.row(), thru_index.row()))

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
                #
                # If the field embeds another object, that object should be valid as well
                #
                if attributes.get('embedded', False) and attributes.get('target', False):
                    value = getattr(entity_instance, field)
                    if value:
                        target_admin = self.admin.get_related_admin(attributes['target'])
                        target_validator = target_admin.create_validator(None)
                        messages.extend( target_validator.objectValidity(value) )
                        continue
                # if the field, is nullable, don't waste time getting its value
                # @todo: check if field is a primary key instead of checking
                # whether the name is id, but this should only happen in the entity validator
                if attributes['nullable']!=True and field!='id':
                    value = getattr(entity_instance, field)
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
                        messages.append(_(u'%s is a required field') % (attributes['name']))
        logger.debug(u'messages : %s'%(u','.join(messages)))
        return messages

    def number_of_invalid_rows(self):
        """
        :return: the number of invalid rows in a model, as they have been verified
        """
        return len(self._invalid_rows)

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
        if not valid:
            if row not in self._invalid_rows:
                self._invalid_rows.add(row)
                self.validity_changed_signal.emit( row )
        elif row in self._invalid_rows:
            self._invalid_rows.remove(row)
            self.validity_changed_signal.emit( row )
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
            _('Invalid form'),
            '\n'.join(self.validityMessages(row)),
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Discard,
            parent
        )

