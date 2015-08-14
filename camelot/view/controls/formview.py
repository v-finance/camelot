#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""form view"""

import logging

LOGGER = logging.getLogger('camelot.view.controls.formview')

from ...core.qt import QtGui, QtCore, QtWidgets, Qt, py_to_variant, is_deleted

from camelot.admin.action.application_action import Refresh
from camelot.admin.action.form_action import FormActionGuiContext
from camelot.view.model_thread import post
from camelot.view.controls.view import AbstractView
from camelot.view.controls.busy_widget import BusyWidget
from camelot.view import register
from .delegates.delegatemanager import DelegateManager

class FormEditors( object ):
    """A class that holds the editors used on a form
    """
    
    option = None
    bold_font = None
    
    def __init__( self, columns, widget_mapper, admin ):
        if self.option == None:
            self.option = QtGui.QStyleOptionViewItem()
            # set version to 5 to indicate the widget will appear on a
            # a form view and not on a table view
            self.option.version = 5
            
        self._admin = admin
        self._widget_mapper = widget_mapper
        self._field_attributes = dict()
        self._index = dict()
        for i, (field_name, field_attributes ) in enumerate( columns):
            self._field_attributes[field_name] = field_attributes
            self._index[field_name] = i
        
    def create_editor( self, field_name, parent ):
        """
        :return: a :class:`QtWidgets.QWidget` or `None` if field_name is unknown
        """
        index = self._index[field_name]
        model = self._widget_mapper.model()
        delegate = self._widget_mapper.itemDelegate()
        model_index = model.createIndex(self._widget_mapper.currentIndex(),
                                        index, 0)
        widget_editor = delegate.createEditor(
            parent,
            self.option,
            model_index
        )
        widget_editor.setObjectName('%s_editor'%field_name)
        stretch = self._field_attributes[field_name].get('stretch', 1)
        widget_editor.setProperty('stretch', py_to_variant(stretch))
        delegate.setEditorData( widget_editor, model_index )
        self._widget_mapper.addMapping( widget_editor, index )
        return widget_editor
    
    def create_label( self, field_name, editor, parent ):
        from camelot.view.controls.field_label import FieldLabel
        from camelot.view.controls.editors.wideeditor import WideEditor
        field_attributes = self._field_attributes[field_name]
        hide_title = field_attributes.get( 'hide_title', False )
        widget_label = None
        if not hide_title:
            widget_label = FieldLabel(
                field_name,
                field_attributes['name'],
                self._admin
            )
            widget_label.setObjectName('%s_label'%field_name)
            if not isinstance(editor, WideEditor):
                widget_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            editor.set_label(widget_label)
        return widget_label
    
class FormWidget(QtWidgets.QWidget):
    """A form widget comes inside a form view"""

    changed_signal = QtCore.qt_signal( int )

    def __init__(self, admin, model, form_display, columns, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self._admin = admin
        widget_mapper = QtWidgets.QDataWidgetMapper(self)
        widget_mapper.setObjectName('widget_mapper')
        widget_mapper.setItemDelegate(DelegateManager(columns, parent=self))
        widget_mapper.currentIndexChanged.connect( self.current_index_changed )
        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        self._index = 0
        self._form = None
        self._columns = None
        self.setLayout(widget_layout)
        self.set_model(model)
        self.create_widgets(widget_mapper, columns, form_display, admin)

    def set_model(self, model):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if model is not None:
            model.dataChanged.connect(self._data_changed)
            model.layoutChanged.connect(self._layout_changed)
            model.modelReset.connect(self._model_reset)
            model.rowsInserted.connect(self._layout_changed)
            model.rowsRemoved.connect(self._layout_changed)
            if widget_mapper is not None:
                widget_mapper.setModel( model )
                register.register( model, widget_mapper )
                
    def get_model(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if widget_mapper is not None:
            return widget_mapper.model()

    def clear_mapping(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if widget_mapper:
            widget_mapper.clearMapping()

    @QtCore.qt_slot()
    def _model_reset(self):
        self._layout_changed()
            
    @QtCore.qt_slot( QtCore.QModelIndex, QtCore.QModelIndex  )
    def _data_changed(self, index_from, index_to):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper is not None:
            current_index = widget_mapper.currentIndex()
            if (current_index >= index_from.row()) and (current_index <= index_to.row()):
                self.changed_signal.emit(current_index)

    @QtCore.qt_slot()
    def _layout_changed(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper is not None:
            # after a layout change, the row we want to display might be there
            if widget_mapper.currentIndex() < 0:
                widget_mapper.setCurrentIndex(self._index)
            widget_mapper.revert()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    @QtCore.qt_slot(int)
    def current_index_changed( self, index ):
        self.changed_signal.emit( index )
        
    def set_index(self, index):
        self._index = index
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.setCurrentIndex(self._index)

    def get_index(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            return widget_mapper.currentIndex()

    def submit(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.submit()

    def create_widgets(self, widget_mapper, columns, form_display, admin):
        """Create value and label widgets"""
        LOGGER.debug( 'begin creating widgets' )
        widgets = FormEditors( columns, widget_mapper, admin )
        widget_mapper.setCurrentIndex( self._index )
        LOGGER.debug( 'put widgets on form' )
        self.layout().insertWidget(0, form_display.render( widgets, self, True) )
        # give focus to the first editor in the form that can receive focus
        for i in range(10):
            first_widget = widget_mapper.mappedWidgetAt(i)
            if first_widget is None:
                break
            if first_widget.focusPolicy() != Qt.NoFocus:
                first_widget.setFocus(Qt.PopupFocusReason)
                break
        LOGGER.debug( 'done' )

class FormView(AbstractView):
    """A FormView is the combination of a FormWidget, possible actions and menu
    items

    .. form_widget: The class to be used as a the form widget inside the form
    view"""

    form_widget = FormWidget

    def __init__(self, title, admin, model, form_display, columns,
                 index, parent = None):
        AbstractView.__init__( self, parent )

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing( 1 )
        layout.setContentsMargins( 1, 1, 1, 1 )
        layout.setObjectName( 'layout' )
        form_and_actions_layout = QtWidgets.QHBoxLayout()
        form_and_actions_layout.setObjectName('form_and_actions_layout')
        layout.addLayout( form_and_actions_layout )
            
        self.model = model
        self.admin = admin
        self.title_prefix = title
        self.refresh_action = Refresh()

        form = FormWidget(admin=admin, model=model, form_display=form_display,
                          columns=columns, parent=self)
        form.setObjectName( 'form' )
        form.changed_signal.connect( self.update_title )
        form.set_index(index)
        form_and_actions_layout.addWidget(form)

        self.gui_context = FormActionGuiContext()
        self.gui_context.workspace = self
        self.gui_context.admin = admin
        self.gui_context.view = self
        self.gui_context.widget_mapper = self.findChild( QtWidgets.QDataWidgetMapper, 
                                                         'widget_mapper' )
        self.setLayout( layout )
        self.change_title(title)

        if hasattr(admin, 'form_size') and admin.form_size:
            self.setMinimumSize(admin.form_size[0], admin.form_size[1])

        self.accept_close_event = False

    @QtCore.qt_slot()
    def refresh(self):
        """Refresh the data in the current view"""
        self.model.refresh()
    
    def _get_title( self, index ):
        verbose_identifier = ''
        for obj in self.model.get_slice(index, index+1):
            if obj is not None:
                verbose_identifier = self.admin.get_verbose_identifier(obj)
        return u'%s %s' % (
            self.title_prefix,
            verbose_identifier
        )
            
    @QtCore.qt_slot( int )
    def update_title(self, current_index ):
        if current_index >= 0:
            post( self._get_title, self.change_title, args=(current_index,) )
        else:
            self.change_title(u'')

    @QtCore.qt_slot(list)
    def set_actions(self, actions):
        form = self.findChild(QtWidgets.QWidget, 'form' )
        layout = self.findChild(QtGui.QLayout, 'form_and_actions_layout' )
        if actions and form and layout:
            side_panel_layout = QtWidgets.QVBoxLayout()
            from camelot.view.controls.actionsbox import ActionsBox
            LOGGER.debug('setting Actions for formview')
            actions_widget = ActionsBox( parent = self, 
                                         gui_context = self.gui_context )
            actions_widget.setObjectName('actions')
            actions_widget.set_actions( actions )
            side_panel_layout.addWidget( actions_widget )
            side_panel_layout.addStretch()
            layout.addLayout( side_panel_layout )
            
    @QtCore.qt_slot(list)
    def set_toolbar_actions(self, actions):
        layout = self.findChild( QtGui.QLayout, 'layout' )
        if layout and actions:
            toolbar = QtWidgets.QToolBar()
            for action in actions:
                qaction = action.render( self.gui_context, toolbar )
                qaction.triggered.connect( self.action_triggered )
                toolbar.addAction( qaction )
            toolbar.addWidget( BusyWidget() )
            layout.insertWidget( 0, toolbar, 0, Qt.AlignTop )
            # @todo : this show is needed on OSX or the form window
            # is hidden after the toolbar is added, maybe this can
            # be solved using windowflags, since this causes some
            # flicker
            self.show()

    @QtCore.qt_slot( bool )
    def action_triggered( self, _checked = False ):
        action_action = self.sender()
        action_action.action.gui_run( self.gui_context )

    @QtCore.qt_slot()
    def validate_close( self ):
        self.admin.form_close_action.gui_run( self.gui_context )
        
    def close_view( self, accept ):
        self.accept_close_event = accept
        if (accept == True) and not is_deleted(self):
            # clear mapping to prevent data being written again to the model,
            # when the underlying object would be reverted
            form = self.findChild( QtWidgets.QWidget, 'form' )
            if form is not None:
                form.clear_mapping()
        self.close()

    def closeEvent(self, event):
        if self.accept_close_event == True:
            event.accept()
        else:
            # make sure the next closeEvent is sent after this one
            # is processed
            QtCore.QTimer.singleShot( 0, self.validate_close )
            event.ignore()

