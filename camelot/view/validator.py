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
from camelot.core.serializable import DataclassSerializable
from camelot.data.types import zip_code_types

from dataclasses import dataclass, field
from stdnum.exceptions import InvalidFormat

from .utils import date_from_string, ParsingError

data_validity = collections.namedtuple('data_validity', ['valid', 'value', 'formatted_value', 'error_msg', 'info'])

@dataclass(frozen=True)
class ValidatorState(DataclassSerializable):

    value: str = None
    formatted_value: str = None
    valid: bool = True
    error_msg: str = None
    info: dict = field(default_factory=dict)

    @classmethod
    def for_value(cls, value):
        return cls(
            value=value,
            formatted_value=value,
        )

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

@dataclass(frozen=True)
class RegexReplaceValidatorState(ValidatorState):

    regex: str = None
    regex_repl: str = None
    example: str = None
    deletechars: str = ''

    @classmethod
    def for_value(cls, value, regex=None, regex_repl=None, example=None):
        state = dict(
            value=value,
            formatted_value=value,
            valid=True,
            error_msg=None,
            regex=regex,
            regex_repl=regex_repl,
            example=example,
        )

        # First sanitize the value.
        value = cls.sanitize(value)
        formatted_value = value

        # Check if the value matches the regex.
        if value is not None and regex is not None:
            regex = re.compile(regex)
            if not regex.fullmatch(value):
                state.update(
                    valid=False,
                    error_msg=InvalidFormat.message,
                )
            else:
                # If the regex replacement pattern is defined, use it construct
                # both the compact as the formatted value:
                if cls.format_repl(regex_repl):
                    formatted_value = re.sub(regex, cls.format_repl(regex_repl), value)
                    value = re.sub(regex, cls.compact_repl(regex_repl), value)
                # If no replacement is defined, the formatted value should be identitical to the formatted one:
                else:
                    formatted_value = value

        state.update(
            value=value,
            formatted_value=formatted_value,
        )
        return cls(**state)

    @classmethod
    def sanitize(cls, value):
        """
        Sanitizes the given value by stripping the chars defined by this state's deletechars,
        and capitilizing the result. If the stripped form becomes the empty string,
        None will be returned.
        """
        if isinstance(value, str):
            return stdnum.util.clean(value, cls.deletechars).strip().upper() or None

    @classmethod
    def compact_repl(cls, regex_repl):
        if regex_repl is not None:
            if '|' in regex_repl:
                def multi_repl(m):
                    for i, repl in enumerate(regex_repl.split('|'), start=1):
                        if m.group(i) is not None:
                            return re.sub(m.re, ''.join(re.findall('\\\\\d+', repl)), m.string)
                return multi_repl
            return ''.join(re.findall('\\\\\d+', regex_repl))

    @classmethod
    def format_repl(cls, regex_repl):
        if regex_repl is not None and '|' in regex_repl:
            def multi_repl(m):
                for i, repl in enumerate(regex_repl.split('|'), start=1):
                    if m.group(i) is not None:
                        return re.sub(m.re, repl, m.string)
            return multi_repl
        return regex_repl

class RegexReplaceValidator(QtGui.QValidator, AbstractValidator):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = None

    def set_state(self, state):
        state = state or dict()
        if not isinstance(state, dict):
            state = ValidatorState.asdict(state)
        self.state = state
        # Emit changed signal as the updated state may affect the validity (and background color).
        self.changed.emit()

    def validate(self, qtext, position):
        ptext = str(qtext).upper()
        if not ptext or self.state is None:
            return (QtGui.QValidator.State.Acceptable, qtext, 0)

        regex = re.compile(self.state["regex"])
        if regex.match(ptext) is None:
            return (QtGui.QValidator.State.Intermediate, qtext, len(ptext))
        else:
            if ptext == self.state["value"]:
                formatted_value = self.state["formatted_value"]
                return (QtGui.QValidator.State.Acceptable if self.state["valid"] else QtGui.QValidator.State.Intermediate,
                        formatted_value, len(formatted_value))

            formatted_value = re.sub(regex, RegexReplaceValidatorState.format_repl(self.state["regex_repl"]), ptext)
            return (QtGui.QValidator.State.Acceptable, formatted_value, len(formatted_value))

    def format_value(self, value):
        return self.state.formatted_value

class ZipcodeValidatorState(RegexReplaceValidatorState):

    deletechars: str = ' -./#,'

    @classmethod
    def for_zip_code_type(cls, value, zip_code_type):
        state = dict()
        if zip_code_type in zip_code_types:
            zip_code_type = zip_code_types[zip_code_type]
            state.update(
                regex=zip_code_type.regex,
                regex_repl=zip_code_type.repl,
                example=zip_code_type.example,
            )
        return cls.for_value(value, **state)

    @classmethod
    def for_city(cls, city):
        if city is not None:
            return cls.for_zip_code_type(city.code, city.zip_code_type)
        return cls()

    @classmethod
    def for_addressable(cls, addressable):
        if addressable is not None:
            if addressable.city is not None:
                return cls.for_zip_code_type(addressable.zip_code, addressable.city.zip_code_type)
            return cls.for_value(addressable.zip_code)
        return cls()

    @classmethod
    def hint_for_city(cls, city):
        if (state := cls.for_city(city)) is not None and \
                (example := state.example) is not None:
            return 'e.g: {}'.format(example)

    @classmethod
    def hint_for_addressable(cls, addressable):
        if addressable is not None:
            return cls.hint_for_city(addressable.city)
