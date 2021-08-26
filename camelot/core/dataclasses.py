import dataclasses
from typing import Union, NewType

from camelot.core.utils import ugettext_lazy

Note = NewType('Note', Union[str, ugettext_lazy])
Directory = NewType('Directory', str)
File = NewType('File', str)

def dataclass(cls):
    """
    Extended dataclass decorator.
    By default dataclasses are unhashable. 
    To use it in the proxy the class either has to be frozen or use an explicitly defined __hash__() method.
    """
    def __hash__(self):
        return object.__hash__(self)
    
    cls.__hash__ = __hash__
    
    return dataclasses.dataclass(cls)
