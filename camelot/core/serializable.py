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
        for chunk in json_encoder.iterencode(self.asdict(self)):
            stream.write(chunk.encode())
    
    @classmethod
    def asdict(cls, obj):
        if not dataclasses._is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
        return cls._asdict_inner(obj)
    
    @classmethod
    def _asdict_inner(cls, obj):
        if dataclasses._is_dataclass_instance(obj):
            if isinstance(obj, ObjectDataclassSerializable):
                return type(obj).__name__, cls.fields_to_dict(obj)
            else:
                return cls.fields_to_dict(obj)
        elif isinstance(obj, (list, tuple)):
            return type(obj)(cls._asdict_inner(v) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((cls._asdict_inner(k), cls._asdict_inner(v))
                              for k, v in obj.items())
        else:
            return copy.deepcopy(obj)
    
    @classmethod
    def fields_to_dict(cls, obj):
        result = []
        for f in dataclasses.fields(obj):
            value = cls._asdict_inner(getattr(obj, f.name))
            result.append((f.name, value))
        return dict(result)

class MetaObjectDataclassSerializable(type):

    cls_register = dict()

    def __new__(cls, clsname, bases, attrs):
        newclass = super().__new__(cls, clsname, bases, attrs)
        if clsname != 'ObjectDataclassSerializable':
            cls.cls_register[clsname] = newclass
        return newclass

    @classmethod
    def get_cls_by_name(cls, cls_name):
        return cls.cls_register.get(cls_name)

class ObjectDataclassSerializable(DataclassSerializable, metaclass=MetaObjectDataclassSerializable):
    """
    Extension of DataclassSerializable for object classes that should be able to be deserialized.
    To do so, the class name of subclassed implementations is registered by the metaclass and included in the serialization.
    When deserializing, this name can be used on the meta class to lookup the corresponding object class.
    """
    pass
