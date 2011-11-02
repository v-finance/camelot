#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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

import logging
logger = logging.getLogger('camelot.admin.entity_admin')

from camelot.admin.action.list_action import OpenFormView
from camelot.admin.object_admin import ObjectAdmin
from camelot.view.model_thread import post, model_function, gui_function
from camelot.core.utils import ugettext_lazy, ugettext
from camelot.admin.validator.entity_validator import EntityValidator

class EntityAdmin(ObjectAdmin):
    """Admin class specific for classes that are mapped by sqlalchemy.
This allows for much more introspection than the standard 
:class:`camelot.admin.object_admin.ObjectAdmin`.
    
It has additional class attributes that customise its behaviour.

**Basic**

.. attribute:: list_action

   The :class:`camelot.admin.action.Action` that will be triggered when the
   user selects an item in a list of objects.  This defaults to 
   :class:`camelot.admin.action.list_action.OpenFormView`, which opens a form
   for the current object.
   
**Filtering**

.. attribute:: list_filter

    A list of fields that should be used to generate filters for in the table
    view.  If the field named is a one2many, many2one or many2many field, the
    field name should be followed by a field name of the related entity ::

        class Project(Entity):
            oranization = OneToMany('Organization')
            name = Field(Unicode(50))
    
          class Admin(EntityAdmin):
              list_display = ['organization']
              list_filter = ['organization.name']

    .. image:: /_static/filter/group_box_filter.png

**Copying**

.. attribute:: copy_deep

   A dictionary of fields that will be deep copied when the user presses the copy
   button.  This is usefull for OneToMany fields.  The key in the dictionary should
   be the name of the field, and the value is a new dictionary that can contain other
   fields that need to be copied::

       copy_deep = {'addresses':{}}

.. attribute:: copy_exclude

    A list of fields that should not be copied when the user presses the copy button::

        copy_exclude = ['name']

    The fields that form the primary key of the object will be excluded by default.

**Searching**

.. attribute:: list_search

    A list of fields that should be searched when the user enters something in
    the search box in the table view.  By default all fields are
    searched for which Camelot can do a conversion of the entered string to the
    datatype of the underlying column.  

    For use with one2many, many2one or many2many fields, the same rules as for the 
    list_filter attribute apply

.. attribute:: search_all_fields

    Defaults to True, meaning that by default all searchable fields should be
    searched.  If this is set to False, one should explicitely set the list_search
    attribute to enable search.

.. attribute:: expanded_list_search

    A list of fields that will be searchable through the expanded search.  When set 
    to None, all the fields in list_display will be searchable.  Use this attribute
    to limit the number of search widgets.  Defaults to None.
 
    """

    list_action = OpenFormView()
    list_search = []
    expanded_list_search = None
    copy_deep = {}
    copy_exclude = []
    search_all_fields = True
    validator = EntityValidator

    def __init__(self, app_admin, entity):
        super(EntityAdmin, self).__init__(app_admin, entity)
        from sqlalchemy import orm
        from sqlalchemy.orm.exc import UnmappedClassError
        from sqlalchemy.orm.mapper import _mapper_registry
        try:
            self.mapper = orm.class_mapper(self.entity)
        except UnmappedClassError, exception:
            mapped_entities = [unicode(m) for m in _mapper_registry.keys()]
            logger.error(u'%s is not a mapped class, configured mappers include %s'%(self.entity, u','.join(mapped_entities)),
                         exc_info=exception)
            raise exception

    @model_function
    def get_query(self):
        """:return: an sqlalchemy query for all the objects that should be
        displayed in the table or the selection view.  Overwrite this method to
        change the default query, which selects all rows in the database.
        """
        from elixir import session
        return session.query( self.entity )

    @model_function
    def get_verbose_identifier(self, obj):
        if obj:
            primary_key = self.mapper.primary_key_from_instance(obj)
            if not None in primary_key:
                primary_key_representation = u','.join([unicode(v) for v in primary_key])
                if hasattr(obj, '__unicode__'):
                    return u'%s %s : %s' % (
                        unicode(self.get_verbose_name() or ''),
                        primary_key_representation,
                        unicode(obj)
                    )
                else:
                    return u'%s %s' % (
                        self.get_verbose_name() or '',
                        primary_key_representation
                    )
        return self.get_verbose_name()

    @model_function
    def get_field_attributes(self, field_name):
        """Get the attributes needed to visualize the field field_name
        :param field_name: the name of the field

        :return: a dictionary of attributes needed to visualize the field,
        those attributes can be:
         * python_type : the corresponding python type of the object
         * editable : bool specifying wether the user can edit this field
         * widget : which widget to be used to render the field
         * ...
        """        
        from sqlalchemy.orm.mapper import _mapper_registry
            
        try:
            return self._field_attributes[field_name]
        except KeyError:

            def create_default_getter(field_name):
                return lambda o:getattr(o, field_name)

            from camelot.view.controls import delegates
            #
            # Default attributes for all fields
            #
            attributes = dict(
                python_type = str,
                to_string = unicode,
                field_name = field_name,
                getter = create_default_getter(field_name),
                length = None,
                tooltip = None,
                background_color = None,
                minimal_column_width = 12,
                editable = False,
                nullable = True,
                widget = 'str',
                blank = True,
                delegate = delegates.PlainTextDelegate,
                validator_list = [],
                name = ugettext_lazy(field_name.replace('_', ' ').capitalize())
            )

            #
            # Field attributes forced by the field_attributes property
            #
            forced_attributes = {}
            try:
                forced_attributes = self.field_attributes[field_name]
            except KeyError:
                pass

            def resolve_target(target):
                """A class or name of the class representing the other
                side of a relation.  Use the name of the class to avoid
                circular dependencies"""
                if isinstance(target, basestring):
                    for mapped_class in _mapper_registry.keys():
                        if mapped_class.class_.__name__ == target:
                            return mapped_class.class_
                    raise Exception('No mapped class found for target %s'%target)
                return target
                
            def get_entity_admin(target):
                """Helper function that instantiated an Admin object for a
                target entity class.

                :param target: an entity class for which an Admin object is
                needed
                """

                try:
                    admin_class = forced_attributes['admin']
                    return admin_class(self.app_admin, target)
                except KeyError:
                    return self.get_related_entity_admin(target)
            #
            # Get the default field_attributes trough introspection if the
            # field is a mapped field
            #
            from sqlalchemy import orm, schema
            from sqlalchemy.exc import InvalidRequestError
            from camelot.view.field_attributes import _sqlalchemy_to_python_type_

            try:
                property = self.mapper.get_property(
                    field_name,
                    resolve_synonyms=True
                )
                if isinstance(property, orm.properties.ColumnProperty):
                    column_type = property.columns[0].type
                    python_type = _sqlalchemy_to_python_type_.get(
                        column_type.__class__,
                        None
                    )
                    if python_type:
                        attributes.update(python_type(column_type))
                    if isinstance( property.columns[0], (schema.Column) ):
                        attributes['nullable'] = property.columns[0].nullable
                        attributes['default'] = property.columns[0].default
                elif isinstance(property, orm.properties.PropertyLoader):
                    target = forced_attributes.get( 'target', 
                                                    property._get_target().class_ )
                    
                    #
                    # _foreign_keys is for sqla pre 0.6.4
                    # 
                    if hasattr(property, '_foreign_keys'):
                        foreign_keys = list(property._foreign_keys)
                    else:
                        foreign_keys = list( property._user_defined_foreign_keys )
                        foreign_keys.extend( list(property._calculated_foreign_keys) )
                        
                    if property.direction == orm.interfaces.ONETOMANY:
                        attributes.update(
                            python_type = list,
                            editable = True,
                            nullable = True,
                            delegate = delegates.One2ManyDelegate,
                            target = target,
                            create_inline = False,
                            direction = property.direction,
                            admin = get_entity_admin(target)
                        )
                    elif property.direction == orm.interfaces.MANYTOONE:
                        attributes.update(
                            python_type = str,
                            editable = True,
                            delegate = delegates.Many2OneDelegate,
                            target = target,
                            #
                            # @todo: take into account all foreign keys instead
                            # of only the first one
                            #
                            nullable = foreign_keys[0].nullable,
                            direction = property.direction,
                            admin = get_entity_admin(target)
                        )
                    elif property.direction == orm.interfaces.MANYTOMANY:
                        attributes.update(
                            python_type = list,
                            editable = True,
                            target = target,
                            nullable = True,
                            create_inline = False,
                            direction = property.direction,
                            delegate = delegates.ManyToManyDelegate,
                            admin = get_entity_admin(target)
                        )
                    else:
                        raise Exception('PropertyLoader has unknown direction')
            except InvalidRequestError:
                #
                # If the field name is not a property of the mapper, then use
                # the default stuff
                #
                pass

            if 'choices' in forced_attributes:
                attributes['delegate'] = delegates.ComboBoxDelegate
                attributes['editable'] = True
                if isinstance(forced_attributes['choices'], list):
                    choices_dict = dict(forced_attributes['choices'])
                    attributes['to_string'] = lambda x : choices_dict[x]

            #
            # Overrule introspected field_attributes with those defined
            #
            attributes.update(forced_attributes)

            #
            # In case of a 'target' field attribute, instantiate an appropriate
            # 'admin' attribute
            #
            if 'target' in attributes:
                attributes['target'] = resolve_target(attributes['target'])
                attributes['admin'] = get_entity_admin(attributes['target'])
            
            self._field_attributes[field_name] = attributes
            return attributes

    def get_dynamic_field_attributes(self, obj, field_names):
        """Takes the dynamic field attributes from through the ObjectAdmin its
        get_dynamic_field_attributes and add the new_message attributes for
        One2Many fields where the object was not flushed yet
        """
        from sqlalchemy.orm.session import Session
        session = Session.object_session( obj )
        # when a previous flush failed, obj might have no session
        if session and obj in session.new:
            new_message = ugettext('Please complete the form first')
        else:
            new_message = None
        for attributes in super(EntityAdmin, self).get_dynamic_field_attributes(obj, field_names):
            attributes['new_message'] = new_message
            yield attributes
            
    @model_function
    def get_list_charts(self):
        return self.list_charts

    @model_function
    def get_filters(self):
        """Returns the filters applicable for these entities each filter is

        :return: [(filter_name, [(option_name, query_decorator), ...), ... ]
        """
        from camelot.view.filters import structure_to_filter

        def filter_generator():
            for structure in self.list_filter:
                filter = structure_to_filter(structure)
                yield (filter, filter.get_name_and_options(self))

        return list(filter_generator())

    @model_function
    def set_defaults(self, entity_instance, include_nullable_fields=True):
        """Set the fields of an object to their default state.
        
        :param include_nullable_fields: also set defaults for nullable fields, 
            depending on the context, this should be set to False to allow 
            the user to set the field to None
        """
        from sqlalchemy.schema import ColumnDefault
        
        if self.is_deleted( entity_instance ):
            return False

        for field, attributes in self.get_fields():
            has_default = False
            try:
                default = attributes['default']
                has_default = True
            except KeyError:
                pass
            if has_default:
                #
                # prevent the setting of a default value when one has been
                # set already
                #
                value = attributes['getter'](entity_instance)
                if value!=None: # False is a legitimate value for Booleans
                    continue
                if isinstance(default, ColumnDefault):
                    default_value = default.execute()
                elif callable(default):
                    import inspect
                    args, _varargs, _kwargs, _defs = \
                        inspect.getargspec(default)
                    if len(args):
                        default_value = default(entity_instance)
                    else:
                        default_value = default()
                else:
                    default_value = default
                logger.debug(
                    'set default for %s to %s' % (
                        field,
                        unicode(default_value)
                    )
                )
                try:
                    setattr(entity_instance, field, default_value)
                except AttributeError, exc:
                    logger.error(
                        'Programming Error : could not set'
                        ' attribute %s to %s on %s' % (
                            field,
                            default_value,
                            entity_instance.__class__.__name__
                        ),
                        exc_info=exc
                    )


    @gui_function
    def create_select_view(admin, query=None, search_text=None, parent=None):
        """Returns a Qt widget that can be used to select an element from a
        query

        :param query: sqlalchemy query object

        :param parent: the widget that will contain this select view, the
        returned widget has an entity_selected_signal signal that will be fired
        when a entity has been selected.
        """
        from camelot.view.art import Icon
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from PyQt4 import QtCore, QtGui

        class SelectQueryTableProxy(QueryTableProxy):
            header_icon = Icon('tango/16x16/emblems/emblem-symbolic-link.png')

        class SelectView(admin.TableView):
            table_model = SelectQueryTableProxy
            entity_selected_signal = QtCore.pyqtSignal(object)
            title_format = ugettext('Select %s')

            def __init__(self, admin, parent):
                super(SelectView, self).__init__(
                    admin,
                    search_text=search_text, parent=parent
                )
                self.row_selected_signal.connect( self.sectionClicked )
                self.setUpdatesEnabled(True)

                table = self.findChild(QtGui.QTableView, 'AdminTableWidget')
                if table != None:
                    table.keyboard_selection_signal.connect(self.on_keyboard_selection)
                    table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

            def emit_entity_selected(self, instance_getter):
                self.entity_selected_signal.emit( instance_getter )
                
            @QtCore.pyqtSlot()
            def on_keyboard_selection(self):
                table = self.findChild(QtGui.QTableView, 'AdminTableWidget')
                if table != None:
                    self.row_selected_signal.emit(table.currentIndex().row())

            @QtCore.pyqtSlot(int)
            def sectionClicked(self, index):
                # table model will be set by the model thread, we can't
                # decently select if it has not been set yet
                if self.table.model():

                    def create_constant_getter(cst):
                        return lambda:cst

                    def create_instance_getter():
                        entity = self.table.model()._get_object(index)
                        return create_constant_getter(entity)

                    post(create_instance_getter, self.emit_entity_selected)

        widget = SelectView(admin, parent)
        widget.setUpdatesEnabled(True)
        widget.setMinimumSize(admin.list_size[0], admin.list_size[1])
        widget.update()
        return widget

    @gui_function
    def create_table_view( self ):
        """Returns a QWidget containing a table view
        """
        return self.TableView( self )

    @model_function
    def delete(self, entity_instance):
        """Delete an entity instance"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        #
        # new and deleted instances cannot be deleted
        #
        if session:
            if entity_instance in session.new:
                session.expunge(entity_instance)
            elif (entity_instance not in session.deleted) and \
                 (entity_instance in session): # if the object is not in the session, it might already be deleted
                history = None
                #
                # only if we know the primary key, we can keep track of its history
                #
                primary_key = self.mapper.primary_key_from_instance(entity_instance)
                #
                # we can only store history of objects where the primary key has only
                # 1 element
                # @todo: store history for compound primary keys
                #
                if not None in primary_key and len(primary_key)==1:
                    pk = primary_key[0]
                    # save the state before the update
                    from camelot.model.memento import BeforeDelete
                    # only register the delete when the camelot model is active
                    if hasattr(BeforeDelete, 'query'):
                        from camelot.model.authentication import getCurrentAuthentication
                        history = BeforeDelete( model = unicode( self.entity.__name__ ),
                                                primary_key = pk,
                                                previous_attributes = {},
                                                authentication = getCurrentAuthentication() )
                entity_instance.delete()
                session.flush( [entity_instance] )
                if history:
                    Session.object_session( history ).flush( [history] )

    @model_function
    def expunge(self, entity_instance):
        """Expunge the entity from the session"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        if session:
            session.expunge( entity_instance )
        
    @model_function
    def flush(self, entity_instance):
        """Flush the pending changes of this entity instance to the backend"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        if session:
            session.flush( [entity_instance] )

    @model_function
    def refresh(self, entity_instance):
        """Undo the pending changes to the backend and restore the original
        state"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        if session:
            if not self.is_deleted( entity_instance ):
                session.refresh( entity_instance )
       
    @model_function
    def is_persistent(self, obj):
        """:return: True if the object has a persisted state, False otherwise"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( obj )
        if session:
            if obj in session.new:
                return False
            if obj in session.deleted:
                return False
            return True
        return False
    
    @model_function
    def is_deleted(self, obj):
        """
        :return: True if the object has been deleted from the persistent
            state, False otherwise"""
        from sqlalchemy.orm.attributes import instance_state
        state = instance_state( obj )
        if state != None and state.deleted:
            return True
        return False
    
    @model_function
    def get_expanded_search_fields(self):
        """
        :return: a list of tuples of type [(field_name, field_attributes)]
        """
        if self.expanded_list_search == None:
            field_list = self.list_display
        else:
            field_list = self.expanded_list_search
        return [(field, self.get_field_attributes(field))
                for field in field_list]
        
    @model_function
    def copy(self, obj, new_obj=None):
        """Duplicate an object.  If no new object is given to copy to, a new
        one will be created.  This function will be called every time the
        user presses a copy button.
        
        :param obj: the object to be copied from
        :param new_obj: the object to be copied to, defaults to None
        :return: the new object
        
        This function takes into account the deep_copy and the copy_exclude
        attributes.  It tries to recreate relations with a minimum of side
        effects.
        """
        from sqlalchemy import orm
        if not new_obj:
            new_obj = obj.__class__()
        #
        # serialize the object to be copied
        #
        # @todo: this code depends on elixir
        serialized = obj.to_dict(deep=self.copy_deep, exclude=[c.name for c in self.mapper.primary_key]+self.copy_exclude)
        #
        # make sure we don't move duplicated OneToMany relations from the
        # old object to the new, but instead duplicate them, by manipulating
        # the serialized structure
        #
        # @todo: this should be recursive
        for property in self.mapper.iterate_properties:
            if isinstance(property, orm.properties.PropertyLoader):
                if property.direction == orm.interfaces.ONETOMANY:
                    target = property._get_target().class_
                    for relation in serialized.get(property.key, []):
                        relation_mapper = orm.class_mapper(target)
                        for primary_key_field in relation_mapper.primary_key:
                            relation[primary_key_field.name] = None
        #from pprint import pprint
        #pprint( serialized )
        #
        # deserialize into the new object
        #
        new_obj.from_dict( serialized )
        #
        # recreate the ManyToOne relations
        #
        for property in self.mapper.iterate_properties:
            if isinstance(property, orm.properties.PropertyLoader):
                if property.direction == orm.interfaces.MANYTOONE:
                    setattr( new_obj, 
                             property.key,
                             getattr( obj, property.key ) )
        return new_obj
