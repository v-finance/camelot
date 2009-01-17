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

"""
@TODO: rewrite docstring

Admin classes, specify how objects should be rendered in the gui

An admin class has class attributes like 'list_display' which contains the
columns that should be displayed in a list view (again, see Django)

So this 'list_display' attribute can be overwritten in the Admin class for each
model.

But for the gui generation itself, we don't use the class attributes, but we
use methods, like 'getColumns', that way, we can make the gui very specific, on
the context
"""

import os
import sys
import logging
logger = logging.getLogger('camelot.view.elixir_admin')

import datetime

import sqlalchemy.types
import camelot.types
from model_thread import gui_function
from model_thread import model_function
import settings

_ = lambda x: x

class EntityAdmin(object):
  name = None
  list_display = []
  fields = []
  form = [] #DEPRECATED
  form_display = []
  # list of field_names to filter on, if the field name is a one2many,
  # many2one or many2many field, the field name should be followed by a
  # field name of the related entity, eg : 'organization.name'
  list_filter = []
  list_charts = []
  list_actions = []
  list_size = (700,500)
  form_size = (700,500)
  form_actions = []
  form_title_column = None
  field_attributes = {}

  def __init__(self, app_admin, entity):
    """
    @param app_admin: the application admin object for this application
    @param entity: the entity class for which this admin instance is to be used
    """
    from camelot.view.remote_signals import get_signal_handler
    self.app_admin = app_admin
    self.rsh = get_signal_handler()
    if entity:
      from model_thread import get_model_thread
      self.entity = entity
      self.mt = get_model_thread()
    #
    # caches to prevent recalculation of things
    #
    self.__field_attributes = dict()

  def __str__(self):
    return 'Admin %s' % str(self.entity.__name__)

  def getName(self):
    return (self.name or self.entity.__name__)

  def getModelThread(self):
    return self.mt

  @model_function
  def getFormActions(self, entity):
    return self.form_actions

  def getRelatedEntityAdmin(self, entity):
    """
    Get the related admin class for an entity, optionally specify for which
    field of this admin's entity
    """
    related_admin = self.app_admin.getEntityAdmin(entity)
    if not related_admin:
      logger.warn('no related admin found for %s'%(entity.__name__))
    return related_admin

  @model_function
  def getSubclasses(self):
    """
    Return admin objects for the subclasses of the Entity represented by this
    admin object
    """
    from elixir import entities
    return [e.Admin(self.app_admin, e)
            for e in entities
            if (issubclass(e, (self.entity, )) and 
                hasattr(e, 'Admin') and
                e!=self.entity)]

  @model_function
  def getFieldAttributes(self, field_name):
    """
    Get the attributes needed to visualize the field field_name
    @param field_name : the name of the field
    @return: a dictionary of attributes needed to visualize the field, those
    attributes can be:
     * python_type : the corresponding python type of the object
     * editable : bool specifying wether the user can edit this field
     * widget : which widget to be used to render the field
     * ...
    """
    try:
      return self.__field_attributes[field_name]
    except KeyError:
      from camelot.model.i18n import tr
      from sqlalchemy import orm
      from sqlalchemy.exceptions import InvalidRequestError
      from field_attributes import _sqlalchemy_to_python_type_
      default = lambda x: dict(python_type=str,
                               length=None,
                               editable=False,
                               nullable=True,
                               widget='str')
      attributes = default(field_name)
      mapper = orm.class_mapper(self.entity)
  
      def get_entity_admin(target):
        try:
          admin_class = self.field_attributes[field_name]['admin']
          return admin_class(self.app_admin, target)
        except KeyError:
          return self.getRelatedEntityAdmin(target)
  
      try:
        property = mapper.get_property(field_name, resolve_synonyms=True)
        if isinstance(property, orm.properties.ColumnProperty):
          type = property.columns[0].type
          python_type = _sqlalchemy_to_python_type_.get(type.__class__, default)
          attributes = python_type(type)
          attributes['nullable'] = property.columns[0].nullable 
          attributes['default'] = property.columns[0].default
        elif isinstance(property, orm.properties.PropertyLoader):
          target = property._get_target_class()
          foreign_keys = property.foreign_keys
          if property.direction == orm.sync.ONETOMANY:
            attributes = dict(python_type=list,
                              length=None,
                              editable=True,
                              nullable=True,
                              widget='one2many',
                              create_inline=False,
                              backref=property.backref.key,
                              admin=get_entity_admin(target))
          elif property.direction == orm.sync.MANYTOONE:
            attributes = dict(python_type=str,
                              length=None,
                              editable=True,
                              #@todo: take into account all foreign keys instead of only the first one
                              nullable=foreign_keys[0].nullable,
                              widget='many2one',
                              admin=get_entity_admin(target))
          elif property.direction == orm.sync.MANYTOMANY:
            attributes = dict(python_type=list,
                              length=None,
                              editable=True,
                              nullable=True,
                              widget='one2many',
                              admin=get_entity_admin(target))
          else:
            raise Exception('PropertyLoader has unknown direction')
      except InvalidRequestError:
        """
        If the field name is not a property of the mapper, then use the default
        stuff
        """
        pass
      attributes.update(dict(blank=True,
                             validator_list=[],
                             name=field_name.replace('_', ' ').capitalize()))
      try:
        for k, v in self.field_attributes[field_name].items():
          if k!='admin':
            attributes[k] = v
      except KeyError:
        pass
      attributes['name'] = tr(attributes['name'])
      self.__field_attributes[field_name] = attributes
      return attributes

  @model_function
  def getColumns(self):
    """
    The columns to be displayed in the list view, returns a list of pairs of
    the name of the field and its attributes needed to display it properly

    @return: [(field_name,
              {'widget': widget_type,
               'editable': True or False,
               'blank': True or False,
               'validator_list':[...],
               'name':'Field name'}),
             ...]
    """
    return [(field, self.getFieldAttributes(field))
            for field in self.list_display]

  @model_function
  def getFields(self):
    if self.form or self.form_display:
      fields = self.getForm().get_fields()
    elif self.fields:
      fields = self.fields
    else:
      fields = self.list_display
    fields_and_attributes =  [(field, self.getFieldAttributes(field)) for field in fields]
    return fields_and_attributes
  
  def getForm(self):
    from forms import Form, structure_to_form
    if self.form or self.form_display:
      return structure_to_form(self.form or self.form_display)
    return Form([f for f, a in self.getFields()])    

  @model_function
  def getListCharts(self):
    return self.list_charts

  @model_function
  def getFilters(self):
    """Return the filters applicable for these entities each filter is 

    @return: [(filter_name, [(option_name, query_decorator), ...), ... ]
    """
    from filters import structure_to_filter
    
    def filter_generator():
      from filters import GroupBoxFilter
      for structure in self.list_filter:
        filter = structure_to_filter(structure)
        yield (filter, filter.get_name_and_options(self))
        
    return list(filter_generator())

  def createValidator(self, model):
    from validator import Validator
    return Validator(self, model)
  
  @model_function
  def setDefaults(self, entity_instance):
    """Set the defaults of an object"""
    from sqlalchemy.schema import ColumnDefault
    for field,attributes in self.getFields():
      try:
        default = attributes['default']
        if isinstance(default, ColumnDefault):
          default_value = default.execute()
        elif callable(default):
          import inspect
          args, varargs, kwargs, defs = inspect.getargspec(default)
          if len(args):
            default_value = default(entity_instance)
          else:
            default_value = default()
        else:
          default_value = default
        logger.debug('set default for %s to %s' % \
                    (field, unicode(default_value)))
        setattr(entity_instance, field, default_value)
      except KeyError,e:
        pass
              
  @gui_function
  def createNewView(admin, parent=None, oncreate=None, onexpunge=None):
    """Create a QT widget containing a form to create a new instance of the
    entity related to this admin class

    The returned class has an 'entity_created_signal' that will be fired when a
    a valid new entity was created by the form
    """

    from PyQt4 import QtCore
    from PyQt4 import QtGui
    from PyQt4.QtCore import SIGNAL
    from proxy.collection_proxy import CollectionProxy
    new_object = []

    @model_function
    def collection_getter():
      if not new_object:
        entity_instance = admin.entity()
        if oncreate:
          oncreate(entity_instance)
        # Give the default fields their value
        admin.setDefaults(entity_instance)
        new_object.append(entity_instance)
      return new_object

    model = CollectionProxy(admin, collection_getter, admin.getFields,
                            max_number_of_rows=1)
    validator = admin.createValidator(model)

    class NewForm(QtGui.QWidget):

      def __init__(self, parent):
        super(NewForm, self).__init__(parent)
        self.setWindowTitle('New %s'%(admin.getName()))
        self.widget_layout = QtGui.QVBoxLayout()
        self.form_view = admin.createFormView('New', model, 0, parent)
        self.widget_layout.insertWidget(0, self.form_view)
        self.setLayout(self.widget_layout)
        self.validate_before_close = True
        self.entity_created_signal = SIGNAL("entity_created")
        
      def validateClose(self):
        if self.validate_before_close:
          self.form_view.widget_mapper.submit()
          if model.hasUnflushedRows():
          
            def validate():
              return validator.isValid(0)
                                
            def showMessage(valid):
              if not valid:
                messages = u'\n'.join(validator.validityMessages(0))
                reply = QtGui.QMessageBox.question(self, u'Could not create new %s'%admin.getName(),
                u"\n%s\n Do you want to lose your changes ?"%messages, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                  # clear mapping to prevent data being written again to the model, after we
                  # reverted the row
                  self.form_view.widget_mapper.clearMapping()
                  
                  def onexpunge_on_all():
                    if onexpunge:
                      for o in new_object:
                        onexpunge(o)
                      
                  admin.mt.post(onexpunge_on_all)
                  self.validate_before_close = False
                  from camelot.view.workspace import get_workspace
                  for window in get_workspace().subWindowList():
                    if window.widget() == self:
                      window.close()
              else:
                def create_instance_getter(new_object):
                  return lambda:new_object[0]
                
                for o in new_object:
                  self.emit(self.entity_created_signal,
                            create_instance_getter(new_object))
                self.validate_before_close = False
                from camelot.view.workspace import get_workspace
                for window in get_workspace().subWindowList():
                  if window.widget() == self:
                    window.close()
            
            admin.mt.post(validate, showMessage)
            return False
          else:
            return True
        return True
      
      def closeEvent(self, event):
        if self.validateClose():
          event.accept()
        else:
          event.ignore()

    form = NewForm(parent)
    form.setMinimumSize(admin.form_size[0], admin.form_size[1])
    return form

  @gui_function
  def createFormView(admin, title, model, index, parent):
    """Creates a Qt widget containing a form view, for a specific row of the
    passed query; uses the Admin class
    """
    logger.debug('creating form view for index %s' % index)
    from controls.formview import FormView
    form = FormView(title, admin, model, index)
    return form

  @gui_function
  def createSelectView(admin, query, search_text=None, parent=None):
    """Returns a QT widget that can be used to select an element from a query,

    @param query: sqlalchemy query object

    @param parent: the widget that will contain this select view, the returned
    widget has an entity_selected_signal signal that will be fired when a
    entity has been selected.
    """
    from controls.tableview import TableView
    from PyQt4 import QtCore
    from PyQt4.QtCore import SIGNAL

    class SelectView(TableView):

      def __init__(self, admin, parent):  
        TableView.__init__(self, admin, search_text=search_text, parent=parent)
        self.entity_selected_signal = SIGNAL("entity_selected")
        self.connect(self, SIGNAL('row_selected'), self.sectionClicked)

      def sectionClicked(self, index):
        # table model will be set by the model thread, we can't decently select
        # if it has not been set yet
        if self.table_model:
          
          def create_constant_getter(cst):
            return lambda:cst
          
          def create_instance_getter():
            entity = self.table_model._get_object(index)
            return create_constant_getter(entity)
            
          def create_emit_and_close(selectview):
            
            def emit_and_close(instance_getter):
              selectview.emit(self.entity_selected_signal, instance_getter)
              from camelot.view.workspace import get_workspace
              for window in get_workspace().subWindowList():
                if window.widget() == selectview:
                  window.close()
              
            return emit_and_close
          
          self.admin.mt.post(create_instance_getter, create_emit_and_close(self))
            
    widget = SelectView(admin, parent)
    widget.resize(admin.list_size[0], admin.list_size[1])
    return widget

  @gui_function
  def createTableView(self, query, parent=None):
    """Returns a QT widget containing a table view, for a certain query, using
    this Admin class; the table widget contains a model QueryTableModel

    @param query: sqlalchemy query object

    @param parent: the workspace widget that will contain the table view
    """

    from PyQt4 import QtCore
    from controls.tableview import TableView
    from proxy.queryproxy import QueryTableProxy
    tableview = TableView(self)
    admin = self

    def createOpenForm(self, tableview):

      def openForm(index):
        from workspace import get_workspace
        model = QueryTableProxy(tableview.admin,
                                tableview.table_model._query_getter,
                                tableview.admin.getFields,
                                max_number_of_rows=1)
        title = u'%s' % (self.getName())

        formview = tableview.admin.createFormView(title, model, index, parent)
        get_workspace().addSubWindow(formview)
        formview.show()

      return openForm

    tableview.connect(tableview,
                      QtCore.SIGNAL('row_selected'),
                      createOpenForm(self, tableview))

    return tableview
