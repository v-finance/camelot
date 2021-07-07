#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

import logging

logger = logging.getLogger('camelot.admin.validator.object_validator')



from ...core.qt import QtCore
from camelot.core.utils import ugettext as _


class ObjectValidator(QtCore.QObject):
    """A validator class for normal python objects.  By default this validator
    declares all objects valid.  Subclass this class and overwrite it's
    `validate_object` method to change it's behaviour.
    """

    def __init__(self, admin, model = None):
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
        self._related_validators = dict()
        self._all_fields = None
        self._all_field_field_attributes = dict()

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

    def validate_object( self, obj ):
        """
        :return: list of messages explaining invalid data, an empty list if
            the object is valid
        """
        from camelot.view.controls import delegates
        messages = []
        
        persistent = self.admin.is_persistent(obj)
        dirty = self.admin.is_dirty(obj)
        
        if (not persistent) or dirty:
            #
            # initialize cached static field attributes on first use
            #
            if self._all_fields is None:
                self._all_fields = [fn for fn,_fa in self.admin.get_all_fields_and_attributes().items()]
                for field_name, static_fa in zip(self._all_fields, self.admin.get_static_field_attributes(self._all_fields)):
                    self._all_field_field_attributes[field_name] = static_fa
            #
            # get dynamic field attributes on each use
            #
            for field_name, dynamic_fa in zip(self._all_fields, self.admin.get_dynamic_field_attributes(obj, self._all_fields)):
                self._all_field_field_attributes[field_name].update(dynamic_fa)
            
            for field, attributes in self._all_field_field_attributes.items():
                # if the field was not editable, don't waste any time
                if attributes.get('editable', False):
                    # if the field, is nullable, don't waste time getting its value
                    if attributes.get('nullable', True) != True:
                        value = getattr(obj, field)
                        logger.debug('column %s is required'%(field))
                        if 'delegate' not in attributes:
                            raise Exception('no delegate specified for %s'%(field))
                        is_null = False
                        if value is None:
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


