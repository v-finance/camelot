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

from .booleditor import BoolEditor
from .choiceseditor import ChoicesEditor
from .coloreditor import ColorEditor
from .customeditor import CustomEditor
from .dateeditor import DateEditor
from .fileeditor import FileEditor
from .floateditor import FloatEditor
from .dbimageeditor import DbImageEditor
from .integereditor import IntegerEditor
from .languageeditor import LanguageEditor
from .localfileeditor import LocalFileEditor
from .many2oneeditor import Many2OneEditor
from .one2manyeditor import One2ManyEditor
from .richtexteditor import RichTextEditor
from .textlineeditor import TextLineEditor
from .virtualaddresseditor import VirtualAddressEditor
from .textediteditor import TextEditEditor
from .wideeditor import WideEditor
from .noteeditor import NoteEditor
from .labeleditor import LabelEditor
from .monthseditor import MonthsEditor

__all__ = [
    BoolEditor.__name__,
    ChoicesEditor.__name__,
    ColorEditor.__name__,
    CustomEditor.__name__,
    DateEditor.__name__,
    FileEditor.__name__,
    FloatEditor.__name__,
    DbImageEditor.__name__,
    IntegerEditor.__name__,
    LabelEditor.__name__,
    LanguageEditor.__name__,
    LocalFileEditor.__name__,
    Many2OneEditor.__name__,
    MonthsEditor.__name__,
    NoteEditor.__name__,
    One2ManyEditor.__name__,
    RichTextEditor.__name__,
    TextLineEditor.__name__,
    VirtualAddressEditor.__name__,
    TextEditEditor.__name__,
    WideEditor.__name__,
]




