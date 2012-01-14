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
from delegatemanager import DelegateManager
from booldelegate import BoolDelegate, TextBoolDelegate
from chartdelegate import ChartDelegate
from codedelegate import CodeDelegate
from colordelegate import ColorDelegate
from coloredfloatdelegate import ColoredFloatDelegate
from comboboxdelegate import ComboBoxDelegate
from currencydelegate import CurrencyDelegate
from customdelegate import CustomDelegate
from datedelegate import DateDelegate
from datetimedelegate import DateTimeDelegate
from filedelegate import FileDelegate
from floatdelegate import FloatDelegate
from imagedelegate import ImageDelegate
from integerdelegate import IntegerDelegate
from intervalsdelegate import IntervalsDelegate
from languagedelegate import LanguageDelegate
from localfiledelegate import LocalFileDelegate
from many2onedelegate import Many2OneDelegate
from one2manydelegate import One2ManyDelegate
from manytoonechoicesdelegate import ManyToOneChoicesDelegate
from plaintextdelegate import PlainTextDelegate
from richtextdelegate import RichTextDelegate
from stardelegate import StarDelegate
from texteditdelegate import TextEditDelegate
from timedelegate import TimeDelegate
from virtualaddressdelegate import VirtualAddressDelegate
from smileydelegate import SmileyDelegate
from notedelegate import NoteDelegate
from labeldelegate import LabelDelegate
from monthsdelegate import MonthsDelegate

__all__ = [
    DelegateManager.__name__,
    BoolDelegate.__name__,
    TextBoolDelegate.__name__,
    ChartDelegate.__name__,
    CodeDelegate.__name__,
    ColorDelegate.__name__,
    ColoredFloatDelegate.__name__,
    ComboBoxDelegate.__name__,
    CurrencyDelegate.__name__,
    CustomDelegate.__name__,
    DateDelegate.__name__,
    DateTimeDelegate.__name__,
    FileDelegate.__name__,
    FloatDelegate.__name__,
    ImageDelegate.__name__,
    IntegerDelegate.__name__,
    IntervalsDelegate.__name__,
    LanguageDelegate.__name__,
    LocalFileDelegate.__name__,
    Many2OneDelegate.__name__,
    One2ManyDelegate.__name__,
    ManyToOneChoicesDelegate.__name__,
    PlainTextDelegate.__name__,
    RichTextDelegate.__name__,
    StarDelegate.__name__,
    TextEditDelegate.__name__,
    TimeDelegate.__name__,
    VirtualAddressDelegate.__name__,
    SmileyDelegate.__name__,
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



