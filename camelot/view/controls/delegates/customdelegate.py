#  ===========================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QItemDelegate
from camelot.core.utils import variant_to_pyobject

from camelot.core.utils import create_constant_function
from camelot.view.proxy import ValueLoading

# custom color
not_editable_background = QtGui.QColor(235, 233, 237)
# darkgray
not_editable_foreground = QtGui.QColor(Qt.darkGray)


def DocumentationMetaclass(name, bases, dct):
    dct['__doc__'] = dct.get('__doc__','') + """

.. _delegate-%s:

.. image:: ../_static/delegates/%s_unselected_disabled.png
.. image:: ../_static/delegates/%s_unselected_editable.png

.. image:: ../_static/delegates/%s_selected_disabled.png
.. image:: ../_static/delegates/%s_selected_editable.png

"""%(name, name, name, name, name,)
    import inspect

    def add_field_attribute_item(a):
        """Add the name of a field attribute and a reference to its documentation
        to the docstring"""
        dct['__doc__'] = dct['__doc__'] + "\n * :ref:`%s <field-attribute-%s>`"%(arg, arg)

    if '__init__' in dct:
        dct['__doc__'] = dct['__doc__'] + 'Field attributes supported by the delegate : \n'
        args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['__init__'])
        for arg in args:
            if arg not in ['self', 'parent']:
                add_field_attribute_item(arg)

    if 'editor' in dct:
        dct['__doc__'] = dct['__doc__'] + '\n\nBy default, creates a %s as its editor.\n'%dct['editor'].__name__
        dct['__doc__'] = dct['__doc__'] + '\n.. image:: ../_static/editors/%s_editable.png'%dct['editor'].__name__ + '\n'
        dct['__doc__'] = dct['__doc__'] + '\nStatic attributes supported by this editor : \n'
        args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['editor'].__init__)
        for arg in args:
            if arg not in ['self', 'parent']:
                add_field_attribute_item(arg)

        if hasattr(dct['editor'], 'set_field_attributes'):
            dct['__doc__'] = dct['__doc__'] + '\n\nDynamic field attributes supported by the editor : \n'
            args, _varargs, _varkw,  _defaults = inspect.getargspec(dct['editor'].set_field_attributes)
            for arg in args:
                if arg not in ['self', 'parent']:
                    add_field_attribute_item(arg)

        dct['__doc__'] = dct['__doc__'] + '\n\n'

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
        assert editor != None
        assert isinstance(editor, (QtGui.QWidget,))
        if option.version != 5:
            editor.setAutoFillBackground(True)
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def sizeHint(self, option, index):
        return QtCore.QSize(self._width, self._height)

    #@QtCore.pyqtSlot()
    # not yet converted to new style sig slot because sender doesn't work
    # in certain versions of pyqt
    def commitAndCloseEditor(self):
        editor = self.sender()
        assert editor != None
        assert isinstance(editor, (QtGui.QWidget,))
        self.commitData.emit(editor)
        # if the editor emits editingFinished, this not necessarely means
        # the editor schould be closed, eg the float editor might have created
        # a calculator and that one would be destroyed if the editor is closed
        #self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)

    def setEditorData(self, editor, index):
        if not index.model():
            return
        value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
        field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
        index.model().data(index, Qt.ToolTipRole)
        editor.set_field_attributes(**field_attributes)
        editor.set_value(value)
        background_color = variant_to_pyobject(index.model().data(index, Qt.BackgroundRole))
        if background_color not in (None, ValueLoading):
            editor.set_background_color(background_color)
        tip = variant_to_pyobject(index.model().data(index, Qt.ToolTipRole))
        if tip not in (None, ValueLoading):
            editor.setCursor(QtGui.QCursor(Qt.WhatsThisCursor))
            editor.setToolTip(unicode(tip))
        else:
            editor.setToolTip('')
                
    def setModelData(self, editor, model, index):
        if isinstance(model, QtGui.QStandardItemModel):
            val = QtCore.QVariant(editor.get_value())
        else:
            val = create_constant_function(editor.get_value())
        model.setData(index, val)

    def paint_text(
        self, 
        painter, 
        option, 
        index, 
        text, 
        margin_left=0, 
        margin_right=0, 
        horizontal_align=Qt.AlignLeft,
        vertical_align=Qt.AlignVCenter
    ):
        """Paint unicode text into the given rect defined by option, and fill the rect with
        the background color
        :arg margin_left: additional margin to the left, to be used for icons or others
        :arg margin_right: additional margin to the right, to be used for icons or others"""

        field_attributes = variant_to_pyobject( index.model().data( index, Qt.UserRole ) )
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            background_color = field_attributes.get( 'background_color', None )
            prefix = field_attributes.get( 'prefix', None )
            suffix = field_attributes.get( 'suffix', None )
            
        rect = option.rect

        if( option.state & QtGui.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
            fontColor = option.palette.highlightedText().color()
        else:
            if editable:
                painter.fillRect(rect, background_color or option.palette.base() )
                fontColor = QtGui.QColor()
                fontColor.setRgb(0,0,0)
            else:
                painter.fillRect(rect, background_color or option.palette.window() )
                fontColor = QtGui.QColor()
                fontColor.setRgb(130,130,130)
        
        if prefix:
            text = '%s %s' % (unicode( prefix ).strip(), unicode( text ).strip() )
        if suffix:
            text = '%s %s' % (unicode( text ).strip(), unicode( suffix ).strip() )
            
        painter.setPen(fontColor.toRgb())
        painter.drawText(rect.x() + 2 + margin_left,
                         rect.y() + 2,
                         rect.width() - 4 - (margin_left + margin_right),
                         rect.height() - 4, # not -10, because the row might not be high enough for this
                         vertical_align | horizontal_align,
                         text)

    def render_ooxml( self, value ):
        """Generator for label text in Office Open XML representing this form"""
        yield '<w:r>'
        yield '  <w:t>%s</w:t>' % unicode(value)
        yield '</w:r>'
