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

"""form view"""

import logging

LOGGER = logging.getLogger('camelot.view.controls.formview')

from ...core.qt import (QtCore, QtWidgets, Qt, py_to_variant, is_deleted,
                        variant_to_py)

from camelot.admin.action.application_action import Refresh
from camelot.admin.action.form_action import FormActionGuiContext
from camelot.view.proxy.collection_proxy import VerboseIdentifierRole
from camelot.view.controls.view import AbstractView
from camelot.view.controls.busy_widget import BusyWidget
from .delegates.delegatemanager import DelegateManager

class FormEditors(QtCore.QObject):

    option = None
    bold_font = None

    def __init__(self, parent, columns, admin):
        """
        A class that holds the editors used on a form

        :parent: should be a QObject which has a widget mapper as its child

        """
        QtCore.QObject.__init__(self, parent)
        assert isinstance(parent, QtCore.QObject)
        assert parent.findChild(QtWidgets.QDataWidgetMapper)
        if self.option is None:
            self.option = QtWidgets.QStyleOptionViewItem()
            # set version to 5 to indicate the widget will appear on a
            # a form view and not on a table view
            self.option.version = 5

        self._admin = admin
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
        widget_mapper = self.parent().findChild(QtWidgets.QDataWidgetMapper)
        model = widget_mapper.model()
        delegate = widget_mapper.itemDelegate()
        model_index = model.createIndex(widget_mapper.currentIndex(),
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
        widget_mapper.addMapping( widget_editor, index )
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
                self._admin,
                parent,
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
        widget_mapper = QtWidgets.QDataWidgetMapper(self)
        widget_mapper.setObjectName('widget_mapper')
        widget_mapper.setItemDelegate(DelegateManager(columns, parent=self))
        widget_mapper.currentIndexChanged.connect( self.current_index_changed )
        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        self._index = 0
        self.setLayout(widget_layout)
        self.set_model(model)
        self.create_widgets(widget_mapper, columns, form_display, admin)

    def set_model(self, model):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if model is not None:
            model.headerDataChanged.connect(self._header_data_changed)
            model.layoutChanged.connect(self._layout_changed)
            model.modelReset.connect(self._layout_changed)
            model.rowsInserted.connect(self._layout_changed)
            model.rowsRemoved.connect(self._layout_changed)
            model.setParent(self)
            if widget_mapper is not None:
                widget_mapper.setModel(model)

    def get_model(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if widget_mapper is not None:
            return widget_mapper.model()

    def clear_mapping(self):
        widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper')
        if widget_mapper:
            widget_mapper.clearMapping()

    # @QtCore.qt_slot(int, int, int)
    def _header_data_changed(self, orientation, first, last):
        if orientation == Qt.Vertical:
            widget_mapper = self.findChild(QtWidgets.QDataWidgetMapper, 'widget_mapper' )
            if widget_mapper is not None:
                current_index = widget_mapper.currentIndex()
                if (current_index >= first) and (current_index <= last):
                    self.changed_signal.emit(current_index)

    
    @QtCore.qt_slot() # for model reset
    @QtCore.qt_slot(QtCore.QModelIndex, int, int) # for rows inserted/removed
    def _layout_changed(self, index=None, start=None, end=None):
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
        widgets = FormEditors(self, columns, admin)
        widget_mapper.setCurrentIndex( self._index )
        LOGGER.debug( 'put widgets on form' )
        self.layout().insertWidget(0, form_display.render( widgets, self, True) )
        ## give focus to the first editor in the form that can receive focus
        # this results in weird behavior on Mac, where the editor get focus
        # from the OS and then immediately gets input
        #for i in range(10):
            #first_widget = widget_mapper.mappedWidgetAt(i)
            #if first_widget is None:
                #break
            #if first_widget.focusPolicy() != Qt.NoFocus:
                #first_widget.setFocus(Qt.PopupFocusReason)
                #break
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

    @QtCore.qt_slot( int )
    def update_title(self, current_index ):
        verbose_identifier = variant_to_py(self.model.headerData(
            current_index, Qt.Vertical, VerboseIdentifierRole
        ))
        if verbose_identifier is not None:
            self.change_title(u'%s %s'%(self.title_prefix,verbose_identifier))
        else:
            self.change_title(u'')

    @QtCore.qt_slot(list)
    def set_actions(self, actions):
        form = self.findChild(QtWidgets.QWidget, 'form' )
        layout = self.findChild(QtWidgets.QLayout, 'form_and_actions_layout' )
        if actions and form and layout:
            side_panel_layout = QtWidgets.QVBoxLayout()
            from camelot.view.controls.actionsbox import ActionsBox
            LOGGER.debug('setting Actions for formview')
            actions_widget = ActionsBox(parent=self)
            actions_widget.setObjectName('actions')
            for action in actions:
                actions_widget.layout().addWidget(
                    self.render_action(action, actions_widget)
                )
            side_panel_layout.addWidget(actions_widget)
            side_panel_layout.addStretch()
            layout.addLayout(side_panel_layout)

    @QtCore.qt_slot(list)
    def set_toolbar_actions(self, actions):
        layout = self.findChild( QtWidgets.QLayout, 'layout' )
        if layout and actions:
            toolbar = QtWidgets.QToolBar()
            toolbar.setIconSize(QtCore.QSize(16,16))
            for action in actions:
                toolbar.addAction(self.render_action(action, toolbar))
            toolbar.addWidget( BusyWidget() )
            layout.insertWidget( 0, toolbar, 0, Qt.AlignTop )
            # @todo : this show is needed on OSX or the form window
            # is hidden after the toolbar is added, maybe this can
            # be solved using windowflags, since this causes some
            # flicker
            self.show()

    @QtCore.qt_slot()
    def validate_close( self ):
        self.admin.form_close_action.gui_run( self.gui_context )

    def close_view( self, accept ):
        self.accept_close_event = accept
        if is_deleted(self):
            return
        if (accept == True):
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


