

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
from enumerationdelegate import EnumerationDelegate
from filedelegate import FileDelegate
from floatdelegate import FloatDelegate
from imagedelegate import ImageDelegate
from integerdelegate import IntegerDelegate
from intervalsdelegate import IntervalsDelegate
from manytomanydelegate import ManyToManyDelegate
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
    doc = doc + custom_delegate.__name__ + '\n' + '-'*len(custom_delegate.__name__) + '\n'
    if hasattr(custom_delegate, '__doc__') and custom_delegate.__doc__:
        doc = doc + custom_delegate.__doc__ + '\n'

__doc__ = doc
