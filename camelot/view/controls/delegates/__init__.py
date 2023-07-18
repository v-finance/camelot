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
from .delegatemanager import DelegateManager
from .booldelegate import BoolDelegate
from .colordelegate import ColorDelegate
from .comboboxdelegate import ComboBoxDelegate
from .customdelegate import CustomDelegate
from .datedelegate import DateDelegate
from .datetimedelegate import DateTimeDelegate
from .filedelegate import FileDelegate
from .floatdelegate import FloatDelegate
from .dbimagedelegate import DbImageDelegate
from .integerdelegate import IntegerDelegate
from .languagedelegate import LanguageDelegate
from .localfiledelegate import LocalFileDelegate
from .many2onedelegate import Many2OneDelegate
from .one2manydelegate import One2ManyDelegate
from .plaintextdelegate import PlainTextDelegate
from .richtextdelegate import RichTextDelegate
from .texteditdelegate import TextEditDelegate
from .virtualaddressdelegate import VirtualAddressDelegate
from .notedelegate import NoteDelegate
from .labeldelegate import LabelDelegate
from .monthsdelegate import MonthsDelegate

__all__ = [
    DelegateManager.__name__,
    BoolDelegate.__name__,
    ColorDelegate.__name__,
    ComboBoxDelegate.__name__,
    CustomDelegate.__name__,
    DateDelegate.__name__,
    DateTimeDelegate.__name__,
    FileDelegate.__name__,
    FloatDelegate.__name__,
    DbImageDelegate.__name__,
    IntegerDelegate.__name__,
    LanguageDelegate.__name__,
    LocalFileDelegate.__name__,
    Many2OneDelegate.__name__,
    One2ManyDelegate.__name__,
    PlainTextDelegate.__name__,
    RichTextDelegate.__name__,
    TextEditDelegate.__name__,
    VirtualAddressDelegate.__name__,
    NoteDelegate.__name__,
    LabelDelegate.__name__,
    MonthsDelegate.__name__,
]

doc = """Camelot includes a number of Qt delegates, most of them are used as default
delegates for the various sqlalchemy and camelot field types.

Some delegates take specific arguments into account for their construction.
All :attr:`field_attributes` specified for a certain field will be propagated
towards the constructor of the delegate.  Some of them will be used by the delegate
itself, others will be used by the editor, created by the delegate.

"""

custom_delegates = list()

def _add_subclasses(delegate):
    global custom_delegates
    subclasses = list(delegate.__subclasses__())
    for subclass in subclasses:
        _add_subclasses(subclass)
    custom_delegates += subclasses

_add_subclasses(CustomDelegate)

custom_delegates.sort(key=lambda d:d.__name__)
for custom_delegate in custom_delegates:
    doc = doc + '\n' + custom_delegate.__name__ + '\n' + '-'*len(custom_delegate.__name__) + '\n'
    if hasattr(custom_delegate, '__doc__') and custom_delegate.__doc__:
        doc = doc + custom_delegate.__doc__ + '\n'

__doc__ = doc





