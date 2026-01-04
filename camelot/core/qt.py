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

import datetime
import logging

LOGGER = logging.getLogger('camelot.core.qt')


from PyQt6 import QtCore, QtGui, QtNetwork, QtXml, QtWidgets
# as of pyqt 5.11, qt should be imported before sip
from PyQt6 import sip

QtCore.qt_slot = QtCore.pyqtSlot
QtCore.qt_signal = QtCore.pyqtSignal
QtCore.qt_property = QtCore.pyqtProperty

is_deleted = sip.isdeleted
delete = sip.delete
transferto = sip.transferto
Qt = QtCore.Qt


def py_to_variant( obj=None ):
    return obj

def variant_to_py(value=None):
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


__all__ = [
    QtCore.__name__,
    QtGui.__name__,
    QtNetwork.__name__,
    QtWidgets.__name__,
    QtXml.__name__,
    Qt.__name__,
    py_to_variant.__name__,
    variant_to_py.__name__,
]

