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
import dataclasses
import re
import stdnum.util

from camelot.core.qt import QtGui
from camelot.core.serializable import DataclassSerializable
from camelot.data.types import zip_code_types

from dataclasses import dataclass, InitVar
from sqlalchemy.ext import hybrid
from stdnum.exceptions import InvalidFormat

from .utils import date_from_string, ParsingError

@dataclass(frozen=True)
class ValidatorState(DataclassSerializable):

    value: str = None
    formatted_value: str = None
    valid: bool = True
    error_msg: str = None

    # Fields that influence how values are sanitized.
    deletechars: str = ''
    to_upper: bool = False

    # Info dictionary allowing user-defined metadata to be associated.
    # This data is meant for server-side validation usecases and therefor should not be serialized.
    info: InitVar(dict) = None

    def __post_init__(self, info):
        object.__setattr__(self, "info", info or dict())

    @hybrid.hybrid_method
    def sanitize(self, value):
        """
        Hybrid method to sanitizes the given value by stripping chars and conditionally
        converting the result to uppercase based on this state.
        If the stripped form becomes the empty string, None will be returned.
        The hybrid behaviour will result in the field defaults for deletechars and to_upper being used
        if called on the class level, and the initialized field values if called on the instance level.
        """
        if isinstance(value, str):
            value = stdnum.util.clean(value, self.deletechars).strip()
            if self.to_upper == True:
                value = value.upper()
            return value or None

    @classmethod
    def for_value(cls, value, **kwargs):
        # Use initialized state to sanitize value so that possible provided
        # sanitization kwargs are correctly accounted for.
        state = cls(**kwargs)
        value = state.sanitize(value)
        return dataclasses.replace(
            state,
            value=value,
            formatted_value=value,
        )

    @classmethod
    def for_setting(cls, key, **kwargs):
        def for_setting_proxy(proxy):
            return cls.for_value(value=getattr(proxy, key), **kwargs)
        return for_setting_proxy

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

class DateValidator(QtGui.QValidator):

    def validate(self, input_, pos):
        try:
            date_from_string(str(input_))
        except ParsingError:
            return (QtGui.QValidator.State.Intermediate, input_, pos)
        return (QtGui.QValidator.State.Acceptable, input_, pos)

@dataclass(frozen=True)
class RegexValidatorState(ValidatorState):

    regex: str = None
    regex_repl: str = None
    example: str = None

    ignore_case: bool = False
    compact: bool = True

    @classmethod
    def for_value(cls, value, **kwargs):
        # Use inherited ValidatorState behaviour, wich will sanitize the value.
        state = super().for_value(value, **kwargs)

        # Check if the value matches the regex.
        if state.value is not None and state.regex is not None:
            if not re.fullmatch(state.regex, state.value, flags=re.IGNORECASE if state.ignore_case else 0):
                state = dataclasses.replace(
                    state,
                    valid=False,
                    error_msg=InvalidFormat.message,
                )
            else:
                # If the regex replacement pattern is defined, use it to construct
                # both the compact as the formatted value:
                if state.regex_repl:
                    state = dataclasses.replace(
                        state,
                        value=re.sub(state.regex, cls.compact_repl(state.regex_repl), state.value)\
                            if state.compact == True else state.value,
                        formatted_value=re.sub(state.regex, cls.format_repl(state.regex_repl), state.value),
                    )
        return state

    @classmethod
    def for_attribute(cls, attribute, **kwargs):
        def for_obj(obj):
            if obj is not None:
                return cls.for_value(attribute.__get__(obj, None), **kwargs)
            return cls()
        return for_obj

    @staticmethod
    def compact_repl(regex_repl):
        if regex_repl is not None:
            if '|' in regex_repl:
                def multi_repl(m):
                    for i, repl in enumerate(regex_repl.split('|'), start=1):
                        if m.group(i) is not None:
                            return re.sub(m.re, ''.join(re.findall('\\\\\d+', repl)), m.string)
                return multi_repl
            return ''.join(re.findall('\\\\\d+', regex_repl))

    @staticmethod
    def format_repl(regex_repl):
        if regex_repl is not None and '|' in regex_repl:
            def multi_repl(m):
                for i, repl in enumerate(regex_repl.split('|'), start=1):
                    if m.group(i) is not None:
                        return re.sub(m.re, repl, m.string)
            return multi_repl
        return regex_repl

class RegexValidator(QtGui.QValidator, AbstractValidator):

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
        ptext = str(qtext)
        if ptext and self.state:

            # Perform sanitization based on the state's parameters.
            if self.state["deletechars"]:
                for c in self.state["deletechars"]:
                    ptext = ptext.replace(c, '')
            if self.state["to_upper"] == True:
                ptext = ptext.upper()

            # First check if the text validates the regex (if defined)
            regex = self.state["regex"]
            flags = re.IGNORECASE if self.state["ignore_case"] == True else 0
            if regex is not None and re.fullmatch(regex, ptext, flags=flags) is None:
                return (QtGui.QValidator.State.Intermediate, qtext, position)
            else:
                # If it passed the regex validation, check if the text differs from the state's last value:
                if ptext == self.state["value"]:
                    # If the value did not change, reuse the state's validation result:
                    formatted_value = self.state["formatted_value"]
                    if self.state["valid"]:
                        return (QtGui.QValidator.State.Acceptable, formatted_value, len(formatted_value))
                    return (QtGui.QValidator.State.Intermediate, formatted_value, position)

                # If the value changed, the state's validation result is invalidated, so perform the regex replace formatting
                # (if available) awaiting the validator state from being updated.
                if self.state["regex_repl"] is not None:
                    formatted_value = re.sub(regex, RegexValidatorState.format_repl(self.state["regex_repl"]), ptext)
                    return (QtGui.QValidator.State.Acceptable, formatted_value, len(formatted_value))
                return (QtGui.QValidator.State.Acceptable, ptext, position)

        return (QtGui.QValidator.State.Acceptable, qtext, 0)

# TODO: once moved to the vFinance repo, the zip_code_types can be
# refactored as identifier types and this ZipcodeValidatorState
# will become superfluous (as the IdentifierValidatorState can then be used).
@dataclass(frozen=True)
class ZipcodeValidatorState(RegexValidatorState):

    deletechars: str = ' -./#,'
    to_upper: bool = True

    @classmethod
    def for_type(cls, zip_code_type, value):
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
            return cls.for_type(city.zip_code_type, city.code)
        return cls()

    @classmethod
    def for_addressable(cls, addressable):
        if addressable is not None:
            if addressable.city is not None:
                return cls.for_type(addressable.city.zip_code_type, addressable.zip_code)
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
