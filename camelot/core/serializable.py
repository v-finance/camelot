import dataclasses
import json

from .utils import ugettext_lazy

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

class DataclassEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ugettext_lazy):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


json_encoder = DataclassEncoder()

class DataclassSerializable(Serializable):
    """
    Use the dataclass info to serialize the object
    """

    def write_object(self, stream):
        for chunk in json_encoder.iterencode(dataclasses.asdict(self)):
            stream.write(chunk.encode())
