#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import copy
import logging

logger = logging.getLogger('camelot.admin.validator.object_validator')

import six

from ...core.qt import QtCore
from camelot.view.model_thread import post
from camelot.core.utils import ugettext as _


class ObjectValidator(QtCore.QObject):
    """A validator class for normal python objects.  By default this validator
    declares all objects valid.  Subclass this class and overwrite it's
    `validate_object` method to change it's behaviour.
    """

    validity_changed_signal = QtCore.qt_signal(int)

    def __init__(self, admin, model = None, initial_validation = False):
        """
        :param model: a collection proxy the validator should inspect, or None
            if only the `validate_object` method is going to get used.
        :param verifiy_initial_validity: do an inital check to see if all rows
            in a model are valid, defaults to False,
            since this might take a lot of time on large collections.
        """
        super(ObjectValidator, self).__init__()
        self.admin = admin
        self.model = model
        self._invalid_rows = dict()
        self._related_validators = dict()
        self._all_fields = None
        self._all_field_field_attributes = dict()

        if initial_validation:
            post(self.validate_all_rows)

    def get_related_validator( self, cls ):
        """Get the validator for another Class
        :param cls: the `Class` for which to get the validator
        :return: an `ObjectValidator` instance
        """
        try:
            return self._related_validators[cls]
        except KeyError:
            validator = self.admin.get_related_admin( cls ).get_validator()
            self._related_validators[cls] = validator
            return validator

    def validate_all_rows(self):
        """Force validation of all rows in the model"""
        for row in range(self.model.getRowCount()):
            self.isValid(row)

    def validate_invalid_rows(self):
        for row in copy.copy(six.iterkeys(self._invalid_rows)):
            self.isValid(row)

    def validate_object( self, obj ):
        """
        :return: list of messages explaining invalid data, an empty list if
            the object is valid
        """
        from camelot.view.controls import delegates
        messages = []
        
        #
        # initialize cached static field attributes on first use
        #
        if self._all_fields is None:
            self._all_fields = [fn for fn,_fa in six.iteritems(self.admin.get_all_fields_and_attributes())]
            for field_name, static_fa in zip(self._all_fields, self.admin.get_static_field_attributes(self._all_fields)):
                self._all_field_field_attributes[field_name] = static_fa
        #
        # get dynamic field attributes on each use
        #
        for field_name, dynamic_fa in zip(self._all_fields, self.admin.get_dynamic_field_attributes(obj, self._all_fields)):
            self._all_field_field_attributes[field_name].update(dynamic_fa)
        
        for field, attributes in six.iteritems(self._all_field_field_attributes):
            # if the field was not editable, don't waste any time
            if attributes.get('editable', False):
                # if the field, is nullable, don't waste time getting its value
                if attributes.get('nullable', True) != True:
                    value = getattr(obj, field)
                    logger.debug('column %s is required'%(field))
                    if 'delegate' not in attributes:
                        raise Exception('no delegate specified for %s'%(field))
                    is_null = False
                    if value==None:
                        is_null = True
                    elif (attributes['delegate'] == delegates.CodeDelegate or issubclass(attributes['delegate'],delegates.CodeDelegate)) and \
                         (sum(len(c) for c in value) == 0):
                        is_null = True
                    elif (attributes['delegate'] == delegates.PlainTextDelegate or issubclass(attributes['delegate'],delegates.PlainTextDelegate)) and (len(value) == 0):
                        is_null = True
                    elif (attributes['delegate'] == delegates.LocalFileDelegate or issubclass(attributes['delegate'],delegates.LocalFileDelegate)) and (len(value) == 0):
                        is_null = True
                    elif (attributes['delegate'] == delegates.VirtualAddressDelegate or issubclass(attributes['delegate'],delegates.VirtualAddressDelegate)) and (not value[1]):
                        is_null = True
                    if is_null:
                        messages.append(_(u'%s is a required field') % (attributes['name']))
        if not len( messages ):
            # if the object itself is valid, dig deeper within the compounding
            # objects
            for compound_obj in self.admin.get_compounding_objects( obj ):
                related_validator = self.get_related_validator( type( compound_obj ) )
                messages.extend( related_validator.validate_object( compound_obj ) )
            logger.debug(u'messages : %s'%(u','.join(messages)))
        return messages

    def number_of_invalid_rows(self):
        """
        :return: the number of invalid rows in a model, as they have been verified
        """
        return len(self._invalid_rows)

    def get_first_invalid_row(self):
        """
        :return: the row number of the first invalid row (where the first row
            has number 0)
        """
        return min(six.iterkeys(self._invalid_rows))

    def get_messages(self, row):
        return self._invalid_rows.get(row, [])

    def isValid(self, row):
        """Verify if a row in a model is 'valid' meaning it could be flushed to
        the database
        """
        messages = []
        logger.debug('isValid for row %s' % row)
        try:
            entity_instance = self.model._get_object(row)
            if entity_instance is not None:
                messages = self.validate_object(entity_instance)
        except Exception as e:
            logger.error(
                'programming error while validating object',
                exc_info=e
            )
        valid = (len(messages) == 0)
        if not valid:
            self._invalid_rows[row] = messages
            if row not in self._invalid_rows:
                self.validity_changed_signal.emit( row )
        elif row in self._invalid_rows:
            self._invalid_rows.pop(row, None)
            self.validity_changed_signal.emit( row )
        logger.debug('valid : %s' % valid)
        return valid

