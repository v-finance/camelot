"""
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

import settings

_ = lambda x: x

logger = logging.getLogger('entity_admin')
logger.setLevel(logging.DEBUG)

import sqlalchemy.types
import camelot.types
import datetime

_sqlalchemy_to_python_type_ = {
  sqlalchemy.types.Boolean: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'widget': 'bool'},

  sqlalchemy.types.BOOLEAN: lambda f: {'python_type': bool,
                                       'editable': True,
                                       'widget': 'bool'},

  sqlalchemy.types.Date: lambda f: {'python_type': datetime.date,
                                    'format': 'dd-mm-YYYY',
                                    'editable': True,
                                    'min': None,
                                    'max': None,
                                    'widget': 'date'},

  sqlalchemy.types.Float: lambda f: {'python_type': float,
                                     'precision': f.precision,
                                     'editable': True,
                                     'min': None,
                                     'max': None,
                                     'widget': 'float'},

  sqlalchemy.types.Integer: lambda f: {'python_type': int,
                                       'editable': True,
                                       'min': None,
                                       'max': None,
                                       'widget': 'int'},

  sqlalchemy.types.INT: lambda f: {'python_type': int,
                                   'editable': True,
                                   'min': None,
                                   'max': None,
                                   'widget': 'int'},

  sqlalchemy.types.String: lambda f: {'python_type': str,
                                      'length': f.length,
                                      'editable': True,
                                      'widget': 'str'},

  sqlalchemy.types.TEXT: lambda f: {'python_type': str,
                                    'length': f.length,
                                    'editable': True,
                                    'widget': 'str'},

  sqlalchemy.types.Unicode: lambda f: {'python_type': str,
                                       'length': f.length,
                                       'editable': True,
                                       'widget': 'str'},

  camelot.types.Image: lambda f: {'python_type': str,
                                  'editable': True,
                                  'widget': 'image'},

  camelot.types.Code: lambda f: {'python_type': list,
                                 'editable': True,
                                 'widget': 'code',
                                 'parts': f.parts},
}


class EntityAdmin(object):

  name = None
  list_display = []
  fields = []
  list_filter = []
  list_charts = []
  list_actions = []
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

  def getName(self):
    return (self.name or self.entity.__name__)

  def getModelThread(self):
    return self.mt

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

  def getSubclasses(self):
    """
    Return admin objects for the subclasses of the Entity represented by this
    admin object
    """
    from elixir import entities
    return [e.Admin(self.app_admin, e)
            for e in entities
            if issubclass(e, (self.entity, ))
            if hasattr(e, 'Admin')]

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
    from sqlalchemy import orm
    from sqlalchemy.exceptions import InvalidRequestError
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
      elif isinstance(property, orm.properties.PropertyLoader):
        target = property._get_target_class()
        if property.direction == orm.sync.ONETOMANY:
          attributes = dict(python_type=str,
                            length=None,
                            editable=True,
                            widget='one2many',
                            admin=get_entity_admin(target))
        elif property.direction == orm.sync.MANYTOONE:
          attributes = dict(python_type=str,
                            length=None,
                            editable=True,
                            widget='many2one',
                            admin=get_entity_admin(target))
        elif property.direction == orm.sync.MANYTOMANY:
          attributes = dict(python_type=str,
                            length=None,
                            editable=True,
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
    return attributes

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

  def getFields(self):
    if self.fields:
      return [(field, self.getFieldAttributes(field)) for field in self.fields]
    else:
      return [(field, self.getFieldAttributes(field))
              for field in self.list_display]

  def getListCharts(self):
    return self.list_charts

  def getFilters(self):
    """
    Return the filters applicable for these entities each filter is a tuple
    of the name of the filter and a list of options that can be selected. Each
    option is a tuple of the name of the option, and a filter function to
    decorate a query

    @return: [(filter_name, [(option_name, query_decorator), ...), ... ]
    """

    def getOptions(attr):
      from sqlalchemy.sql import select
      from elixir import session
      col = getattr(self.entity, attr)
      session.bind = self.entity.table.metadata.bind
      query = select([col], distinct=True, order_by=col.asc())

      def decorator(col, value):
        return lambda q: q.filter(col==value)

      options = [(value[0], decorator(col, value[0]))
                 for value in session.execute(query)]
      return [('All', lambda q: q)] + options

    return [(attr, getOptions(attr)) for attr in self.list_filter]

  def createValidator(self, model):
    from validator import *
    return Validator(self, model)
  
  def createNewView(admin, parent=None):
    """
    Create a QT widget containing a form to create a new instance of the entity
    related to this admin class

    The returned class has an 'entity_created_signal' that will be fired when a
    a valid new entity was created by th form
    """

    from PyQt4 import QtCore
    from PyQt4 import QtGui
    from PyQt4.QtCore import SIGNAL

    from proxy.collection_proxy import CollectionProxy

    new_object = []

    def collection_getter():
      if not new_object:
        new_object.append(admin.entity())
      return new_object

    model = CollectionProxy(admin, collection_getter, admin.getFields,
                            max_number_of_rows=1)

    class NewForm(QtGui.QWidget):

      def __init__(self, parent):
        super(NewForm, self).__init__(parent)
        self.setWindowTitle('New %s'%(admin.getName()))
        self.widget_layout = QtGui.QVBoxLayout()
        self.form_view = admin.createFormView('New', model, 0, parent)
        self.widget_layout.insertWidget(0, self.form_view)
        self.setLayout(self.widget_layout)
        self.entity_created_signal = SIGNAL("entity_created")
        
      def closeEvent(self, event):
        if self.form_view.validateClose(self):
          event.accept()
        else:
          event.ignore()
        
      def close(self):
        for o in new_object:
          if o.id:
            self.emit(self.entity_created_signal,
                      create_instance_getter(new_object))
        QtGui.QWidget.close(self)

    return NewForm(parent)

  def createFormView(admin, title, model, index, parent):
    """
    Creates a Qt widget containing a form view, for a specific row of the
    passed query; uses the Admin class
    """
    logger.debug('creating form view for index %s'%index)

    from PyQt4 import QtCore
    from PyQt4.QtCore import SIGNAL
    from PyQt4 import QtGui

    validator = admin.createValidator(model)
    
    class FormView(QtGui.QWidget):

      def __init__(self):
        super(FormView, self).__init__(None)
        self.setWindowTitle(title)
        self.widget_layout = QtGui.QHBoxLayout()
        self.widget_mapper = QtGui.QDataWidgetMapper()
        self.model = model
        self.connect(self.model,
                     SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                     self.dataChanged)
        self.widget_mapper.setModel(self.model)
        self.form_layout = QtGui.QFormLayout()
        self.widget_layout.insertLayout(0, self.form_layout)
        self.setLayout(self.widget_layout)
        self.validate_before_close = True
        admin.mt.post(lambda: None,
                      lambda *args: self.setColumnsAndDelegate(
                                      self.model.columns_getter(),
                                      self.model.getItemDelegate()))

        def getEntityAndActions():
          entity = self.model._get_object(index)
          actions = admin.getFormActions(entity)
          return entity, actions

        admin.mt.post(getEntityAndActions, self.setEntityAndActions)

      def dataChanged(self, index_from, index_to):
        #@TODO: only revert if this form is in the changed range
        self.widget_mapper.revert()

      def setColumnsAndDelegate(self, columns, delegate):
        for i, column in enumerate(columns):
          widget = delegate.createEditor(parent,
                                         None,
                                         self.model.index(index, i))
          self.form_layout.addRow(column[1]['name'], widget)
          self.widget_mapper.addMapping(widget, i)
        self.widget_mapper.setItemDelegate(delegate)
        self.widget_mapper.setCurrentIndex(index)

      def setEntityAndActions(self, result):
        entity, actions = result
        if actions:
          from controls.actions import ActionsBox
          logger.debug('setting Actions')
          self.actions_widget = ActionsBox(self, admin.mt)
          self.actions_widget.setActions(actions)
          self.actions_widget.setEntity(entity)
          self.widget_layout.insertWidget(1, self.actions_widget)

      def validateClose(self, window_to_close):
        if self.validate_before_close:
          # submit should not happen a second time, since then we don't want the widgets data to
          # be written to the model
          self.widget_mapper.submit()
          if model.hasUnflushedRows():
          
            def validate():
              return validator.isValid(self.widget_mapper.currentIndex())
            
            def expunge_object():
              from elixir import session
              o = model._get_object(self.widget_mapper.currentIndex())
              if o.id:
                session.refresh(o)
              else:
                session.expunge(o)
                                
            def showMessage(valid):
              if not valid:
                messages = u'\n'.join(validator.validityMessages(self.widget_mapper.currentIndex()))
                reply = QtGui.QMessageBox.question(self, u'Unsaved changes',
                u"Changes in this window could not be saved :\n%s\n Do you want to lose your changes ?"%messages, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                  admin.mt.post(expunge_object)
                  self.validate_before_close = False
                  window_to_close.close()
            
            admin.mt.post(validate, showMessage)
            return False
          else:
            return True
        return True
                  
      def closeEvent(self, event):
        if self.validateClose(self):
          event.accept()
        else:
          event.ignore()
          
    return FormView()

  def createSelectView(self, query, parent=None):
    """
    Returns a QT widget that can be used to select an element form a query,

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
        TableView.__init__(self, admin, parent)
        self.entity_selected_signal = SIGNAL("entity_selected")
        self.connect(self.table.verticalHeader(),
                     SIGNAL('sectionClicked(int)'),
                     self.sectionClicked)

      def sectionClicked(self, index):

        def create_instance_getter(index):
          return lambda: self.table_model._get_object(index)

        self.emit(self.entity_selected_signal, create_instance_getter(index))

        self.close()

    return SelectView(self, parent)

  def createTableView(self, query, parent=None):
    """
    Returns a QT widget containing a table view, for a certain query, using
    this Admin class; the table widget contains a model QueryTableModel

    @param query: sqlalchemy query object
    @param parent: the workspace widget that will contain the table view
    """
    from controls.tableview import TableView
    from proxy.queryproxy import QueryTableProxy
    from PyQt4 import QtCore
    from PyQt4.QtCore import SIGNAL

    tableview = TableView(self, parent)

    def createOpenForm(self, tableview):

      def openForm(index):
        from camelot.view.workspace import get_workspace, key_from_query
        model = QueryTableProxy(self,
                                tableview.table_model.query,
                                self.getFields)
        title = u'%s'%(self.getName())
        form = self.createFormView(title, model, index, parent)
        get_workspace().addWindow('form', form)
        form.show()

      return openForm

    tableview.connect(tableview.table.verticalHeader(),
                      SIGNAL('sectionClicked(int)'),
                      createOpenForm(self, tableview))

    return tableview

  def __str__(self):
    return 'Admin %s'%str(self.entity.__name__)
