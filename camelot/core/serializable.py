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
        for chunk in json_encoder.iterencode(dataclasses.asdict(self)):
            stream.write(chunk.encode())
