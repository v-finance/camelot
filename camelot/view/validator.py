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

""":class:`QtGui.QValidator` subclasses to be used in the
editors or other widgets.
"""
import collections
import re
import stdnum.util

from camelot.core.qt import QtGui
from camelot.data.types import zip_code_types

from stdnum.exceptions import InvalidFormat

from .utils import date_from_string, ParsingError

data_validity = collections.namedtuple('data_validity', ['valid', 'value', 'formatted_value', 'error_msg', 'info'])

class AbstractValidator:
    """
    Validators must be default constructable.
    Validators can have a state which is set by set_state.
    """

    validators = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators[cls.__name__] = cls

    @classmethod
    def get_validator(cls, validator_type, parent=None):
        if validator_type is None:
            return None
        return cls.validators[validator_type](parent)

    def set_state(self, state):
        pass

    def format_value(self, value):
        """
        Format the given value for display.
        The value is left untouched by default.
        """
        return value

class DateValidator(QtGui.QValidator):

    def validate(self, input_, pos):
        try:
            date_from_string(str(input_))
        except ParsingError:
            return (QtGui.QValidator.State.Intermediate, input_, pos)
        return (QtGui.QValidator.State.Acceptable, input_, pos)

def sanitize_zip_code(zip_code):
    """
    Sanitizes the given zip code by stripping whitespace and delimeters,
    and capitilizing the result. If the stripped form becomes the empty string,
    None will be returned.
    """
    if isinstance(zip_code, str):
        return stdnum.util.clean(zip_code, ' -./#,').strip().upper() or None

def validate_zip_code(zip_code_type, zip_code):
    # First sanitize the zip code.
    zip_code = sanitize_zip_code(zip_code)
    formatted_zip_code = zip_code
    info = {}
    if zip_code is not None and zip_code_type in zip_code_types:
        zip_code_type = zip_code_types[zip_code_type]

        # Check if the zip code matches the zip code type's regex.
        # This is done as the regex may enforce additional constraints in some cases
        # e.g. the module validate a broader range of identifiers that is used for both legal and natural party identifiers.
        if zip_code_type.regex is not None:
            regex = re.compile(zip_code_type.regex)
            if not regex.fullmatch(zip_code):
                return data_validity(False, zip_code, zip_code, InvalidFormat.message, info)
            # If the zip code type has regex replacement patterns defined, use them construct
            # both the compact as the formatted value:
            if zip_code_type.format_repl:
                formatted_zip_code = re.sub(regex, zip_code_type.format_repl, zip_code)
                zip_code = re.sub(regex, zip_code_type.compact_repl, zip_code)
            # If no replacement is defined, the formatted zip code should be equal to the formatted one:
            else:
                formatted_zip_code = zip_code

    return data_validity(True, zip_code, formatted_zip_code, None, info)
