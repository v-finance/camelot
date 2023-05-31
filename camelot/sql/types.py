from sqlalchemy.types import Unicode, Date, Numeric

from camelot.data import types


def first_letter_transform(data):
    return data[0] if data else data


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

def IdentifyingDate(*args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.identifying, *args, **kwargs)

def QuasiIdentifyingDate(*args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.quasi_identifying, *args, **kwargs)

def SensitivePersonalDate(*args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_peronsal, *args, **kwargs)

def SensitiveFinancialDate(*args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_financial, *args, **kwargs)

def SensitiveHealthDate(*args, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_health, *args, **kwargs)


class SensitiveNumeric(SensitiveType, Numeric):
    """
    Custom SQLAlchemy Numeric type for sensitive data.
    """

    def __init__(self, sensitivity_level, transform=None, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform)
        Numeric.__init__(self, *args, **kwargs)

def IdentifyingNumeric(*args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.identifying, *args, **kwargs)

def QuasiIdentifyingNumeric(*args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.quasi_identifying, *args, **kwargs)

def SensitivePersonalNumeric(*args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_peronsal, *args, **kwargs)

def SensitiveFinancialNumeric(*args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_financial, *args, **kwargs)

def SensitiveHealthNumeric(*args, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_health, *args, **kwargs)
