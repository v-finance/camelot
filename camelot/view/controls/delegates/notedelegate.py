from texteditdelegate import TextEditDelegate, DocumentationMetaclass
from camelot.view.controls.editors.noteeditor import NoteEditor

class NoteDelegate(TextEditDelegate):
    
    __metaclass__ = DocumentationMetaclass
    
    editor = NoteEditor
