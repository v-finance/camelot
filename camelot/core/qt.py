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

class DelayedQtWebEngineWidgets(DelayedModule):

    @property
    def QWebView(self):
        return self.QWebEngineView

QtCore = DelayedModule('QtCore')
QtGui = DelayedModule('QtGui')
QtWebKit = DelayedModule('QtWebKit')
QtNetwork = DelayedModule('QtNetwork')
QtXml = DelayedModule('QtXml')

# virtual modules that points to the qt module containing these classes
QtModel = DelayedModule('QtGui')
QtWidgets = DelayedModule('QtGui')
QtPrintSupport = DelayedModule('QtGui')

if qt_api in ('', 'PySide'):
    try:
        qt_api = 'PySide'
        QtCore.qt_slot = QtCore.Slot
        QtCore.qt_signal = QtCore.Signal
        QtCore.qt_property = QtCore.Property
        is_deleted = lambda _qobj:False
        delete = lambda _qobj:True
    except ImportError:
        LOGGER.warn('Could not load PySide')
        qt_api = ''

if qt_api in ('', 'PyQt6'):
    try:
        qt_api = 'PyQt6'
        # as of pyqt 5.11, qt should be imported before sip
        from PyQt6 import QtCore
        from PyQt6 import sip
        QtCore.qt_slot = QtCore.pyqtSlot
        QtCore.qt_signal = QtCore.pyqtSignal
        QtCore.qt_property = QtCore.pyqtProperty
        QtModel = DelayedModule('QtCore')
        QtWidgets = DelayedModule('QtWidgets')
        QtPrintSupport = DelayedModule('QtPrintSupport')
        QtQml = DelayedModule('QtQml')
        QtQuick = DelayedModule('QtQuick')
        #QtWebKit = DelayedQtWebEngineWidgets('QtWebEngineWidgets')
        QtWebKit = DelayedModule('QtWebKitWidgets')
        QtQuickWidgets = DelayedModule('QtQuickWidgets')
        is_deleted = sip.isdeleted
        delete = sip.delete
        transferto = sip.transferto
    except ImportError:
        LOGGER.warn('Could not load PyQt6')
        qt_api = ''

if qt_api=='':
    raise Exception('PyQt4, PyQt5, PyQt6 nor PySide could be imported')
else:
    LOGGER.info('Using {} Qt bindings'.format(qt_api))

Qt = getattr(__import__(qt_api+'.QtCore', globals(), locals(), ['Qt']), 'Qt')

def _py_to_variant_2( obj=None ):
    return obj

def _valid_variant_2( variant ):
    return variant!=None

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

py_to_variant = _py_to_variant_2
valid_variant = _valid_variant_2
variant_to_py = _variant_to_py_2

if qt_api in ('PySide'):

    #
    # Encoding used when transferring translation strings from
    # python to qt
    #
    _encoding=QtCore.QCoreApplication.UnicodeUTF8

    def qtranslate(string_to_translate, n=-1, msgctxt=None):
        """Translate a string using the QCoreApplication translation framework
        :param string_to_translate: a unicode string
        :return: the translated unicode string if it was possible to translate
        """
        msgctxt_encoded = None
        if msgctxt is not None:
            msgctxt_encoded = msgctxt.encode('utf-8')
        return str(QtCore.QCoreApplication.translate(
            '',
            string_to_translate.encode('utf-8'),
            msgctxt_encoded,
            _encoding,
            n
        ))

else:

    def qtranslate(string_to_translate, n=-1, msgctxt=None):
        """Translate a string using the QCoreApplication translation framework
        :param string_to_translate: a unicode string
        :return: the translated unicode string if it was possible to translate
        """
        msgctxt_encoded = None
        if msgctxt is not None:
            msgctxt_encoded = msgctxt.encode('utf-8')
        return str(QtCore.QCoreApplication.translate(
            '',
            string_to_translate.encode('utf-8'),
            msgctxt_encoded,
            n,
        ))

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

    # Qt messages are now remotely logged by the launcher's message handler
    #QtCore.qInstallMessageHandler(qmsghandler)

def jsonvalue_to_py(obj=None):
    """Convert QJsonValue to python equivalent"""
    if isinstance(obj, QtCore.QJsonValue):
        return obj.toVariant()
    return obj

__all__ = [
    QtCore.__name__,
    QtGui.__name__,
    QtNetwork.__name__,
    Qt.__name__,
    py_to_variant.__name__,
    valid_variant.__name__,
    variant_to_py.__name__,
    jsonvalue_to_py.__name__,
]

