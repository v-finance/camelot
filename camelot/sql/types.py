from sqlalchemy.types import Unicode, Date, Numeric

from camelot.data import types

def remove_transform(data):
    return None

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

    def __init__(self, sensitivity_level, *args, transform=None, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform)
        Unicode.__init__(self, *args, **kwargs)

def IdentifyingUnicode(*args, transform=None, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.identifying, *args, transform=transform, **kwargs)

def QuasiIdentifyingUnicode(*args, transform=None, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.quasi_identifying, *args, transform=transform, **kwargs)

def SensitivePersonalUnicode(*args, transform=None, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_personal, *args, transform=transform, **kwargs)

def SensitiveFinancialUnicode(*args, transform=None, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_financial, *args, transform=transform, **kwargs)

def SensitiveHealthUnicode(*args, transform=None, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_health, *args, transform=transform, **kwargs)


class SensitiveDate(SensitiveType, Date):
    """
    Custom SQLAlchemy Date type for sensitive data.
    """

    def __init__(self, sensitivity_level, *args, transform=None, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform=transform)
        Date.__init__(self, *args, **kwargs)

def IdentifyingDate(*args, transform=None, **kwargs):
    return SensitiveDate(types.sensitivity_levels.identifying, *args, transform=transform, **kwargs)

def QuasiIdentifyingDate(*args, transform=None, **kwargs):
    return SensitiveDate(types.sensitivity_levels.quasi_identifying, *args, transform=transform, **kwargs)

def SensitivePersonalDate(*args, transform=None, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_personal, *args, transform=transform, **kwargs)

def SensitiveFinancialDate(*args, transform=None, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_financial, *args, transform=transform, **kwargs)

def SensitiveHealthDate(*args, transform=None, **kwargs):
    return SensitiveDate(types.sensitivity_levels.sensitive_health, *args, transform=transform, **kwargs)


class SensitiveNumeric(SensitiveType, Numeric):
    """
    Custom SQLAlchemy Numeric type for sensitive data.
    """

    def __init__(self, sensitivity_level, *args, transform=None, **kwargs):
        SensitiveType.__init__(self, sensitivity_level, transform=transform)
        Numeric.__init__(self, *args, **kwargs)

def IdentifyingNumeric(*args, transform=None, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.identifying, *args, transform=transform, **kwargs)

def QuasiIdentifyingNumeric(*args, transform=None, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.quasi_identifying, *args, transform=transform, **kwargs)

def SensitivePersonalNumeric(*args, transform=None, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_personal, *args, transform=transform, **kwargs)

def SensitiveFinancialNumeric(*args, transform=None, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_financial, *args, transform=transform, **kwargs)

def SensitiveHealthNumeric(*args, transform=None, **kwargs):
    return SensitiveNumeric(types.sensitivity_levels.sensitive_health, *args, transform=transform, **kwargs)
