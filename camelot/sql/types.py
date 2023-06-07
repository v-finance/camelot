from sqlalchemy.types import Unicode, Date, Numeric

from camelot.data import types


def mask_first_name(column):
    return 'anon.pseudo_first_name({})'.format(column)

def mask_last_name(column):
    return 'anon.pseudo_last_name({})'.format(column)


class SensitiveType:

    def __init__(self, sensitivity_level, transform=None):
        self.sensitivity_level = sensitivity_level
        self.transform = transform

class SensitiveUnicode(SensitiveType, Unicode):
    """
    Custom SQLAlchemy Unicode type for sensitive data.
    """

    def __init__(self, sensitivity_level, transform=None, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform)
        Unicode.__init__(self, *args, **kwargs)

def IdentifyingUnicode(transform=None, *args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.identifying, transform, *args, **kwargs)

def QuasiIdentifyingUnicode(transform=None, *args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.quasi_identifying, transform, *args, **kwargs)

def SensitivePersonalUnicode(transform=None, *args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_peronsal, transform, *args, **kwargs)

def SensitiveFinancialUnicode(transform=None, *args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_financial, transform, *args, **kwargs)

def SensitiveHealthUnicode(transform=None, *args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_health, transform, *args, **kwargs)


class SensitiveDate(SensitiveType, Date):
    """
    Custom SQLAlchemy Date type for sensitive data.
    """

    def __init__(self, sensitivity_level, transform=None, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform)
        Date.__init__(self, *args, **kwargs)

def IdentifyingDate(transform=None, *args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.identifying, transform, *args, **kwargs)

def QuasiIdentifyingDate(transform=None, *args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.quasi_identifying, transform, *args, **kwargs)

def SensitivePersonalDate(transform=None, *args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_peronsal, transform, *args, **kwargs)

def SensitiveFinancialDate(transform=None, *args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_financial, transform, *args, **kwargs)

def SensitiveHealthDate(transform=None, *args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_health, transform, *args, **kwargs)


class SensitiveNumeric(SensitiveType, Numeric):
    """
    Custom SQLAlchemy Numeric type for sensitive data.
    """

    def __init__(self, sensitivity_level, transform=None, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform)
        Numeric.__init__(self, *args, **kwargs)

def IdentifyingNumeric(transform=None, *args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.identifying, transform, *args, **kwargs)

def QuasiIdentifyingNumeric(transform=None, *args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.quasi_identifying, transform, *args, **kwargs)

def SensitivePersonalNumeric(transform=None, *args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_peronsal, transform, *args, **kwargs)

def SensitiveFinancialNumeric(transform=None, *args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_financial, transform, *args, **kwargs)

def SensitiveHealthNumeric(transform=None, *args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_health, transform, *args, **kwargs)
