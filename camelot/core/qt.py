#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
"""
Qt compatibility module.  This module hides the differences in behavior between :

    * Qt4 and Qt5
    * PyQt and PySide
    * PyQt4 and PyQt5

To switch between different Qt bindings, set the `CAMELOT_QT_API` environment
variable to either `PyQt4`, `PySide` or experimental `PyQt5`.

"""

import datetime
import logging
import os

import six

LOGGER = logging.getLogger('camelot.core.qt')

# an empty environment variable might result in an empty string,
# so treat a non existent environment variable as an empty string
qt_api = os.environ.get('CAMELOT_QT_API', '')
if qt_api != '':
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

# virtual modules that points to the qt module containing these classes
QtModel = DelayedModule('QtGui')
QtWidgets = DelayedModule('QtGui')
QtPrintSupport = DelayedModule('QtGui')

if qt_api in ('', 'PyQt4'):
    try:
        qt_api = 'PyQt4'
        import sip
        QtCore.qt_slot = QtCore.pyqtSlot
        QtCore.qt_signal = QtCore.pyqtSignal
        QtCore.qt_property = QtCore.pyqtProperty
        # the api version is only available after importing QtCore
        variant_api = sip.getapi('QVariant')
        string_api = sip.getapi('QString')
        is_deleted = sip.isdeleted
        delete = sip.delete
    except ImportError:
        LOGGER.warn('Could not load PyQt4')
        qt_api = ''

if qt_api in ('', 'PySide'):
    try:
        qt_api = 'PySide'
        QtCore.qt_slot = QtCore.Slot
        QtCore.qt_signal = QtCore.Signal
        QtCore.qt_property = QtCore.Property
        variant_api = 2
        string_api = 2
        is_deleted = lambda _qobj:False
        delete = lambda _qobj:True
    except ImportError:
        LOGGER.warn('Could not load PySide')
        qt_api = ''

if qt_api in ('', 'PyQt5'):
    try:
        qt_api = 'PyQt5'
        import sip
        QtCore.qt_slot = QtCore.pyqtSlot
        QtCore.qt_signal = QtCore.pyqtSignal
        QtCore.qt_property = QtCore.pyqtProperty
        variant_api = 2
        string_api = 2
        QtModel = DelayedModule('QtCore')
        QtWidgets = DelayedModule('QtWidgets')
        QtPrintSupport = DelayedModule('QtPrintSupport')
        QtQml = DelayedModule('QtQml')
        QtQuick = DelayedModule('QtQuick')
        is_deleted = sip.isdeleted
        delete = sip.delete
    except ImportError:
        LOGGER.warn('Could not load PyQt5')
        qt_api = ''

if qt_api=='':
    raise Exception('PyQt4, PySide nor PyQt5 could be imported')
else:
    LOGGER.info('Using {} Qt bindings'.format(qt_api))

Qt = getattr(__import__(qt_api+'.QtCore', globals(), locals(), ['Qt']), 'Qt')

assert variant_api
assert string_api

def _py_to_variant_1( obj=None ):
    """Convert a Python object to a :class:`QtCore.QVariant` object
    """
    if obj is None:
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

if qt_api in ('PyQt4', 'PySide'):

    #
    # Encoding used when transferring translation strings from
    # python to qt
    #
    _encoding=QtCore.QCoreApplication.UnicodeUTF8

    def qtranslate(string_to_translate):
        """Translate a string using the QCoreApplication translation framework
        :param string_to_translate: a unicode string
        :return: the translated unicode string if it was possible to translate
        """
        return six.text_type(QtCore.QCoreApplication.translate('', 
                                                               string_to_translate.encode('utf-8'), 
                                                               encoding=_encoding))

else:

    def qtranslate(string_to_translate):
        """Translate a string using the QCoreApplication translation framework
        :param string_to_translate: a unicode string
        :return: the translated unicode string if it was possible to translate
        """
        return six.text_type(QtCore.QCoreApplication.translate('', 
                                                               string_to_translate.encode('utf-8'),))

    def qmsghandler(msg_type, msg_log_context, msg_string):
        """ Logging handler to redirect messages from Qt to Python """
        log_levels = {
            0: logging.DEBUG,
            1: logging.WARN,
            2: logging.ERROR,
            3: logging.FATAL,
        }
        log_level = log_levels.get(msg_type)
        if log_level is not None:
            LOGGER.log(log_level, msg_string)
        else:
            LOGGER.log(logging.ERROR, 'Received message with unknown log level')

    QtCore.qInstallMessageHandler(qmsghandler)

__all__ = [
    QtCore.__name__,
    QtGui.__name__,
    QtNetwork.__name__,
    Qt.__name__,
    py_to_variant.__name__,
    valid_variant.__name__,
    variant_to_py.__name__,
]

