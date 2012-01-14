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

"""Camelot includes editors for various types of fields.  Each editor at least supports
these features :


 * a set_value method to set a python type as the editor's value

 * a get_value method to retrieve a python type from the editor

 * the ValueLoading state : an editor has as its value ValueLoading upon construction and
the editor's value can be set to ValueLoading if the value that should be displayed is
not yet available in the GUI thread, but is still on it's way from the model to the GUI.
This means that once set_value( ValueLoading ) is called, get_value() will always return
ValueLoading until set_value is called with another argument.

"""

from booleditor import BoolEditor, TextBoolEditor
from charteditor import ChartEditor
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
from languageeditor import LanguageEditor
from localfileeditor import LocalFileEditor
from many2oneeditor import Many2OneEditor
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
from noteeditor import NoteEditor
from labeleditor import LabelEditor
from monthseditor import MonthsEditor

__all__ = [
    BoolEditor.__name__,
    ChartEditor.__name__,
    ChoicesEditor.__name__,
    CodeEditor.__name__,
    ColoredFloatEditor.__name__,
    ColorEditor.__name__,
    CustomEditor.__name__,
    DateEditor.__name__,
    DateTimeEditor.__name__,
    EmbeddedMany2OneEditor.__name__,
    FileEditor.__name__,
    FloatEditor.__name__,
    ImageEditor.__name__,
    IntegerEditor.__name__,
    LabelEditor.__name__,
    LanguageEditor.__name__,
    LocalFileEditor.__name__,
    Many2OneEditor.__name__,
    MonthsEditor.__name__,
    NoteEditor.__name__,
    One2ManyEditor.__name__,
    OneToManyChoicesEditor.__name__,
    RichTextEditor.__name__,
    StarEditor.__name__,
    TextLineEditor.__name__,
    TimeEditor.__name__,
    VirtualAddressEditor.__name__,
    SmileyEditor.__name__,
    TextBoolEditor.__name__,
    TextEditEditor.__name__,
    WideEditor.__name__,
]


