import collections
from sqlalchemy import util

from camelot.core.utils import ugettext_lazy
from camelot.admin.action import Mode

class Types(util.OrderedProperties):
    """
    A collection of types with a unique id and name.

    This class pretends some compatibility with the python 3 Enum class by
    having a __members__ attribute.
    """

    instances = []

    def __init__(self, *args, literal=False, verbose=False, fields_to_translate=['name']):
        """
        Each argument passed to the constructor should be a feature type.

        :param fields_to_translate: list of fields of which the values should be translated.
        :param verbose: if True, the explicit 'verbose_name' field of each type is used as its verbose representation.
        When False, the name of each type is used, possibly converted depending on the literal flag.
        :param literal: flag that indicates if the name field of each type should be uses as is/converted as a translation key.
        """
        super(Types, self).__init__()
        for f in args:
            assert f.name not in self, 'Duplicate types defined with name {}'.format(f.name)
            if hasattr(f, 'id'):
                assert f.id not in [t.id for t in self], 'Duplicate types defined with id {}'.format(f.id)
            self[f.name] = f
        Types.instances.append(self)
        object.__setattr__(self, '__literal__', literal)
        object.__setattr__(self, '__verbose__', verbose)
        object.__setattr__(self, '__fields_to_translate__', fields_to_translate)

    @property
    def __kwargs__(self):
        return dict(literal=self.__literal__, verbose=self.__verbose__, fields_to_translate=self.__fields_to_translate__)

    @property
    def __members__(self):
        return self._data

    def get_translation_keys(self, name):
        type_instance = self[name]
        for field_to_translate in self.__fields_to_translate__:
            key = getattr(type_instance, field_to_translate)
            if field_to_translate == 'name':
                key = type_instance.name.replace(u'_', u' ').capitalize()
            if key is not None:
                yield key

    def get_verbose_name(self, name):
        if name in self:
            if self.__verbose__ == True:
                verbose_name = self[name].verbose_name
                if not isinstance(verbose_name, ugettext_lazy):
                    verbose_name = ugettext_lazy(verbose_name)
            else:
                verbose_name = name if self.__literal__ == True else name.replace(u'_', u' ').capitalize()
                if 'name' in self.__fields_to_translate__:
                    verbose_name = ugettext_lazy(verbose_name)
            return verbose_name
        elif name is not None:
            return ugettext_lazy(name.replace(u'_', u' ').capitalize())

    def get_choices(self, *args):
        """
        This method has args to be able to use it in dynamic field attributes
        """
        return [(name, self.get_verbose_name(name)) for name in self._data]

    def get_enumeration(self):
        return [(feature_type.id, self.get_verbose_name(feature_type.name)) for feature_type in self]

    def get_modes(self):
        return [Mode(*choice) for choice in self.get_choices()]

    def get_by_id(self, type_id):
        """
        Returns the name of one of this Types' values that matches the given id,
        None if no match is found.
        """
        for t in self:
            if t.id == type_id:
                return t.name


sensitivity_level_type = collections.namedtuple('sensitivity_level_type', ('id', 'name', 'description'))

sensitivity_levels = Types(
    sensitivity_level_type(0, 'insensitive',         'Data field that is insensitive.'),
    sensitivity_level_type(1, 'identifying',         'Data field that uniquely identifies a person.'),
    sensitivity_level_type(2, 'quasi_identifying',   'Data field that can be combined with other fields to identify a person.'),
    sensitivity_level_type(3, 'sensitive_personal',  'Data field containing sensitive personal information.'),
    sensitivity_level_type(4, 'sensitive_financial', 'Data field containing sensitive financial information'),
    sensitivity_level_type(5, 'sensitive_health',    'Data field containing sensitive health information'),
)

