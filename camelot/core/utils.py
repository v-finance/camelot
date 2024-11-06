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

"""Utility functions"""

import collections
import enum
import logging

from .qt import QtCore, qtranslate

logger = logging.getLogger('camelot.core.utils')

#
# Global dictionary containing all user defined translations in the
# current locale
#
_translations_ = {}

def set_translation(source, value):
    """Store a tranlation in the global translation dictionary"""
    _translations_[source] = value

def ugettext(string_to_translate, msgctxt=None):
    """Translate the string_to_translate to the language of the current locale.
    This is a two step process.  First the function will try to get the
    translation out of the Translation entity, if this is not successfull, the
    function will ask QCoreApplication to translate string_to_translate (which
    tries to get the translation from the .qm files)"""
    assert isinstance(string_to_translate, str)
    result = _translations_.get(string_to_translate, None)
    if not result:
        result = qtranslate( string_to_translate, msgctxt=msgctxt)
        #print string_to_translate, result
        # try one more time with string_to_translate capitalized
        if result is string_to_translate:
            result2 = qtranslate( string_to_translate.capitalize(), msgctxt=msgctxt)
            if result2 is not string_to_translate.capitalize():
                result = result2

    return result


class ugettext_lazy(object):
    """Like :function:`ugettext`, but delays the translation until the string
    is shown to the user.  This makes it possible for the user to translate
    the string.
    """

    def __init__(self, string_to_translate, *args, **kwargs):
        assert isinstance(string_to_translate, str)
        self._string_to_translate = string_to_translate
        self._args = args
        self._kwargs = kwargs

    def __str__(self):
        return ugettext(self._string_to_translate).format(*self._args, **self._kwargs)

    def __eq__(self, other_string):
        if isinstance(other_string, str):
            return other_string == self._string_to_translate.format(*self._args, **self._kwargs)
        if isinstance(other_string, ugettext_lazy):
            return other_string._string_to_translate == self._string_to_translate and \
                   other_string._args == self._args and other_string._kwargs == self._kwargs
        return False
    
    def __ne__(self, other_string):
        return not self.__eq__( other_string )
    
    def __repr__(self):
        return u"_('%s')"%self._string_to_translate

def format_float(value, precision=3):
    return QtCore.QString("%L1").arg(float(value), 0, 'f', precision)

arity = collections.namedtuple('arity', ('minimum', 'maximum'))

class Arity(enum.Enum):
    """
    Enum that represents the arity (e.g. number of arguments or operands) of a certain operation or function.
    To support operations with a varying arity that accept a variable number of arguments, the arity values
    are composed of a minimum and a maximum arity, with None representing a varyable value.
    """

    nullary =    arity(0, 0)
    unary =      arity(1, 1)
    binary =     arity(2, 2)
    ternary =    arity(3, 3)
    quaternary = arity(4, 4)
    quinary =    arity(5, 5)
    senary =     arity(6, 6)
    septenary =  arity(7, 7)
    octonary =   arity(8, 8)
    novenary =   arity(9, 9)
    denary =     arity(10, 10)
    multiary =   arity(2, None)

    @property
    def minimum(self):
        return self._value_.minimum

    @property
    def maximum(self):
        return self._value_.maximum
