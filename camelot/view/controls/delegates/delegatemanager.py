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

import logging
logger = logging.getLogger('camelot.view.controls.delegates.delegatemanager')

from ....core.serializable import NamedDataclassSerializable
from ....core.item_model import ColumnAttributesRole
from ....core.qt import QtCore, QtWidgets, Qt, is_deleted
from .plaintextdelegate import PlainTextDelegate

class DelegateManager(QtWidgets.QItemDelegate):
    """Manages custom delegates, should not be used by the application
  developer
  """

    actionTriggered = QtCore.qt_signal(list, object, QtWidgets.QWidget)

    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent)
        # set a delegate for the vertical header
        self.insert_column_delegate(-1, PlainTextDelegate(_parent=self))

    def get_column_delegate(self, index):
        column = index.column()
        delegate = self.findChild(QtWidgets.QAbstractItemDelegate, str(column))
        if delegate is None:
            delegate_cls_name, column_attributes = tuple(index.model().headerData(
                column, Qt.Orientation.Horizontal, ColumnAttributesRole
            ))
            delegate_cls = NamedDataclassSerializable.get_cls_by_name(delegate_cls_name)
            delegate = delegate_cls(_parent=self, **column_attributes)
            self.insert_column_delegate(column, delegate)
        return delegate

    def insert_column_delegate(self, column, delegate):
        """Inserts a custom column delegate"""
        assert delegate != None
        delegate.setObjectName(str(column))
        delegate.commitData.connect(self._commit_data)
        delegate.closeEditor.connect(self._close_editor)

    def _commit_data(self, editor):
        self.commitData.emit(editor)

    # @QtCore.qt_slot( QtWidgets.QWidget, QtWidgets.QAbstractItemDelegate.EndEditHint )
    def _close_editor(self, editor, hint):
        self.closeEditor.emit(editor, hint )

    @QtCore.qt_slot(list, object)
    def editorActionTriggered(self, route, mode):
        self.actionTriggered.emit(route, mode, self.sender())

    def createEditor(self, parent, option, index):
        """Use a custom delegate createEditor method if it exists"""
        try:
            delegate = self.get_column_delegate(index)
            editor = delegate.createEditor(parent, option, index)
            editor.actionTriggered.connect(self.editorActionTriggered)
        except Exception as e:
            logger.error('Programming Error : could not createEditor editor data for editor at column %s'%(index.column()), exc_info=e)
            return QtWidgets.QWidget( parent = parent )
        return editor

    def setEditorData(self, editor, index):
        """Use a custom delegate setEditorData method if it exists"""
        logger.debug('setting editor data for column %s' % index.column())
        # the datawidgetmapper has no mechanism to remove a deleted
        # editor from its list of editors for which the data is set
        if not is_deleted(editor):
            try:
                delegate = self.get_column_delegate(index)
                delegate.setEditorData(editor, index)
            except Exception as e:
                logger.error('Programming Error : could not set editor data for editor at column %s'%(index.column()), exc_info=e)
                logger.error('value that could not be set : %s'%str(index.model().data(index, Qt.ItemDataRole.EditRole)))
                logger.error('editor that failed %s %s'%(type(editor).__name__, editor.objectName()))

    def setModelData(self, editor, model, index):
        """Use a custom delegate setModelData method if it exists"""
        logger.debug('setting model data for column %s' % index.column())
        delegate = self.get_column_delegate(index)
        delegate.setModelData(editor, model, index)

    def sizeHint(self, option, index):
        option = QtWidgets.QStyleOptionViewItem()
        delegate = self.get_column_delegate(index)
        return delegate.sizeHint(option, index)

    #def eventFilter(self, *args):
        #"""The datawidgetmapper installs the delegate as an event filter
        #on each editor.

        #TODO : investigate if this is a reliable alternative to implement
               #commitData instead of the editingFinished signal.
        #"""
        #return False


