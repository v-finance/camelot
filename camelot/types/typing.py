from typing import Union, NewType, _GenericAlias

from camelot.core.utils import ugettext_lazy

Note = NewType('Note', Union[str, ugettext_lazy])
Directory = NewType('Directory', str)
File = NewType('File', str)
Months = NewType('Months', int)
Color = NewType('Color', str)

def is_optional_type(field_type):
    return isinstance(field_type, _GenericAlias) and \
           field_type.__origin__ == Union and \
           len(field_type.__args__) == 2 and \
           type(None) == field_type.__args__[1]