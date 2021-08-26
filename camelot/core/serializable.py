import copy

import dataclasses
import io
import json

from .utils import ugettext_lazy
from enum import Enum

class Serializable(object):
    """
    Classes implementing this interface are able to serialize their
    state to a stream.
    """

    def write_object(self, stream):
        """
        Write the state of the object to a binary stream
        """
        raise NotImplementedError()

    def read_object(self, stream):
        """
        Read the state of the object from a binary stream
        """
        state = json.load(stream)
        self.__dict__.update(state)

    def _to_bytes(self):
        """
        Helper method to serialize the object to bytes.

        The purpose of this method is to make unittesting easier, it is not
        intended for use in production code.
        """
        stream = io.BytesIO()
        self.write_object(stream)
        return stream.getvalue()

    def _to_dict(self):
        """
        Helper method to serialize the object to bytes, and deserialize it to
        a dict or list.  Notice that the generated dict through serialization
        will only contain primitive datatypes.

        The purpose of this method is to make unittesting easier, it is not
        intended for use in production code.
        """
        return json.loads(self._to_bytes())
        
class DataclassEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ugettext_lazy):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


json_encoder = DataclassEncoder()

class DataclassSerializable(Serializable):
    """
    Use the dataclass info to serialize the object
    """

    def write_object(self, stream):
        for chunk in json_encoder.iterencode(self.asdict()):
            stream.write(chunk.encode())

    def asdict(self):
        """Return the fields of a dataclass instance as a new dictionary mapping
        field names to field values.

        Example usage:

          @dataclass
          class C:
              x: int
              y: int

          c = C(1, 2)
          assert asdict(c) == {'x': 1, 'y': 2}

        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        if not dataclasses._is_dataclass_instance(self):
            raise TypeError("asdict() should be called on dataclass instances")
        return _asdict_inner(self)


def _asdict_inner(obj):
    if dataclasses._is_dataclass_instance(obj):
        if isinstance(obj, ObjectDataclassSerializable):
            return type(obj).__name__, fields_to_dict(obj)
        else:
            return fields_to_dict(obj)
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_inner(v) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)((_asdict_inner(k), _asdict_inner(v))
                          for k, v in obj.items())
    else:
        return copy.deepcopy(obj)

def fields_to_dict(obj):
    result = []
    for f in dataclasses.fields(obj):
        value = _asdict_inner(getattr(obj, f.name))
        result.append((f.name, value))
    return dict(result)

class ObjectDataclassSerializable(DataclassSerializable):
    """
    Variation on DataclassSerializable where
    """
    pass
