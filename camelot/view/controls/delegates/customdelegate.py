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

import six

from ....core.qt import (QtGui, QtCore, QtWidgets, Qt,
                         py_to_variant, variant_to_py)
from ....core.item_model import ProxyDict, FieldAttributesRole, PreviewRole

from camelot.view.proxy import ValueLoading


def DocumentationMetaclass(name, bases, dct):
    dct['__doc__'] = (dct.get('__doc__') or '') + """

.. _delegate-%s:

.. image:: /_static/delegates/%s_unselected_disabled.png
.. image:: /_static/delegates/%s_unselected_editable.png

.. image:: /_static/delegates/%s_selected_disabled.png
.. image:: /_static/delegates/%s_selected_editable.png

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
        
        row_separator = '+' + '-'*40 + '+' + '-'*90 + '+'
        row_format = """| %-38s | %-88s |"""
        states = {'editable':['editable=True'], 
                  'disabled':['editable=False'],
                  'editable_tooltip':['editable=True', "tooltip='tooltip'"], 
                  'disabled_tooltip':['editable=False', "tooltip='tooltip'"],
                  'editable_background_color':['editable=True', 'background_color=ColorScheme.green'], 
                  'disabled_background_color':['editable=False', 'background_color=ColorScheme.green']                  
                  }

        dct['__doc__'] = dct['__doc__'] + '\n\nBy default, creates a %s as its editor.\n\n'%dct['editor'].__name__
        dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        dct['__doc__'] = dct['__doc__'] + row_format%('**Field Attributes**', '**Editor**') + '\n'
        dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        for state, attrs in six.iteritems(states):
            for i,attr in enumerate(attrs):
                if i==0:
                    image = '.. image:: /_static/editors/%s_%s.png'%(dct['editor'].__name__, state)
                else:
                    image = ''
                dct['__doc__'] = dct['__doc__'] + row_format%(attr, image) + '\n'
            dct['__doc__'] = dct['__doc__'] + row_separator + '\n'
        
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

color_groups = {True: QtGui.QPalette.Inactive,
                False: QtGui.QPalette.Disabled}

class CustomDelegate(QtWidgets.QItemDelegate):
    """Base class for implementing custom delegates.

    .. attribute:: editor

    class attribute specifies the editor class that should be used

    """

    editor = None
    horizontal_align = Qt.AlignLeft

    def __init__(self, parent=None, editable=True, **kwargs):
        """:param parent: the parent object for the delegate
        :param editable: a boolean indicating if the field associated to the delegate
        is editable

        """
        super( CustomDelegate, self ).__init__(parent)
        self.editable = editable
        self.kwargs = kwargs
        self._font_metrics = QtGui.QFontMetrics(QtWidgets.QApplication.font())
        self._height = self._font_metrics.lineSpacing() + 10
        self._width = self._font_metrics.averageCharWidth() * 20

    @classmethod
    def get_standard_item(cls, locale, value, field_attributes_values):
        """
        This method is used by the proxy to convert the value of a field
        to the data for the standard item model.  The result of this call can be
        used by the methods of the delegate.

        :param locale: the `QLocale` to be used to display locale dependent values
        :param value: the value of the field on the object
        :param field_attributes_values: the values of the field attributes on the
           object
        
        :return: a `QStandardItem` object
        """
        item = QtGui.QStandardItem()
        item.setData(py_to_variant(value), Qt.EditRole)
        item.setData(py_to_variant(ProxyDict(field_attributes_values)),
                     FieldAttributesRole)
        item.setData(py_to_variant(field_attributes_values.get('tooltip')),
                     Qt.ToolTipRole)
        item.setData(py_to_variant(field_attributes_values.get('background_color')),
                     Qt.BackgroundRole)
        return item

    def createEditor(self, parent, option, index):
        """
        :param option: use an option with version 5 to indicate the widget
        will be put onto a form
        """

        editor = self.editor(parent, editable = self.editable, option = option, **self.kwargs)
        assert editor != None
        assert isinstance(editor, QtWidgets.QWidget)
        if option.version != 5:
            editor.setAutoFillBackground(True)
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def sizeHint(self, option, index):
        return QtCore.QSize(self._width, self._height)

    #@QtCore.qt_slot()
    # not yet converted to new style sig slot because sender doesn't work
    # in certain versions of pyqt
    def commitAndCloseEditor(self):
        editor = self.sender()
        assert editor != None
        assert isinstance(editor, QtWidgets.QWidget)
        self.commitData.emit(editor)
        # * Closing the editor results in the calculator not working
        # * not closing the editor results in the virtualaddresseditor not
        #   getting closed always
        #self.closeEditor.emit( editor, QtWidgets.QAbstractItemDelegate.NoHint )

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        value = variant_to_py(index.model().data(index, Qt.EditRole))
        field_attributes = variant_to_py(index.data(Qt.UserRole)) or dict()
        # ok i think i'm onto something, dynamically set tooltip doesn't change
        # Qt model's data for Qt.ToolTipRole
        # but i wonder if we should make the detour by Qt.ToolTipRole or just
        # get our tooltip from field_attributes
        # (Nick G.): Avoid 'None' being set as tooltip.
        if field_attributes.get('tooltip'):
            editor.setToolTip( six.text_type( field_attributes.get('tooltip', '') ) )
        #
        # first set the field attributes, as these may change the 'state' of the
        # editor to properly display and hold the value, eg 'precision' of a 
        # float might be changed
        #
        editor.set_field_attributes(**field_attributes)
        editor.set_value(value)

    def setModelData(self, editor, model, index):
        model.setData(index, py_to_variant(editor.get_value()))

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_py(index.model().data(index, PreviewRole))
        self.paint_text(painter, option, index, value or six.text_type())
        painter.restore()

    def paint_text(
        self,
        painter,
        option,
        index,
        text,
        margin_left=0,
        margin_right=0,
        horizontal_align=None,
        vertical_align=Qt.AlignVCenter
    ):
        """Paint unicode text into the given rect defined by option, and fill the rect with
        the background color
        :arg margin_left: additional margin to the left, to be used for icons or others
        :arg margin_right: additional margin to the right, to be used for icons or others"""

        rect = option.rect
        # prevent text being centered if the height of the cell increases beyond multiple
        # lines of text
        if rect.height() > 2 * self._height:
            vertical_align = Qt.AlignTop

        field_attributes = variant_to_py(index.data(Qt.UserRole))
        if field_attributes != ValueLoading:
            editable = field_attributes.get( 'editable', True )
            background_color = field_attributes.get( 'background_color', None )
            prefix = field_attributes.get( 'prefix', None )
            suffix = field_attributes.get( 'suffix', None )

        if( option.state & QtWidgets.QStyle.State_Selected ):
            painter.fillRect(option.rect, option.palette.highlight())
            fontColor = option.palette.highlightedText().color()
        else:
            color_group = color_groups[editable]
            painter.fillRect(rect, background_color or option.palette.brush(color_group, QtGui.QPalette.Base) )
            fontColor = option.palette.color(color_group, QtGui.QPalette.Text)
        

        if prefix:
            text = '%s %s' % (six.text_type( prefix ).strip(), six.text_type( text ).strip() )
        if suffix:
            text = '%s %s' % (six.text_type( text ).strip(), six.text_type( suffix ).strip() )

        painter.setPen(fontColor.toRgb())
        painter.drawText(rect.x() + 2 + margin_left,
                         rect.y() + 2,
                         rect.width() - 4 - (margin_left + margin_right),
                         rect.height() - 4, # not -10, because the row might not be high enough for this
                         vertical_align | (horizontal_align or self.horizontal_align),
                         text)




