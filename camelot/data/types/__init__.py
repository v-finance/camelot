import collections
import re

from camelot.core.utils import ugettext_lazy
from camelot.admin.action import Mode

from sqlalchemy import util

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

# Zip/Postal code types with regular expression specifications as required for use with BECRIS.
class zip_code_type(collections.namedtuple('zip_code_type', ('code', 'regex', 'repl', 'example'))):

    @property
    def id(self):
        return self.code

    @property
    def name(self):
        return self.code

    @property
    def prefixes(self):
        prefixes = []
        if self.code is not None:
            prefixes.append(self.code)
        if self.regex is not None:
            m = re.match('\(\?\:([^\)]+)\)', self.regex)
            if m is not None:
                prefixes.extend(m.group(1).split('|'))
        return set(prefixes)

    @property
    def compact_repl(self):
        if self.repl is not None:
            if '|' in self.repl:
                def multi_repl(m):
                    for i, repl in enumerate(self.repl.split('|'), start=1):
                        if m.group(i) is not None:
                            return re.sub(m.re, ''.join(re.findall('\\\\\d+', repl)), m.string)
                return multi_repl
            return ''.join(re.findall('\\\\\d+', self.repl))

    @property
    def format_repl(self):
        if self.repl is not None and '|' in self.repl:
            def multi_repl(m):
                for i, repl in enumerate(self.repl.split('|'), start=1):
                    if m.group(i) is not None:
                        return re.sub(m.re, repl, m.string)
            return multi_repl
        return self.repl

    @property
    def tooltip(self):
        if self.example is not None:
            return 'e.g: {}'.format(self.example)

zip_code_types = Types(
  #             #code #regex                                            #regex_repl     #example
  zip_code_type("AD", "AD\d{3}",                                         None,          "AD100"),
  zip_code_type("AF", "\d{4}",                                           None,          "1057"),
  zip_code_type("AI", "(AI)-?(2640)",                                   "\\1-\\2",      "AI-2640"),
  zip_code_type("AL", "\d{4}",                                           None,          "5300"),
  zip_code_type("AM", "\d{4}(\d{2})?",                                   None,          "0010, 001011"),
  zip_code_type("AQ", "7151",                                            None,          "7151"),
  zip_code_type("AR", "[A-Z]\d{4}([A-Z]{3})?",                           None,          "C1425CLA, U9000"),
  zip_code_type("AS", "^(967\d{2})$|^((967\d{2})-?(\d{4}))$",           "\\1|\\3-\\4",  "96799, 96799-9999"),
  zip_code_type("AT", "\d{4}",                                           None,          "1010"),
  zip_code_type("AU", "\d{4}",                                           None,          "2599"),
  zip_code_type("AX", "22\d{3}",                                         None,          "22999"),
  zip_code_type("AZ", "(?:AZ)? ?(\d{4})",                               "AZ \\1",       "AZ 1000, AZ1000"),
  zip_code_type("BA", "\d{5}",                                           None,          "71000"),
  zip_code_type("BB", "BB\d{5}",                                         None,          "BB15094"),
  zip_code_type("BD", "\d{4}",                                           None,          "1219"),
  zip_code_type("BE", "\d{4}",                                           None,          "1049"),
  zip_code_type("BF", "[1-9]\d{4}",                                      None,          "99999"),
  zip_code_type("BG", "\d{4}",                                           None,          "1000"),
  zip_code_type("BH", "\d{3}\d?",                                        None,          "317, 1216"),
  zip_code_type("BL", "9709\d{1}|97133",                                 None,          "97099, 97133"),
  zip_code_type("BM", "([A-Z]{2}) ?(\d{2})",                            "\\1 \\2",      "CR 03"),
  zip_code_type("BN", "[A-Z]{2}\d{4}",                                   None,          "KB2333"),
  zip_code_type("BR", "([0-9]{5})-?([0-9]{3})",                         "\\1-\\2",      "28999-999"),
  zip_code_type("BT", "\d{5}",                                           None,          "31002"),
  zip_code_type("BY", "\d{6}",                                           None,          "231300"),
  zip_code_type("CA", "([A-Z][0-9][A-Z]) ?([0-9][A-Z][0-9])",           "\\1 \\2",     "K1A 0T6"),
  zip_code_type("CC", "6799",                                            None,          "6799"),
  zip_code_type("CH", "[1-9]\d{3}",                                      None,          "8050"),
  zip_code_type("CL", "\d{7}",                                           None,          "9340000"),
  zip_code_type("CN", "\d{6}",                                           None,          "710000"),
  zip_code_type("CO", "\d{6}",                                           None,          "111121"),
  zip_code_type("CR", "\d{5}",                                           None,          "10101"),
  zip_code_type("CU", "(?:CP)?(\d{5})",                                 "CP \\1",       "CP10400, 33700"),
  zip_code_type("CV", "\d{4}",                                           None,          "5110"),
  zip_code_type("CX", "6798",                                            None,          "6798"),
  zip_code_type("CY", "[1-9]\d{3}",                                      None,          "4999"),
  zip_code_type("CZ", "([1-7][0-9]{2}) ?([0-9]{2})",                    "\\1 \\2",      "160 00, 16000"),
  zip_code_type("DE", "\d{5}",                                           None,          "60320"),
  zip_code_type("DK", "\d{4}",                                           None,          "2000"),
  zip_code_type("DO", "\d{5}",                                           None,          "10103"),
  zip_code_type("DZ", "\d{5}",                                           None,          "16000"),
  zip_code_type("EC", "\d{6}",                                           None,          "170515"),
  zip_code_type("EE", "\d{5}",                                           None,          "10111"),
  zip_code_type("EG", "\d{5}",                                           None,          "12411"),
  zip_code_type("EH", "7\d{4}",                                          None,          "70000, 71000"),
  zip_code_type("ES", "\d{5}",                                           None,          "28006"),
  zip_code_type("ET", "\d{4}",                                           None,          "3020"),
  zip_code_type("FI", "\d{5}",                                           None,          "00180"),
  zip_code_type("FK", "(FIQQ) ?(1ZZ)",                                  "\\1 \\2",      "FIQQ 1ZZ"),
  zip_code_type("FM", "^(9694\d{1})$|^((9694\d{1})-?(\d{4}))$",         "\\1|\\3-\\4",  "96942, 96942-9999"),
  zip_code_type("FO", "\d{3}",                                           None,          "927"),
  zip_code_type("FR", "\d{5}",                                           None,          "75008"),
  zip_code_type("GB", "^((GIR) ?(0AA))$|^(([A-Z][0-9]{1,2}) ?([0-9][A-Z]{2}))$|^(([A-Z][A-HJ-Y][0-9]{1,2}) ?([0-9][A-Z]{2}))$|^(([A-Z][A-HJ-Y][0-9]?[A-Z]) ?([0-9][A-Z]{2}))$|^(([A-Z][0-9][A-Z]) ?([0-9][A-Z]{2}))$", "\\2 \\3|||\\5 \\6|||\\8 \\9|||\\11 \\12|||\\14 \\15", "M2 5BQ, M34 4AB, CR0 2YR, DN16 9AA, W1A 4ZZ, EC1A 1HQ"),
  zip_code_type("GE", "\d{4}",                                           None,          "0100"),
  zip_code_type("GF", "973\d{2}",                                        None,          "97310"),
  zip_code_type("GG", "(GY([0-9][0-9A-HJKPS-UW]?|[A-HK-Y][0-9][0-9ABEHMNPRV-Y]?)) ?([0-9][ABD-HJLNP-UW-Z]{2})", "\\1 \\3", "GY1 3HR"),
  zip_code_type("GI", "(GX11) ?(1AA)",                                  "\\1 \\2",      "GX11 1AA"),
  zip_code_type("GL", "39\d{2}",                                         None,          "3905"),
  zip_code_type("GN", "\d{3}",                                           None,          "001"),
  zip_code_type("GP", "97[0-1]\d{2}",                                    None,          "97122"),
  zip_code_type("GR", "(\d{3}) ?(\d{2})",                               "\\1 \\2",      "241 00, 24100"),
  zip_code_type("GS", "(SIQQ) ?(1ZZ)",                                  "\\1 \\2",      "SIQQ 1ZZ"),
  zip_code_type("GT", "\d{5}",                                           None,          "01002"),
  zip_code_type("GU", "^(969[1-3][0-2])$|^((969[1-3][0-2])-?(\d{4}))$", "\\1|\\3-\\4",  "96911, 96911-9999"),
  zip_code_type("GW", "\d{4}",                                           None,          "1000"),
  zip_code_type("HK", "999077",                                          None,          "999077"),
  zip_code_type("HM", "7151",                                            None,          "7151"),
  zip_code_type("HN", "\d{5}",                                           None,          "34101"),
  zip_code_type("HR", "[1-5]\d{4}",                                      None,          "21000"),
  zip_code_type("HT", "(?:HT) ?(\d{4})",                                "HT\\1",        "HT1440"),
  zip_code_type("HU", "[1-9]\d{3}",                                      None,          "2310"),
  zip_code_type("ID", "[1-9]\d{4}",                                      None,          "15360"),
  zip_code_type("IL", "\d{7}",                                           None,          "1029200"),
  zip_code_type("IM", "(IM([0-9][0-9A-HJKPS-UW]?|[A-HK-Y][0-9][0-9ABEHMNPRV-Y]?)) ?([0-9][ABD-HJLNP-UW-Z]{2})", "\\1 \\3", "IM5 1JS"),
  zip_code_type("IN", "[1-9]\d{5}",                                      None,          "500012"),
  zip_code_type("IO", "(BB9D) ?(1ZZ)",                                  "\\1 \\2",      "BB9D 1ZZ"),
  zip_code_type("IQ", "\d{5}",                                           None,          "58019"),
  zip_code_type("IR", "(\d{5})-?(\d{5})",                               "\\1-\\2",       "9187158198, 15119-43943"),
  zip_code_type("IS", "[1-9]\d{2}",                                      None,          "101"),
  zip_code_type("IT", "\d{5}",                                           None,          "36051"),
  zip_code_type("JE", "(JE[0-9]{1}) ?(\d[A-Z]{2})",                     "\\1 \\2",      "JE1 1AG"),
  zip_code_type("JM", "JM[A-Z]{3}\d{2}",                                 None,          "JMAAW19"),
  zip_code_type("JO", "\d{5}",                                           None,          "11118"),
  zip_code_type("JP", "(\d{3})-?(\d{4})",                               "\\1-\\2",      "408-0307"),
  zip_code_type("KE", "\d{5}",                                           None,          "40406"),
  zip_code_type("KG", "\d{6}",                                           None,          "720020"),
  zip_code_type("KH", "\d{5,6}",                                         None,          "01501, 010102, 120209"),
  zip_code_type("KI", "KI\d{4}",                                         None,          "KI0107"),
  zip_code_type("KN", "^(KN\d{4})$|^((KN\d{4})-?(\d{4}))$",             "\\1|\\3-\\4",  "KN0101, KN0802, KN0801-0802, KN0901-0902"),
  zip_code_type("KR", "\d{5}",                                           None,          "11962"),
  zip_code_type("KW", "\d{5}",                                           None,          "60000"),
  zip_code_type("KY", "(KY[0-9]{1})-?([0-9]{4})",                       "\\1-\\2",      "KY1-1800"),
  zip_code_type("KZ", "([A-Z]\d{2}[A-Z]\d[A-Z]\d)|(\d{6})",              None,          "A10A5T4, 010010"),
  zip_code_type("LA", "\d{5}",                                           None,          "13000"),
  zip_code_type("LB", "^(\d{4})$|^((\d{4}) ?(\d{4}))$",                 "\\1|\\3 \\4",  "2038 3054, 1103"),
  zip_code_type("LC", "(LC\d{2}) ?(\d{3})",                             "\\1 \\2",      "LC05 201"),
  zip_code_type("LI", "\d{4}",                                           None,          "9490"),
  zip_code_type("LK", "\d{5}",                                           None,          "80212"),
  zip_code_type("LR", "\d{4}",                                           None,          "1000"),
  zip_code_type("LS", "\d{3}",                                           None,          "100"),
  zip_code_type("LT", "(?:LT)?-?(\d{5})",                               "LT-\\1",       "LT-01100, 01100"),
  zip_code_type("LU", "(?:L)?-?(\d{4})",                                "L-\\1",        "1019, L-2530"),
  zip_code_type("LV", "(?:LV)?-?(\d{4})",                               "LV-\\1",       "LV-1010, 1010"),
  zip_code_type("MA", "[1-9]\d{4}",                                      None,          "20192"),
  zip_code_type("MC", "980\d{2}",                                        None,          "98000"),
  zip_code_type("MD", "(?:MD)?-?(\d{4})",                               "MD-\\1",       "MD2001, MD-2001, 2001"),
  zip_code_type("ME", "\d{5}",                                           None,          "81250"),
  zip_code_type("MF", "97[0-1]\d{2}",                                    None,          "97150"),
  zip_code_type("MG", "\d{3}",                                           None,          "101"),
  zip_code_type("MH", "^(969[6-7][0-9])$|^((969[6-7][0-9])-?(\d{4}))$", "\\1|\\3-\\4",  "96960, 96960-9999"),
  zip_code_type("MK", "\d{4}",                                           None,          "1045"),
  zip_code_type("MM", "\d{5}",                                           None,          "11121"),
  zip_code_type("MN", "\d{5}",                                           None,          "16080"),
  zip_code_type("MP", "^(9695\d{1})$|^((9695\d{1})-?(\d{4}))$",         "\\1|\\3-\\4",  "96950, 96950-9999"),
  zip_code_type("MQ", "972\d{2}",                                        None,          "97212"),
  zip_code_type("MS", "MSR\d{4}",                                        None,          "MSR1120"),
  zip_code_type("MT", "(([A-Z]{3}) ?([0-9]{4}))|(([A-Z]{2}) ?([0-9]{2}))|(([A-Z]{3}) ?([0-9]{2}))", "\\2 \\3|||\\5 \\6|||\\8 \\9", "VLT 1117, TP01, TP 01, RBT1676, QRM09, BKR 01"),
  zip_code_type("MU", "[0-9A-R]\d{4}",                                   None,          "A0000, 20101"),
  zip_code_type("MV", "\d{5}",                                           None,          "20195"),
  zip_code_type("MW", "\d{6}",                                           None,          "101100, 307100"),
  zip_code_type("MX", "\d{5}",                                           None,          "97229"),
  zip_code_type("MY", "\d{5}",                                           None,          "50050"),
  zip_code_type("MZ", "\d{4}",                                           None,          "1104"),
  zip_code_type("NA", "\d{5}",                                           None,          "10003"),
  zip_code_type("NC", "988\d{2}",                                        None,          "98814"),
  zip_code_type("NE", "\d{4}",                                           None,          "8001"),
  zip_code_type("NF", "(2899)",                                          None,          "2899"),
  zip_code_type("NG", "[1-9]\d{5}",                                      None,          "100001"),
  zip_code_type("NI", "\d{5}",                                           None,          "11001"),
  zip_code_type("NL", "([1-9]\d{3}) ?([A-Z]{2})",                       "\\1 \\2",      "1011 AC, 1011AC"),
  zip_code_type("NO", "\d{4}",                                           None,          "5262"),
  zip_code_type("NP", "\d{5}",                                           None,          "44600"),
  zip_code_type("NR", "(NRU68)",                                         None,          "NRU68"),
  zip_code_type("NU", "(9974)",                                          None,          "9974"),
  zip_code_type("NZ", "\d{4}",                                           None,          "8041"),
  zip_code_type("OM", "\d{3}",                                           None,          "112"),
  zip_code_type("PA", "\d{4}",                                           None,          "0601, 1001"),
  zip_code_type("PE", "\d{5}",                                           None,          "15001"),
  zip_code_type("PF", "((987)\d{2})",                                    None,          "98755"),
  zip_code_type("PG", "\d{3}",                                           None,          "244"),
  zip_code_type("PH", "\d{4}",                                           None,          "4104"),
  zip_code_type("PK", "[1-9]\d{4}",                                      None,          "75600"),
  zip_code_type("PL", "([0-9]{2})-?([0-9]{3})",                         "\\1-\\2",      "87-100"),
  zip_code_type("PM", "975\d{2}",                                        None,          "97500"),
  zip_code_type("PN", "(PCR9) ?(1ZZ)",                                  "\\1 \\2",      "PCR9 1ZZ"),
  zip_code_type("PR", "^(00\d{3})$|^((00\d{3})-?(\d{4}))$",             "\\1|\\3-\\4",  "00716, 00601, 00716-9999"),
  zip_code_type("PS", "(P[1-9]\d{6})|((\d{3})-?(\d{3}))",               "\\1|\\3-\\4",  "600-699, P3600700"),
  zip_code_type("PT", "([1-9]\d{3})-?(\d{3})",                          "\\1-\\2",      "1000-260"),
  zip_code_type("PW", "96939|96940",                                     None,          "96939, 96940"),
  zip_code_type("PY", "\d{4}",                                           None,          "3180"),
  zip_code_type("RE", "(974|977|978)\d{2}",                              None,          "97450"),
  zip_code_type("RO", "\d{6}",                                           None,          "507085"),
  zip_code_type("RS", "\d{5,6}",                                         None,          "24430, 456769"),
  zip_code_type("RU", "\d{6}",                                           None,          "385100"),
  zip_code_type("SA", "^([1-8]\d{4})$|^(([1-8]\d{4})-?(\d{4}))$",       "\\1|\\3-\\4",  "11564, 75311-8538"),
  zip_code_type("SD", "\d{5}",                                           None,          "13315"),
  zip_code_type("SE", "([1-9]\d{2}) ?(\d{2})",                          "\\1 \\2",      "113 51"),
  zip_code_type("SG", "\d{6}",                                           None,          "570150"),
  zip_code_type("SH", "((ASCN) ?(1ZZ))|((TDCU) ?(1ZZ))|((STHL) ?(1ZZ))", "\\2 \\3|||\\5 \\6|||\\8 \\9",         "ASCN 1ZZ, TDCU 1ZZ, STHL 1ZZ"),
  zip_code_type("SI", "[1-9]\d{3}",                                      None,          "8341"),
  zip_code_type("SJ", "8099|(917[0-1])",                                 None,          "8099, 9170, 9171"),
  zip_code_type("SK", "(\d{3}) ?(\d{2})",                               "\\1 \\2",      "811 01, 81101"),
  zip_code_type("SM", "4789\d{1}",                                       None,          "47894"),
  zip_code_type("SN", "[1-8]\d{4}",                                      None,          "10200"),
  zip_code_type("SS", "\d{5}",                                           None,          "11111"),
  zip_code_type("SV", "\d{4}",                                           None,          "1201"),
  zip_code_type("SZ", "([A-Z]\d{3})",                                    None,          "M201"),
  zip_code_type("TC", "(TKCA) ?(1ZZ)",                                  "\\1 \\2",      "TKCA 1ZZ"),
  zip_code_type("TH", "\d{5}",                                           None,          "10240"),
  zip_code_type("TJ", "7\d{5}",                                          None,          "799999"),
  zip_code_type("TM", "7\d{5}",                                          None,          "745180"),
  zip_code_type("TN", "\d{4}",                                           None,          "3200"),
  zip_code_type("TR", "\d{5}",                                           None,          "34000"),
  zip_code_type("TT", "\d{6}",                                           None,          "120110"),
  zip_code_type("TW", "^((\d{3})-?(\d{2,3}))$|^(\d{6})$|^(\d{3})$",     "\\2-\\3|||\\4|\\5", "237-01, 407, 999999, 999-999"),
  zip_code_type("TZ", "\d{5}",                                           None,          "31324"),
  zip_code_type("UA", "\d{5}",                                           None,          "65000"),
  zip_code_type("US", "^(\d{5})$|^((\d{5})-?(\d{4}))$",                 "\\1|\\3-\\4", "11550, 11550-9999, 00716, 00716-9999"),
  zip_code_type("UY", "[1-9]\d{4}",                                      None,          "11700"),
  zip_code_type("UZ", "\d{6}",                                           None,          "702100"),
  zip_code_type("VA", "00120",                                           None,          "00120"),
  zip_code_type("VC", "VC\d{4}",                                         None,          "VC0100"),
  zip_code_type("VE", "[1-8]\d{3}",                                      None,          "1061"),
  zip_code_type("VG", "VG11[0-6]0",                                      None,          "VG1120"),
  zip_code_type("VI", "^(008\d{2})$|^((008\d{2})-?(\d{4}))$",           "\\1|\\3-\\4",  "00850, 00850-9999"),
  zip_code_type("VN", "\d{6}",                                           None,          "112132"),
  zip_code_type("WF", "986\d{2}",                                        None,          "98600"),
  zip_code_type("WS", "WS[1-2]\d{3}",                                    None,          "WS1382"),
  zip_code_type("YT", "(976|985)\d{2}",                                  None,          "97600"),
  zip_code_type("ZA", "\d{4}",                                           None,          "6001"),
  zip_code_type("ZM", "\d{5}",                                           None,          "50100"),
  literal=True,
)
