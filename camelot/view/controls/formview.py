#  ============================================================================
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
#  ============================================================================

"""form view"""

import logging
logger = logging.getLogger( 'camelot.view.controls.formview' )

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui
from camelot.view.model_thread import model_function, post
from camelot.view.controls.view import AbstractView
from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

class ContextMenuAction(QtGui.QAction):

    default_icon = Icon( 'tango/16x16/categories/applications-system.png' )
    
    def __init__(self, parent, title, icon = None):
        """
        :param parent: the widget on which the context menu will be placed
        :param title: text displayed in the context menu
        :param icon: camelot.view.art.Icon object
        """
        super(ContextMenuAction, self).__init__(title, parent)
        self.icon = icon
        if self.icon:
            self.setIcon(self.icon.getQIcon())
        else:
            self.setIcon(self.default_icon.getQIcon())

class FormWidget( QtGui.QWidget ):
    
    changed_signal = QtCore.SIGNAL( 'changed()' )
    
    def __init__(self, admin):
        QtGui.QWidget.__init__(self)
        self._admin = admin
        self._widget_mapper = QtGui.QDataWidgetMapper()
        self._widget_layout = QtGui.QHBoxLayout()
        self._widget_layout.setSpacing( 0 )
        self._widget_layout.setMargin( 0 )
        self._index = 0
        self._model = None
        self._form = None
        self._columns = None
        self._delegate = None
        self.setLayout( self._widget_layout )
        # define context menu and resp. action
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        export_action = ContextMenuAction(self, _('Export form'))
        self.connect(export_action, QtCore.SIGNAL('triggered()'), self.export_form)
        self.addAction(export_action)

    def export_form(self):
        from camelot.view.export.word import open_stream_in_word
        
        def create_ooxml_export(row):
            print self._columns
            def ooxml_export():
                # TODO insert delegates
                delegates = {}
                for c in self._columns:
                    # FIXME incorrect
                    delegates[c[0]] = c[1]['delegate']
                
                
                obj = self._model._get_object(row)
                print ' - '.join(self._form.render_ooxml( obj, delegates ))
                # open_document_in_word(self._form.render_ooxml( obj, delegates ))
                
            return ooxml_export
                
        post( create_ooxml_export(self.get_index()) )

                        
    def get_model(self):
        return self._model
    
    def set_model(self, model):
        self._model = model
        sig = 'dataChanged(const QModelIndex &, const QModelIndex &)'
        self.connect( self._model, QtCore.SIGNAL( sig ), self._data_changed )
        self.connect( self._model, QtCore.SIGNAL( 'layoutChanged()' ), self._layout_changed )
        self.connect( self._model, self._model.item_delegate_changed_signal, self._item_delegate_changed )
        self._widget_mapper.setModel( model )
        
        def get_columns_and_form():
            return ( self._model.getColumns(), self._admin.get_form_display() )
      
        post( get_columns_and_form, self._set_columns_and_form )
        
    def clear_mapping(self):
        self._widget_mapper.clearMapping()
         
    def _data_changed( self, index_from, index_to ):
        #@TODO: only revert if this form is in the changed range
        self._widget_mapper.revert()
        self.emit(self.changed_signal)
        
    def _layout_changed(self):
        self._widget_mapper.revert()
        self.emit(self.changed_signal)
        
    def _item_delegate_changed(self):
        from camelot.view.controls.delegates.delegatemanager import DelegateManager
        self._delegate = self._model.getItemDelegate()
        assert self._delegate
        assert isinstance(self._delegate, DelegateManager)
        self._create_widgets()
                     
    def set_index(self, index):
        self._index = index
        self._widget_mapper.setCurrentIndex( self._index )
        
    def get_index(self):
        return self._widget_mapper.currentIndex()
        
    def submit(self):
        self._widget_mapper.submit()
                
    def to_first(self):
        self._widget_mapper.toFirst()
        self.emit(self.changed_signal)
        
    def to_last(self):
        self._widget_mapper.toLast()
        self.emit(self.changed_signal)
        
    def to_next(self):
        self._widget_mapper.toNext()
        self.emit(self.changed_signal)
        
    def to_previous(self):
        self._widget_mapper.toPrevious()
        self.emit(self.changed_signal)
        
    def _set_columns_and_form(self, columns_and_form ):
        self._columns, self._form = columns_and_form
        self._create_widgets()
        
    def _create_widgets( self ):
        """Create value and label widgets"""
        from camelot.view.controls.field_label import FieldLabel
        from camelot.view.controls.editors.wideeditor import WideEditor
        #
        # Dirty trick to make form views work during unit tests, since unit tests
        # have no event loop running, so the delegate will never be set, so we get
        # it and are sure it will be there if we are running without threads
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
        self._widget_mapper.setItemDelegate( self._delegate )
        option = QtGui.QStyleOptionViewItem()
        # set version to 5 to indicate the widget will appear on a
        # a form view and not on a table view
        option.version = 5
 
        #
        # this loop can take a while to complete, so processEvents is called regulary
        #    
        for i, ( field_name, field_attributes ) in enumerate( self._columns ):
#            if i%10==0:
#                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeSocketNotifiers, 100)
            model_index = self._model.index( self._index, i )
            hide_title = False
            if 'hide_title' in field_attributes:
                hide_title = field_attributes['hide_title']
            widget_label = None
            widget_editor = self._delegate.createEditor( self, option, model_index )
            if not hide_title:
                widget_label = FieldLabel( field_name, field_attributes['name'], field_attributes, self._admin )
                if not isinstance(widget_editor, WideEditor):
                    widget_label.setAlignment( Qt.AlignVCenter | Qt.AlignRight )
      
            # required fields font is bold
            if ( 'nullable' in field_attributes ) and \
               ( not field_attributes['nullable'] ):
                font = QtGui.QApplication.font()
                font.setBold( True )
                widget_label.setFont( font )
        
            assert widget_editor
            assert isinstance(widget_editor, QtGui.QWidget)
            
            self._widget_mapper.addMapping( widget_editor, i )
            widgets[field_name] = ( widget_label, widget_editor )
    
        self._widget_mapper.setCurrentIndex( self._index )
        self._widget_layout.insertWidget( 0, self._form.render( widgets, self ) )
        self._widget_layout.setContentsMargins( 7, 7, 7, 7 )
        
class FormView( AbstractView ):
    """A FormView is the combination of a FormWidget, possible actions and menu items
    
.. form_widget: The class to be used as a the form widget inside the form view

    """

    form_widget = FormWidget
    
    def __init__( self, title, admin, model, index ):
        AbstractView.__init__( self )
        layout = QtGui.QHBoxLayout()
        self._form = FormWidget(admin)
        self.model = model
        self.title_prefix = title
        self.admin = admin
        self.connect(self._form, FormWidget.changed_signal, self.update_title)
        self._form.set_model(model)
        self._form.set_index(index)
        layout.addWidget(self._form)
        self.change_title(title)
        self.closeAfterValidation = QtCore.SIGNAL( 'closeAfterValidation()' )
        self.setLayout( layout )
    
        if hasattr( admin, 'form_size' ) and admin.form_size:
            self.setMinimumSize( admin.form_size[0], admin.form_size[1] )
      
        self.validator = admin.create_validator( model )
        self.validate_before_close = True

        def getActions():
            return admin.get_form_actions( None )
      
        post( getActions, self.setActions )
        self.update_title()
    
    def update_title( self ):
  
        def get_title():
            obj = self.getEntity()
            return u'%s %s' % ( self.title_prefix, self.admin.get_verbose_identifier( obj ) )
      
        post( get_title, self.change_title )
    
    def getEntity( self ):
        return self.model._get_object( self._form.get_index() )
    
    def setActions( self, actions ):
        if actions:
            side_panel_layout = QtGui.QVBoxLayout()
            from camelot.view.controls.actionsbox import ActionsBox
            logger.debug( 'setting Actions for formview' )
            self.actions_widget = ActionsBox( self, self.getEntity )
            action_widgets = self.actions_widget.setActions( actions )
            for action_widget in action_widgets:
                self.connect( self._form, FormWidget.changed_signal, action_widget.changed )
                action_widget.changed()
            side_panel_layout.insertWidget( 1, self.actions_widget )
            side_panel_layout.addStretch()
            self.layout().addLayout(side_panel_layout)
      
    def viewFirst( self ):
        """select model's first row"""
        self._form.submit()
        self._form.to_first()
    
    def viewLast( self ):
        """select model's last row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        self._form.submit()
        self._form.to_last()
    
    def viewNext( self ):
        """select model's next row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        self._form.submit()
        self._form.to_next()
    
    def viewPrevious( self ):
        """select model's previous row"""
        # submit should not happen a second time, since then we don't want
        # the widgets data to be written to the model
        self._form.submit()
        self._form.to_previous()
    
    def showMessage( self, valid ):
        import sip
        if not valid:
            reply = self.validator.validityDialog( self._form.get_index(), self ).exec_()
            if reply == QtGui.QMessageBox.Discard:
            # clear mapping to prevent data being written again to the model,
            # then we reverted the row
                self._form.clear_mapping()
                self.model.revertRow( self._form.get_index() )
                self.validate_before_close = False
                self.emit( self.closeAfterValidation )
        else:
            self.validate_before_close = False
            if not sip.isdeleted( self ):
                self.emit( self.closeAfterValidation )
                    
    def validateClose( self ):
        logger.debug( 'validate before close : %s' % self.validate_before_close )
        if self.validate_before_close:
            # submit should not happen a second time, since then we don't
            # want the widgets data to be written to the model
            self._form.submit()
      
            def validate():
                return self.validator.isValid( self._form.get_index() )
        
            post( validate, self.showMessage )
            return False
      
        return True
    
    def closeEvent( self, event ):
        logger.debug( 'formview closed' )
        if self.validateClose():
            event.accept()
        else:
            event.ignore()
      
    @model_function
    def toHtml( self ):
        """generates html of the form"""
        from jinja import Environment
    
        def to_html( d = u'' ):
            """Jinja 1 filter to convert field values to their default html
            representation
            """
      
            def wrapped_in_table( env, context, value ):
                if isinstance( value, list ):
                    return u'<table><tr><td>' + \
                           u'</td></tr><tr><td>'.join( [unicode( e ) for e in value] ) + \
                           u'</td></tr></table>'
                return unicode( value )
        
            return wrapped_in_table
      
        entity = self.getEntity()
        fields = self.admin.get_fields()
        table = [dict( field_attributes = field_attributes,
                      value = getattr( entity, name ) )
                      for name, field_attributes in fields]
    
        context = {
          'title': self.admin.get_verbose_name(),
          'table': table,
        }
    
        from camelot.view.templates import loader
        env = Environment( loader = loader )
        env.filters['to_html'] = to_html
        tp = env.get_template( 'form_view.html' )
    
        return tp.render( context )
