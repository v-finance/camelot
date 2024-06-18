import dataclasses
import io
import json
import base64

from camelot.core.qt import QtCore, QtGui
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
        if isinstance(obj, QtGui.QKeySequence):
            return obj.toString()
        if isinstance(obj, QtGui.QKeySequence.StandardKey):
            return QtGui.QKeySequence(obj).toString()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, QtCore.QJsonValue):
            return obj.toVariant()
        if isinstance(obj, QtGui.QImage):
            byte_array = QtCore.QByteArray()
            buffer = QtCore.QBuffer(byte_array)
            buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
            obj.save(buffer, "PNG");
            return base64.b64encode(byte_array).decode()
         # FIXME: Remove this when all classes are serializable.
         #        Currently needed to serialize some fields
         #        (e.g. RouteWithRenderHint) from SetColumns._to_dict().
        if isinstance(obj, DataclassSerializable):
            return obj.asdict(obj)
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
        """
        Custom implementation of dataclasses asdict that allows customizing the serialization of dataclasses' fields,
        which the default dataclass implementation does not allow.
        """
        if not dataclasses._is_dataclass_instance(obj):
            raise TypeError("asdict() should be called on dataclass instances")
        return cls._asdict_inner(obj)
    
    @classmethod
    def _asdict_inner(cls, obj):
        if dataclasses._is_dataclass_instance(obj):
            return type(obj).serialize_fields(obj)
        elif isinstance(obj, (list, tuple)):
            return type(obj)(cls._asdict_inner(v) for v in obj)
        elif isinstance(obj, dict):
            return type(obj)((cls._asdict_inner(k), cls._asdict_inner(v))
                              for k, v in obj.items())
        else:
            # we assube obj will be handled by DataclassEncoder.default
            return obj
    
    @classmethod
    def serialize_fields(cls, obj):
        """
        Serialize the given dataclass object's fields.
        By default this will return a dictionary with each field turned into a key-value pair of its name and its value.
        """
        result = []
        for f in dataclasses.fields(obj):
            value = cls._asdict_inner(getattr(obj, f.name))
            result.append((f.name, value))
        return dict(result)

class MetaNamedDataclassSerializable(type):

    cls_register = dict()

    def __new__(cls, clsname, bases, attrs):
        newclass = super().__new__(cls, clsname, bases, attrs)
        if clsname != 'NamedDataclassSerializable':
            cls.cls_register[clsname] = newclass
        return newclass

    @classmethod
    def get_cls_by_name(cls, cls_name):
        return cls.cls_register.get(cls_name)

class NamedDataclassSerializable(DataclassSerializable, metaclass=MetaNamedDataclassSerializable):
    """
    Extended DataclassSerializable interface for object classes that should be able to be deserialized.
    To to do so, this class provides the following strategies:
      * It extends the default dataclass fields serialization of DataclassSerializable, returning a tuple consisting of the name of the concrete class,
        and the default serialized fields data.
      * The same concrete class name is used the register each concrete class implementation on this class' metaclass.
        When deserializing, the serialized class name can then be used to lookup the corresponding registered class.
    """
    
    @classmethod
    def serialize_fields(cls, obj): 
        return type(obj).__name__, super(NamedDataclassSerializable, cls).serialize_fields(obj)
