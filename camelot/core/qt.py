"""
Qt compatibility module.  This module hides the differences in behavior between :

    * Qt4 and Qt5
    * PyQt and PySide
    * PyQt4 and PyQt5

To switch between different Qt bindings, set the `CAMELOT_QT_API` environment
variable to either `PyQt4` or `PySide`.

"""

import datetime
import logging
import os

import six

LOGGER = logging.getLogger('camelot.core.qt')

qt_api = os.environ.get('CAMELOT_QT_API', None)
if qt_api is not None:
    LOGGER.warn('CAMELOT_QT_API environment variable set to {}'.format(qt_api))

class DelayedModule(object):
    """
    Import QtWebKit as late as possible, since it's the largest
    part of the QT Library (15 meg on Ubuntu linux)
    """
    
    def __init__(self, module_name):
        self.__name__ = module_name
        self.module = None
    
    def __getattr__(self, attr):
        global qt_api
        if self.module is None:
            binding_module = __import__(qt_api,
                                        globals(), locals(), [self.__name__])
            self.module = getattr(binding_module, self.__name__)
        return getattr(self.module, attr)

QtCore = DelayedModule('QtCore')
QtGui = DelayedModule('QtGui')
QtWebKit = DelayedModule('QtWebKit')
QtNetwork = DelayedModule('QtNetwork')
QtXml = DelayedModule('QtXml')

if qt_api in (None, 'PyQt4'):
    try:
        qt_api = 'PyQt4'
        import sip
        QtCore.qt_slot = QtCore.pyqtSlot
        QtCore.qt_signal = QtCore.pyqtSignal
        QtCore.qt_property = QtCore.pyqtProperty
        # the api version is only available after importing QtCore
        variant_api = sip.getapi('QVariant')
        string_api = sip.getapi('QString')

        def is_deleted( qobj ):
            """
            :param qobj: a :class:`QtCore.QObject`
            :return: :const:`True` if the qobj was deleted, :const:`False`
                otherwise
            """
            return sip.isdeleted( qobj )

    except ImportError:
        qt_api = None

elif qt_api in (None, 'PySide'):
    try:
        qt_api = 'PySide'
        QtCore.qt_slot = QtCore.Slot
        QtCore.qt_signal = QtCore.Signal
        QtCore.qt_property = QtCore.Property
        variant_api = 2
        string_api = 2

        def is_deleted( qobj ):
            """
            :param qobj: a :class:`QtCore.QObject`
            :return: :const:`True` if the qobj was deleted, :const:`False`
                otherwise
            """
            return False

    except ImportError:
        qt_api = None

if qt_api is None:
    raise Exception('PyQt4 nor PySide could be imported')
else:
    LOGGER.info('Using {} Qt bindings'.format(qt_api))

Qt = getattr(__import__(qt_api+'.QtCore', globals(), locals(), ['Qt']), 'Qt')

assert variant_api
assert string_api

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

def _variant_to_py_2(value=None):
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
    q_string_size = len
    q_string_startswith = str.startswith
    q_string_endswith = str.endswith
elif string_api==1:
    q_string = QtCore.QString
    q_string_size = QtCore.QString.size
    q_string_startswith = QtCore.QString.startsWith
    q_string_endswith = QtCore.QString.endsWith
else:
    raise Exception('Unsupported QString API')

__all__ = [
    QtCore.__name__,
    QtGui.__name__,
    QtNetwork.__name__,
    Qt.__name__,
    py_to_variant.__name__,
    valid_variant.__name__,
    variant_to_py.__name__,
    ]