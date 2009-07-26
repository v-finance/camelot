
"""Camelot includes a number of Qt delegates, most of them are used as default
delegates for the various sqlalchemy and camelot field types.

Some delegates take specific arguments into account for their construction.
All :attr:`field_attributes` specified for a certain field will be propagated
towards the constructor of the delegate.
"""

from delegatemanager import DelegateManager
from boolcolumndelegate import BoolColumnDelegate
from codecolumndelegate import CodeColumnDelegate
from colorcolumndelegate import ColorColumnDelegate
from coloredfloatcolumndelegate import ColoredFloatColumnDelegate
from comboboxcolumndelegate import ComboBoxColumnDelegate
from datecolumndelegate import DateColumnDelegate
from datetimecolumndelegate import DateTimeColumnDelegate
from filedelegate import FileDelegate
from floatcolumndelegate import FloatColumnDelegate
from imagecolumndelegate import ImageColumnDelegate
from integercolumndelegate import IntegerColumnDelegate
from intervalscolumndelegate import IntervalsColumnDelegate
from manytomanycolumndelegate import ManyToManyColumnDelegate
from many2onecolumndelegate import Many2OneColumnDelegate
from one2manycolumndelegate import One2ManyColumnDelegate
from onetomanychoicesdelegate import OneToManyChoicesDelegate
from plaintextcolumndelegate import PlainTextColumnDelegate
from richtextcolumndelegate import RichTextColumnDelegate
from stardelegate import StarDelegate
from texteditcolumndelegate import TextEditColumnDelegate
from timecolumndelegate import TimeColumnDelegate
from virtualaddresscolumndelegate import VirtualAddressColumnDelegate
