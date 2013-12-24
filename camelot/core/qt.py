"""
Qt compatibility module.  This module hides the differences in behavior between :

    * Qt4 and Qt5
    * PyQt and PySide
    * PyQt4 and PyQt5

"""

import datetime

import six

try:
    import sip
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore import Qt
    
    # the api version is only available after importing QtCore
    variant_api = sip.getapi('QVariant')
    string_api = sip.getapi('QString')
except ImportError:
    try:
        from PySide import QtCore, QtGui
        from PySide.QtCore import Qt
        variant_api = 2
        string_api = 2
    except ImportError:
        raise Exception('PyQt nor PySide could be imported')

def _py_to_variant_1( obj=None ):
    """Convert a Python object to a :class:`QtCore.QVariant` object
    """
    if obj==None:
        return QtCore.QVariant()
    return QtCore.QVariant(obj)

def _py_to_variant_2( obj=None ):
    return obj

def _valid_variant_1( variant ):
    return variant.isValid()

def _valid_variant_2( variant ):
    return variant!=None

def _variant_to_py_1(qvariant=None):
    """Try to convert a QVariant to a python object as good as possible"""
    if not qvariant:
        return None
    if qvariant.isNull():
        return None
    type = qvariant.type()
    if type == QtCore.QVariant.String:
        value = six.text_type(qvariant.toString())
    elif type == QtCore.QVariant.Date:
        value = qvariant.toDate()
        value = datetime.date( year=value.year(),
                               month=value.month(),
                               day=value.day() )
    elif type == QtCore.QVariant.Int:
        value = int(qvariant.toInt()[0])
    elif type == QtCore.QVariant.LongLong:
        value = int(qvariant.toLongLong()[0])
    elif type == QtCore.QVariant.Double:
        value = float(qvariant.toDouble()[0])
    elif type == QtCore.QVariant.Bool:
        value = bool(qvariant.toBool())
    elif type == QtCore.QVariant.Time:
        value = qvariant.toTime()
        value = datetime.time( hour = value.hour(),
                               minute = value.minute(),
                               second = value.second() )
    elif type == QtCore.QVariant.DateTime:
        value = qvariant.toDateTime()
        value = value.toPyDateTime()
    elif type == QtCore.QVariant.Color:
        value = QtGui.QColor(qvariant)
    elif type == QtCore.QVariant.ByteArray:
        value = qvariant.toByteArray()
    else:
        value = qvariant.toPyObject()

    return value

def _variant_to_py_2( value ):
    if isinstance( value, QtCore.QDate ):
        value = datetime.date( year = value.year(),
                               month = value.month(),
                               day = value.day() )
    elif isinstance( value, QtCore.QTime ):
        value = datetime.time( hour = value.hour(),
                               minute = value.minute(),
                               second = value.second() )
    elif isinstance( value, QtCore.QDateTime ):
        date = value.date()
        time = value.time()
        value = datetime.datetime( year = date.year(),
                                   month = date.month(),
                                   day = date.day(),
                                   hour = time.hour(),
                                   minute = time.minute(),
                                   second = time.second()
                                   )
    return value

if variant_api==2:
    py_to_variant = _py_to_variant_2
    valid_variant = _valid_variant_2
    variant_to_py = _variant_to_py_2
elif variant_api==1:
    py_to_variant = _py_to_variant_1
    valid_variant = _valid_variant_1
    variant_to_py = _variant_to_py_1
else:
    raise Exception('Unsupported QVariant API')

def _q_string_2(arg=None):
    return arg

if string_api==2:
    q_string = _q_string_2
elif string_api==1:
    q_string = QtCore.QString
else:
    raise Exception('Unsupported QString API')

__all__ = [
    QtCore.__name__,
    QtGui.__name__,
    Qt.__name__,
    py_to_variant.__name__,
    valid_variant.__name__,
    variant_to_py.__name__,
    ]