
"""Camelot includes editors for various types of fields.  Each editor at least supports
these features :


* a set_value method to set a python type as the editor's value
* a get_value method to retrieve a python type from the editor
* the ValueLoading state : an editor has as its value ValueLoading upon construction and
the editor's value can be set to ValueLoading if the value that should be displayed is
not yet available in the GUI thread, but is still on it's way from the model to the GUI. 
"""

from customeditor import editingFinished

from booleditor import BoolEditor
from choiceseditor import ChoicesEditor
from codeeditor import CodeEditor
from coloredfloateditor import ColoredFloatEditor
from coloreditor import ColorEditor
from customeditor import CustomEditor
from dateeditor import DateEditor
from datetimeeditor import DateTimeEditor
from embeddedmany2oneeditor import EmbeddedMany2OneEditor
from fileeditor import FileEditor
from floateditor import FloatEditor
from imageeditor import ImageEditor
from integereditor import IntegerEditor
from many2oneeditor import Many2OneEditor
from manytomanyeditor import ManyToManyEditor
from one2manyeditor import One2ManyEditor
from onetomanychoiceseditor import OneToManyChoicesEditor
from richtexteditor import RichTextEditor
from stareditor import StarEditor
from textlineeditor import TextLineEditor
from timeeditor import TimeEditor
from virtualaddresseditor import VirtualAddressEditor
from smileyeditor import SmileyEditor
from textediteditor import TextEditEditor
from wideeditor import WideEditor

