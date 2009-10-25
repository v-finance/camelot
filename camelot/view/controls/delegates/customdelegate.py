#  ===========================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ===========================================================================

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QItemDelegate
from camelot.core.utils import variant_to_pyobject

from camelot.view.controls import editors
from camelot.core.utils import create_constant_function
from camelot.view.proxy import ValueLoading

# custom color
not_editable_background = QtGui.QColor(235, 233, 237)
# darkgray
not_editable_foreground = QtGui.QColor(Qt.darkGray)


def DocumentationMetaclass(name, bases, dct):
    dct['__doc__'] = dct.get('__doc__','') + """

.. image:: ../_static/delegates/%s_unselected_disabled.png
.. image:: ../_static/delegates/%s_unselected_editable.png
.. image:: ../_static/delegates/%s_selected_disabled.png
.. image:: ../_static/delegates/%s_selected_editable.png
"""%(name, name, name, name)
    return type(name, bases, dct)

  
class CustomDelegate(QItemDelegate):
    """Base class for implementing custom delegates.

.. attribute:: editor 

class attribute specifies the editor class that should be used
"""

    editor = None
  
    def __init__(self, parent=None, editable=True, **kwargs):
        """:param parent: the parent object for the delegate
:param editable: a boolean indicating if the field associated to the delegate
is editable"""
        QItemDelegate.__init__(self, parent)
        self.editable = editable
        self.kwargs = kwargs
        self._font_metrics = QtGui.QFontMetrics(QtGui.QApplication.font())
        self._height = self._font_metrics.lineSpacing() + 10
        self._width = self._font_metrics.averageCharWidth() * 20
    
    def createEditor(self, parent, option, index):
        """:param option: use an option with version 5 to indicate the widget
will be put onto a form"""
        editor = self.editor(parent, editable=self.editable, **self.kwargs)
        if option.version != 5:
            editor.setAutoFillBackground(True)
        self.connect(editor,
                     editors.editingFinished,
                     self.commitAndCloseEditor)
        return editor
  
    def sizeHint(self, option, index):
        return QtCore.QSize(self._width, self._height)

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget*)'), editor)
        sig = SIGNAL('closeEditor(QWidget*, \
                                  QAbstractItemDelegate::EndEditHint)')
        self.emit(sig, editor, QtGui.QAbstractItemDelegate.NoHint)

    def setEditorData(self, editor, index):
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        editor.set_value(value)
        index.model().data(index, Qt.ToolTipRole)
        tip = variant_to_pyobject(index.model().data(index, Qt.ToolTipRole))
        if tip not in (None, ValueLoading):
            editor.setToolTip(unicode(tip))
        else:
            editor.setToolTip('')

    def setModelData(self, editor, model, index):
        if isinstance(model, QtGui.QStandardItemModel):
            val = QtCore.QVariant(editor.get_value())
        else:
            val = create_constant_function(editor.get_value())
        model.setData(index, val)
