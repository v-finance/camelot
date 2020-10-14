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

"""Functions and classes to use a progress dialog in combination with
a model thread"""

import logging

from camelot.core.utils import ugettext, ugettext_lazy
from camelot.view.art import FontIcon

import six

from ...core.qt import QtModel, QtCore, QtWidgets, Qt, QtQuick, QtQml, py_to_variant, is_deleted

LOGGER = logging.getLogger( 'camelot.view.controls.qml_progress_dialog' )
#LOGGER.setLevel(logging.DEBUG)

class ProgressState:
    def __init__(self):
        self.label = ''
        self.title = ugettext('Please wait')
        self.event_loop = None
        self.details = []
        self.reset()

    def reset(self):
        self.minimum = 0
        self.maximum = 100
        self.value = 0
        self.setValue_called = False
        self.auto_close = True
        self.auto_reset = True
        self.hidden = False
        self.ok_hidden = True
        self.cancel_hidden = False


class QmlProgressDialog(QtCore.QObject):
    """
A Progress Dialog, used during the :meth:`gui_run` of an action.

.. image:: /_static/controls/progress_dialog.png
    """
    # FIXME: ^ update image

    canceled = QtCore.qt_signal()

    def __init__(self, quick_view):
        super().__init__(parent=quick_view)
        self.setObjectName('progress_dialog')

        item = quick_view.findChild(QtCore.QObject, "progress_dialog_item")
        assert item is not None

        item.setParent(self)
        item.cancelClicked.connect(self.cancel)
        item.cancelClicked.connect(self.canceled)
        item.copyClicked.connect(self.copy_clicked)

        self.levels = []
        self._detail_hidden = True
        self._was_canceled = False

        # animation variables
        self._current_offset = 0
        self._direction = 1

    def labelText(self):
        assert len(self.levels)
        return self.levels[-1].label

    @QtCore.qt_slot(str)
    def setLabelText(self, text):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        label_text = item.findChild(QtCore.QObject, 'labelText')
        if label_text is not None:
            label_text.setProperty('text', text)
        if len(self.levels):
            self.levels[-1].label = text

    def isHidden(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        return not item.property('visible')

    def hide(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        if len(self.levels):
            self.levels[-1].hidden = True
        item.setProperty('visible', False)
        self._detail_hidden = True

    def show(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        if len(self.levels):
            self.levels[-1].hidden = False
        item.setProperty('visible', True)

    def minimum(self):
        assert len(self.levels)
        return self.levels[-1].minimum

    @QtCore.qt_slot(int)
    def setMinimum(self, value):
        """
        This property holds the lowest value represented by the progress bar. The default is 0.
        """
        assert len(self.levels)
        self.levels[-1].minimum = value
        self._update_progress()

    def maximum(self):
        assert len(self.levels)
        return self.levels[-1].maximum

    @QtCore.qt_slot(int)
    def setMaximum(self, value):
        """
        This property holds the highest value represented by the progress bar. The default is 100.
        """
        assert len(self.levels)
        self.levels[-1].maximum = value
        self._update_progress()

    @QtCore.qt_slot(int, int)
    def setRange(self, minimum, maximum):
        assert len(self.levels)
        self.levels[-1].minimum = minimum
        self.levels[-1].maximum = maximum
        self._update_progress()

    @QtCore.qt_slot(int)
    def setValue(self, value):
        assert len(self.levels)
        self.levels[-1].value = value
        self.levels[-1].setValue_called = True
        self._update_progress()
        if self.isHidden():
            self.show()
        # auto reset check
        if self.levels[-1].auto_reset:
            if self.levels[-1].value == self.levels[-1].maximum:
                LOGGER.debug('auto reset....')
                self.reset()

    def autoClose(self):
        assert len(self.levels)
        return self.levels[-1].auto_close

    def setAutoClose(self, value):
        """
        This property holds whether the dialog gets hidden by reset(). The default is true.
        """
        assert len(self.levels)
        self.levels[-1].auto_close = value

    def autoReset(self):
        assert len(self.levels)
        return self.levels[-1].auto_reset

    def setAutoReset(self, value):
        """
        This property holds whether the progress dialog calls reset() as soon as value() equals maximum(). The default is true.
        """
        assert len(self.levels)
        self.levels[-1].auto_reset = value


    @QtCore.qt_slot()
    def reset(self):
        """
        Resets the progress dialog. The progress dialog becomes hidden if autoClose() is true.
        """
        LOGGER.debug('reset()')
        assert len(self.levels)
        if self.levels[-1].auto_close:
            LOGGER.debug('auto close...')
            # FIXME
            #self.hide()
        self.levels[-1].reset()
        self._update_progress()
        self.title = self.levels[-1].title
        self._was_canceled = False
        QtCore.QTimer.singleShot(100, self._update_animation)

    @QtCore.qt_slot()
    def cancel(self):
        """
        Resets the progress dialog. wasCanceled() becomes true until the progress dialog is reset. The progress dialog becomes hidden.
        """
        self.reset()
        self._was_canceled = True
        self.hide()

    def wasCanceled(self):
        return self._was_canceled

    def minimumDuration(self):
        """
        Not implemented...
        """
        return 0

    @QtCore.qt_slot(int)
    def setMinimumDuration(self, ms):
        """
        Not implemented...
        """
        pass

    def _update_progress(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        # update the progress bar width
        assert len(self.levels)
        state = self.levels[-1]

        delta = state.maximum - state.minimum
        value = state.value - state.minimum
        if delta != 0:
            percent = value / delta
        else:
            percent = 0
        LOGGER.debug('_update_progress: percent={}  min={}  max={}  val={}'.format(100*percent, self.levels[-1].minimum, self.levels[-1].maximum, self.levels[-1].value))
        item.setProperty('progress', percent)

        offset_rectangle = item.findChild(QtCore.QObject, 'offsetRectangle')
        if offset_rectangle is not None:
            offset_rectangle.setProperty('width', 0)


    @property
    def title(self):
        assert len(self.levels)
        return self.levels[-1].title

    @title.setter
    def title(self, value):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        title_text = item.findChild(QtCore.QObject, 'titleText')
        if title_text is not None:
            title_text.setProperty('text', value)
        if len(self.levels):
            self.levels[-1].title = value

    @QtCore.qt_slot()
    def copy_clicked(self):
        detail_model = self._get_detail_model()
        text = u'\n'.join([six.text_type(s) for s in detail_model.stringList()])
        QtWidgets.QApplication.clipboard().setText(text)

    def push_level(self, verbose_name):
        LOGGER.debug('push_level()')
        self.levels.append(ProgressState())
        LOGGER.debug('# levels: {}'.format(len(self.levels)))
        self.setLabelText(verbose_name)

        self.reset()
        self.set_ok_hidden(self.levels[-1].ok_hidden)
        self.set_cancel_hidden(self.levels[-1].cancel_hidden)

    def pop_level(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        LOGGER.debug('pop_level()')
        self.levels.pop()
        LOGGER.debug('# levels: {}'.format(len(self.levels)))
        if is_deleted(self):
            return
        if len(self.levels):
            self.setLabelText(self.levels[-1].label)
            self._update_progress()
            if self.levels[-1].hidden:
                self.hide()
            else:
                self.show()
            self.set_ok_hidden(self.levels[-1].ok_hidden)
            self.set_cancel_hidden(self.levels[-1].cancel_hidden)
            # restore details
            self.clear_details(False)
            for detail in self.levels[-1].details:
                self.add_detail(detail, False)

            # reconnect ok button with event loop
            try:
                item.okClicked.disconnect()
            except TypeError:
                pass
            if self.levels[-1].event_loop is not None:
                item.okClicked.connect(self.levels[-1].event_loop.quit)

        else:
            self.hide()

    def _get_detail_model(self):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        detail_model = self.findChild(QtModel.QStringListModel, 'detail_model')
        if detail_model is None:
            # a standarditem model is used, in the ideal case, the item
            # model with the real data should live in the model thread, and
            # this should only be a proxy
            detail_model = QtModel.QStringListModel( parent = self )
            detail_model.setObjectName('detail_model')
            detail_list = item.findChild( QtCore.QObject, 'detailList' )
            if detail_list is not None:
                QtQml.QQmlProperty(detail_list, 'model').write(detail_model)
        return detail_model

    def add_detail( self, text, add_to_level=True ):
        """Add detail text to the list of details in the progress dialog
        :param text: a string
        """
        LOGGER.debug('add_detail("{}")'.format(text))
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        # force evaluation of ugettext_lazy (if needed)
        if isinstance(text, ugettext_lazy):
            text = str(text)
        # show copy button
        copy_button = item.findChild(QtCore.QObject, 'copyButton')
        if copy_button is not None:
            copy_button.setProperty('visible', True)

        detail_list = item.findChild( QtCore.QObject, 'detailList' )
        if detail_list is not None:
            detail_model = self._get_detail_model()
            if self._detail_hidden:
                detail_model.removeRows(0, detail_model.rowCount())
                detail_list.setProperty('visible', True)
                self._detail_hidden = False
            detail_model.insertRow(detail_model.rowCount())
            index = detail_model.index(detail_model.rowCount()-1, 0)
            detail_model.setData(index,
                          py_to_variant(text),
                          Qt.DisplayRole)

        if add_to_level and len(self.levels):
            self.levels[-1].details.append(text)

    def clear_details( self, clear_in_level=True ):
        """Clear the detail text"""
        LOGGER.debug('clear_details()')
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        # remove all rows from model
        detail_model = self._get_detail_model()
        detail_model.removeRows(0, detail_model.rowCount())
        # hide the details list
        self._detail_hidden = True
        detail_list = item.findChild( QtCore.QObject, 'detailList' )
        if detail_list is not None:
            detail_list.setProperty('visible', False)
        if clear_in_level and len(self.levels):
            self.levels[-1].details.clear()

    def enlarge(self):
        """
        Not implemented...
        """
        pass

    def set_ok_hidden( self, hidden = True ):
        # hide/show ok button
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        ok_button = item.findChild(QtCore.QObject, 'okButton')
        if ok_button is not None:
            ok_button.setProperty('visible', not hidden)
        # set title to Completed if not hidden
        title_text = item.findChild(QtCore.QObject, 'titleText')
        if title_text is not None:
            if hidden:
                assert len(self.levels)
                title_text.setProperty('text', self.levels[-1].title)
            else:
                assert len(self.levels)
                self.levels[-1].setValue_called = True # stop animation
                title_text.setProperty('text', ugettext('Completed'))
        if len(self.levels):
            self.levels[-1].ok_hidden = hidden


    def exec_(self):
        assert len(self.levels)
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        LOGGER.debug('ENTER exec_()')
        event_loop = QtCore.QEventLoop()
        self.levels[-1].event_loop = event_loop
        # disconnect event loop from lower levels
        try:
            item.okClicked.disconnect()
        except TypeError:
            pass
        item.okClicked.connect(event_loop.quit)
        event_loop.exec_()
        LOGGER.debug('LEAVE exec_()')

    def set_cancel_hidden( self, hidden = True ):
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        cancel_button = item.findChild(QtCore.QObject, 'cancelButton')
        if cancel_button is not None:
            cancel_button.setProperty('visible', not hidden)
        if len(self.levels):
            self.levels[-1].cancel_hidden = hidden



    @QtCore.qt_slot()
    def _update_animation(self):
        """
        Update animation that is used when setValue is not yet called.

        The offsetRectangle is currently used to offset the progressRectangle.
        The progressRectangle has a fixed width (i.e. bar_width) and moves from
        left to right and back.
        """
        LOGGER.debug('_update_animation()')
        item = self.findChild(QtQuick.QQuickItem, 'progress_dialog_item')
        assert item is not None
        if len(self.levels) and self.levels[-1].setValue_called:
            return
        if self.isHidden():
            return

        progress_bar_rectangle = item.findChild(QtCore.QObject, 'progressBarRectangle')
        if progress_bar_rectangle is None:
            return

        bar_width = 200
        total_width = progress_bar_rectangle.property('width')

        offset_rectangle = item.findChild(QtCore.QObject, 'offsetRectangle')
        if offset_rectangle is None:
            return
        progress_rectangle = item.findChild(QtCore.QObject, 'progressRectangle')
        if progress_rectangle is None:
            return

        progress_rectangle.setProperty('width', bar_width)
        offset_rectangle.setProperty('width', max(min(self._current_offset, total_width - bar_width), 0))
        self._current_offset += self._direction * 10
        if self._current_offset >= total_width - bar_width:
            self._direction *= -1
        if self._current_offset <= 0:
            self._direction *= -1

        QtCore.QTimer.singleShot(50, self._update_animation)
