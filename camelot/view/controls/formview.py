#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""form view"""

import functools
import logging

LOGGER = logging.getLogger('camelot.view.controls.formview')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.admin.action.application_action import Refresh
from camelot.admin.action.form_action import FormActionGuiContext
from camelot.view.model_thread import post
from camelot.view.controls.view import AbstractView
from camelot.view.controls.busy_widget import BusyWidget
from camelot.view import register

class FormEditors( object ):
    """A class that holds the editors used on a form
    """
    
    option = None
    bold_font = None
    
    def __init__( self, columns, widget_mapper, delegate, admin ):
        if self.option == None:
            self.option = QtGui.QStyleOptionViewItem()
            # set version to 5 to indicate the widget will appear on a
            # a form view and not on a table view
            self.option.version = 5
            self.bold_font = QtGui.QApplication.font()
            self.bold_font.setBold(True)
            
        self._admin = admin
        self._widget_mapper = widget_mapper
        self._field_attributes = dict()
        self._index = dict()
        for i, (field_name, field_attributes ) in enumerate( columns):
            self._field_attributes[field_name] = field_attributes
            self._index[field_name] = i
        
    def create_editor( self, field_name, parent ):
        """
        :return: a :class:`QtGuiQWidget` or None if field_name is unknown
        """
        index = self._index[field_name]
        model = self._widget_mapper.model()
        delegate = self._widget_mapper.itemDelegate()
        model_index = model.index( self._widget_mapper.currentIndex(), index )
        widget_editor = delegate.createEditor(
            parent,
            self.option,
            model_index
        )
        widget_editor.setObjectName('%s_editor'%field_name)
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
                field_attributes,
                self._admin
            )
            widget_label.setObjectName('%s_label'%field_name)
            if not isinstance(editor, WideEditor):
                widget_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        # required fields font is bold
        nullable = field_attributes.get( 'nullable', True )
        if not nullable:
            widget_label.setFont( self.bold_font )
        return widget_label
    
class FormWidget(QtGui.QWidget):
    """A form widget comes inside a form view or inside an embedded manytoone 
    editor"""

    changed_signal = QtCore.pyqtSignal( int )

    def __init__(self, parent, admin):
        QtGui.QWidget.__init__(self, parent)
        self._admin = admin
        widget_mapper = QtGui.QDataWidgetMapper(self)
        widget_mapper.setObjectName('widget_mapper')
        if self._admin.get_save_mode()=='on_leave':
            widget_mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)
        widget_layout = QtGui.QHBoxLayout()
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        self._index = 0
        self._model = None
        self._form = None
        self._columns = None
        self._delegate = None
        self.setLayout(widget_layout)

    def get_model(self):
        return self._model

    def set_model(self, model):
        self._model = model
        self._model.dataChanged.connect( self._data_changed )
        self._model.layoutChanged.connect( self._layout_changed )
        self._model.item_delegate_changed_signal.connect( self._item_delegate_changed )
        self._model.setObjectName( 'model' )
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.setModel( model )
            register.register( model, widget_mapper )

        def get_columns_and_form():
            return (self._model.getColumns(), self._admin.get_form_display())

        post(get_columns_and_form, self._set_columns_and_form)

    def clear_mapping(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.clearMapping()

    @QtCore.pyqtSlot( QtCore.QModelIndex, QtCore.QModelIndex  )
    def _data_changed(self, index_from, index_to):
        #@TODO: only revert if this form is in the changed range
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.revert()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    @QtCore.pyqtSlot()
    def _layout_changed(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.revert()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    @QtCore.pyqtSlot()
    def _item_delegate_changed(self):
        from camelot.view.controls.delegates.delegatemanager import \
            DelegateManager
        self._delegate = self._model.getItemDelegate()
        self._delegate.setObjectName('delegate')
        assert self._delegate != None
        assert isinstance(self._delegate, DelegateManager)
        self._create_widgets()

    def set_index(self, index):
        self._index = index
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.setCurrentIndex(self._index)

    def get_index(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            return widget_mapper.currentIndex()

    def submit(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.submit()

    def to_first(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.toFirst()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    def to_last(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.toLast()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    def to_next(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.toNext()
            self.changed_signal.emit( widget_mapper.currentIndex() )

    def to_previous(self):
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if widget_mapper:
            widget_mapper.toPrevious()
            self.changed_signal.emit( widget_mapper.currentIndex() )
        
    @QtCore.pyqtSlot(tuple)
    def _set_columns_and_form(self, columns_and_form ):
        self._columns, self._form = columns_and_form
        self._create_widgets()

    def _create_widgets(self):
        """Create value and label widgets"""
        #
        # Dirty trick to make form views work during unit tests, since unit
        # tests have no event loop running, so the delegate will never be set,
        # so we get it and are sure it will be there if we are running without
        # threads
        #
        if not self._delegate:
            self._delegate = self._model.getItemDelegate()
        #
        # end of dirty trick
        #
        # only if all information is available, we can start building the form
        if not (self._form and self._columns and self._delegate):
            return
        
        widgets = {}
        widget_mapper = self.findChild(QtGui.QDataWidgetMapper, 'widget_mapper' )
        if not widget_mapper:
            return
        LOGGER.debug( 'begin creating widgets' )
        widget_mapper.setItemDelegate(self._delegate)
        widgets = FormEditors( self._columns, widget_mapper, self._delegate, self._admin )
        widget_mapper.setCurrentIndex( self._index )
        LOGGER.debug( 'put widgets on form' )
        self.layout().insertWidget(0, self._form.render( widgets, self, True) )
        LOGGER.debug( 'done' )
        #self._widget_layout.setContentsMargins(7, 7, 7, 7)


class FormView(AbstractView):
    """A FormView is the combination of a FormWidget, possible actions and menu
    items

    .. form_widget: The class to be used as a the form widget inside the form
    view"""

    form_widget = FormWidget

    def __init__(self, title, admin, model, index, parent = None):
        AbstractView.__init__( self, parent )

        layout = QtGui.QVBoxLayout()
        layout.setSpacing( 1 )
        layout.setMargin( 1 )
        layout.setObjectName( 'layout' )
        form_and_actions_layout = QtGui.QHBoxLayout()
        form_and_actions_layout.setObjectName('form_and_actions_layout')
        layout.addLayout( form_and_actions_layout )
            
        self.model = model
        self.admin = admin
        self.title_prefix = title
        self.refresh_action = Refresh()

        form = FormWidget(self, admin)
        form.setObjectName( 'form' )
        form.changed_signal.connect( self.update_title )
        form.set_model(model)
        form.set_index(index)
        form_and_actions_layout.addWidget(form)

        self.gui_context = FormActionGuiContext()
        self.gui_context.workspace = self
        self.gui_context.admin = admin
        self.gui_context.view = self
        self.gui_context.widget_mapper = self.findChild( QtGui.QDataWidgetMapper, 
                                                         'widget_mapper' )
        self.setLayout( layout )

        self.change_title(title)

        if hasattr(admin, 'form_size') and admin.form_size:
            self.setMinimumSize(admin.form_size[0], admin.form_size[1])

        self.accept_close_event = False

        get_actions = admin.get_form_actions
        post( functools.update_wrapper( functools.partial( get_actions, 
                                                           None ),
                                        get_actions ),
              self.set_actions )

        get_toolbar_actions = admin.get_form_toolbar_actions
        post( functools.update_wrapper( functools.partial( get_toolbar_actions, 
                                                           Qt.TopToolBarArea ),
                                        get_toolbar_actions ),
              self.set_toolbar_actions )
                
    @QtCore.pyqtSlot()
    def refresh(self):
        """Refresh the data in the current view"""
        self.model.refresh()
    
    def _get_title( self, index ):
        obj = self.model._get_object( index )
        return u'%s %s' % (
            self.title_prefix,
            self.admin.get_verbose_identifier(obj)
        )
            
    @QtCore.pyqtSlot( int )
    def update_title(self, current_index ):
        post( self._get_title, self.change_title, args=(current_index,) )

    @QtCore.pyqtSlot(list)
    def set_actions(self, actions):
        form = self.findChild(QtGui.QWidget, 'form' )
        layout = self.findChild(QtGui.QLayout, 'form_and_actions_layout' )
        if actions and form and layout:
            side_panel_layout = QtGui.QVBoxLayout()
            from camelot.view.controls.actionsbox import ActionsBox
            LOGGER.debug('setting Actions for formview')
            actions_widget = ActionsBox( parent = self, 
                                         gui_context = self.gui_context )
            actions_widget.setObjectName('actions')
            actions_widget.set_actions( actions )
            side_panel_layout.addWidget( actions_widget )
            side_panel_layout.addStretch()
            layout.addLayout( side_panel_layout )
            
    @QtCore.pyqtSlot(list)
    def set_toolbar_actions(self, actions):
        layout = self.findChild( QtGui.QLayout, 'layout' )
        if layout and actions:
            toolbar = QtGui.QToolBar()
            for action in actions:
                qaction = action.render( self.gui_context, toolbar )
                qaction.triggered.connect( self.action_triggered )
                toolbar.addAction( qaction )
            toolbar.addWidget( BusyWidget() )
            layout.insertWidget( 0, toolbar, 0, Qt.AlignTop )

    @QtCore.pyqtSlot( bool )
    def action_triggered( self, _checked = False ):
        action_action = self.sender()
        action_action.action.gui_run( self.gui_context )
        
    def to_first(self):
        """select model's first row"""
        form = self.findChild(QtGui.QWidget, 'form' )
        if form:
            form.submit()
            form.to_first()

    def to_last(self):
        """select model's last row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        form = self.findChild(QtGui.QWidget, 'form' )
        if form:
            form.submit()
            form.to_last()

    def to_next(self):
        """select model's next row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        form = self.findChild(QtGui.QWidget, 'form' )
        if form:
            form.submit()
            form.to_next()

    def to_previous(self):
        """select model's previous row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        form = self.findChild(QtGui.QWidget, 'form' )
        if form:
            form.submit()
            form.to_previous()

    @QtCore.pyqtSlot()
    def validate_close( self ):
        self.admin.form_close_action.gui_run( self.gui_context )
        
    def close_view( self, accept ):
        self.accept_close_event = accept
        if accept == True:
            # clear mapping to prevent data being written again to the model,
            # when the underlying object would be reverted
            form = self.findChild( QtGui.QWidget, 'form' )
            if form != None:
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
