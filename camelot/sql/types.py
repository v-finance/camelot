from sqlalchemy.types import Unicode, Date, Numeric

from camelot.data import types

class SensitiveType:

    def __init__(self, sensitivity_level):
        self.sensitivity_level = sensitivity_level

class SensitiveUnicode(SensitiveType, Unicode):
    """
    Custom SQLAlchemy Unicode type for sensitive data.
    """

    def __init__(self, sensitivity_level, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level)
        Unicode.__init__(self, *args, **kwargs)

def IdentifyingUnicode(*args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.identifying, *args, **kwargs)

def QuasiIdentifyingUnicode(*args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.quasi_identifying, *args, **kwargs)

def SensitivePersonalUnicode(*args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_peronsal, *args, **kwargs)

def SensitiveFinancialUnicode(*args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_financial, *args, **kwargs)

def SensitiveHealthUnicode(*args, **kwargs):
    return SensitiveUnicode(types.sensitivity_levels.sensitive_health, *args, **kwargs)



class SensitiveDate(SensitiveType, Date):
    """
    Custom SQLAlchemy Date type for sensitive data.
    """

    def __init__(self, sensitivity_level, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level)
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

    def __init__(self, sensitivity_level, *args, **kwargs):
        SensitiveType.__init__(self, sensitivity_level)
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
