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

import inspect
import itertools
import logging


logger = logging.getLogger('camelot.admin.entity_admin')

from ..core.item_model import QueryModelProxy

from camelot.admin.admin_route import register_list_actions
from camelot.admin.action import list_filter, application_action, list_action
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.validator.entity_validator import EntityValidator
from camelot.core.memento import memento_change
from camelot.core.naming import initial_naming_context
from camelot.core.orm import Session
from camelot.core.orm.entity import entity_to_dict
from camelot.types import PrimaryKey

from sqlalchemy import orm, schema, sql
from sqlalchemy.ext import hybrid
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.exc import UnmappedClassError

class EntityAdmin(ObjectAdmin):
    """Admin class specific for classes that are mapped by sqlalchemy.
This allows for much more introspection than the standard
:class:`camelot.admin.object_admin.ObjectAdmin`.

It has additional class attributes that customise its behaviour.

**Filtering**

.. attribute:: list_filter

    A list of fields that should be used to generate filters for in the table
    view.  If the field named is a one2many, many2one or many2many field, the
    field name should be followed by a field name of the related entity ::

        class Project( Entity ):
            oranization = OneToMany( 'Organization' )
            name = Column( Unicode(50) )

          class Admin( EntityAdmin ):
              list_display = ['organization']
              list_filter = ['organization.name']

    .. image:: /_static/filter/group_box_filter.png

**Copying**

.. attribute:: copy_deep

    A dictionary of fields that will be deep copied when the user presses the copy
    button.  This is useful for OneToMany fields.  The key in the dictionary should
    be the name of the field, and the value is a new dictionary :: 

       copy_deep = {'addresses':{}}

    This dictionary can contain fields in the related object that need to be deep 
    copied as well ::

       copy_deep = {'addresses':{'city':{}}}


.. attribute:: copy_exclude

    A list of fields that should not be copied when the user presses the copy button::

        copy_exclude = ['name']

    The fields that form the primary key of the object will be excluded by default.

To further customize the copy process without additional user interaction,
:meth:`camelot.admin.object_admin.EntityAdmin.copy` method can be overwritten.

If the user interaction during the copy process needs to be customized as well, the
:class:`camelot.admin.action.list_action.DuplicateSelection` class can be subclassed
and used as a custom action.


    """

    copy_deep = {}
    copy_exclude = []
    validator = EntityValidator
    basic_search = True
    basic_filters = True
    
    # Temporary hack to allow admins of target entities in one2many/many2many relations to register themselves as editable
    # with a pending owning instance.
    # This should be used with extreme care though, as the default list actions only support a persistent owning instance
    # and thus specialized actions should be used by the target admin to handle the persistence flow correctly.
    # This is a temporary measure in order to work towards supporting this behaviour in general in the future.
    allow_relation_with_pending_owner = False
    
    def __init__(self, app_admin, entity):
        super(EntityAdmin, self).__init__(app_admin, entity)
        from sqlalchemy.orm.exc import UnmappedClassError
        from sqlalchemy.orm.mapper import _mapper_registry
        try:
            self.mapper = orm.class_mapper(self.entity)
        except UnmappedClassError as exception:
            mapped_entities = [str(m) for m in _mapper_registry.keys()]
            logger.error(u'%s is not a mapped class, configured mappers include %s'%(self.entity, u','.join(mapped_entities)),
                         exc_info=exception)
            raise exception
        # caching
        self._search_fields = None
        self._filter_actions = None
        self._field_filters = None

    @classmethod
    def get_sql_field_attributes( cls, columns ):
        """Returns a set of default field attributes based on introspection
        of the SQLAlchemy columns that form a field

        :param: columns a list of :class:`sqlalchemy:sqlalchemy.schema.Column`
            objects.
        :return: a dictionary with field attributes

        By default this method looks at the first column that defines the
        field and derives a delegate and other field attributes that make
        sense.
        """
        from camelot.view.field_attributes import _sqlalchemy_to_python_type_
        sql_attributes = dict()
        for column in columns:
            column_type = column.type
            sql_attributes['python_type'] = ''
            sql_attributes['doc'] = ''
            # PrimaryKey is not in _sqlalchemy_to_python_type_, but its
            # implementation class probably is
            if isinstance(column_type, PrimaryKey):
                column_type = column_type.load_dialect_impl(None)
            for base_class in inspect.getmro( type( column_type ) ):
                fa = _sqlalchemy_to_python_type_.get( base_class,
                                                      None )
                if fa is not None:
                    sql_attributes.update( fa( column_type ) )
                    break
            if isinstance( column, (schema.Column) ):
                sql_attributes['nullable'] = column.nullable
                sql_attributes['default'] = column.default
                sql_attributes['doc'] = column.doc or ''
                editable = (column.primary_key is False)
                # if these fields are editable, they are validated when a form
                # is closed, while at that time the field is not yet filled
                # because the foreign key column is only filled after the flush
                if len(column.foreign_keys):
                    editable = False
                sql_attributes['editable'] = editable
            field_admin = getattr(column, '_field_admin', None)
            if field_admin != None:
                sql_attributes.update(field_admin.get_field_attributes())
            break
        return sql_attributes

    def get_mapper(self):
        """Returns this entity admin's mapper."""
        return self.mapper

    def get_query(self, session=None):
        """
        Overwrite this method to configure eager loading strategies
        to be used in a specific admin.

        :param session: the session to be used to create a query.
           Uses the default session if None is given.
           Not passing the session is considered deprecated behavior.

        :return: an sqlalchemy query for all the objects that should be
        displayed in the table or the selection view.  Overwrite this method to
        change the default query, which selects all rows in the database.
        """
        session = session or Session()
        return session.query(self.entity)

    def get_proxy(self, objects):
        """
        :return: a :class:`camelot.core.item_model.proxy.AbstractModelProxy`
            instance for the given objects.
        """
        if isinstance(objects, orm.Query):
            return QueryModelProxy(objects)
        return super(EntityAdmin, self).get_proxy(objects)

    def get_verbose_identifier(self, obj):
        if obj is not None:
            primary_key = self.primary_key(obj)
            if not None in primary_key:
                primary_key_representation = u','.join([str(v) for v in primary_key])
                if hasattr(obj, '__unicode__'):
                    return u'%s %s : %s' % (
                        str(self.get_verbose_name() or ''),
                        primary_key_representation,
                        str(obj)
                    )
                elif hasattr(obj, '__str__'):
                    return u'%s %s : %s' % (
                        self.get_verbose_name() or '',
                        primary_key_representation,
                        obj.__str__()
                    )                
                else:
                    return u'%s %s' % (
                        self.get_verbose_name() or '',
                        primary_key_representation
                    )
        return self.get_verbose_name()

    def get_verbose_search_identifier(self, obj):
        return self.get_verbose_object_name(obj)

    @register_list_actions('_admin_route', '_shared_toolbar_actions')
    def _get_shared_toolbar_actions( self ):
        return [
            list_filter.search_filter,
            list_action.set_filters,
            application_action.refresh,
        ]

    @register_list_actions('_admin_route', '_toolbar_actions')
    def get_list_toolbar_actions( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of the application.  return
            None if no toolbar should be created.
        """
        toolbar_actions = super(EntityAdmin, self).get_list_toolbar_actions()
        return toolbar_actions + self._get_shared_toolbar_actions()

    @register_list_actions('_admin_route', '_select_toolbar_actions')
    def get_select_list_toolbar_actions( self ):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of the application.  return
            None if no toolbar should be created.
        """
        toolbar_actions = super(EntityAdmin, self).get_select_list_toolbar_actions()
        if self.is_editable():
            return [
                list_action.close_list,
                list_action.list_label,
                list_action.add_new_object,
                list_action.delete_selection,
                list_action.duplicate_selection,
                list_action.to_first_row,
                list_action.to_last_row,
                ] + self._get_shared_toolbar_actions()
        return toolbar_actions + self._get_shared_toolbar_actions()

    @register_list_actions('_admin_route')
    def get_related_toolbar_actions(self, direction):
        actions = super(EntityAdmin, self).get_related_toolbar_actions(direction)
        if direction == 'onetomany' and self.entity.get_ranked_by() is not None:
            actions.extend([list_action.move_rank_up, list_action.move_rank_down])
        return actions

    def get_descriptor_field_attributes(self, field_name):
        """Returns a set of default field attributes based on introspection
        of the descriptor of a field.
        """
        from camelot.view.controls import delegates
        attributes = super(EntityAdmin, self).get_descriptor_field_attributes(field_name)
        #
        # Field attributes forced by the field_attributes property
        #
        forced_attributes = self.field_attributes.get(field_name, {})
        #
        # Get the default field_attributes trough introspection if the
        # field is a mapped field
        #
        from sqlalchemy import orm
        from sqlalchemy.exc import InvalidRequestError
        #
        # See if there is a sqlalchemy descriptor
        #
        for cls in self.entity.__mro__:
            descriptor = cls.__dict__.get(field_name, None)
            if descriptor is not None:
                if isinstance(descriptor, hybrid.hybrid_property):
                    attributes['editable'] = (descriptor.fset is not None)
                    if (descriptor.expr is None) or (descriptor.expr == descriptor.fget):
                        # the descriptor has no expression, stop the introspection
                        break
                    # dont try to get the expression from the descriptor, but use
                    # the 'appropriate' way to get it from the class.  Getting it
                    # from the descriptor seems to manipulate  the actual descriptor
                    class_attribute = getattr(self.entity, field_name)
                    if class_attribute is not None:
                        # Attribute should always have an expression because of the check made above.
                        expression = class_attribute.expression
                        columns = []
                        if isinstance(expression, (schema.Column, sql.elements.Label)):
                            columns = [expression]
                        elif isinstance(expression, sql.Select):
                            columns = expression.columns
                        for k, v in self.get_sql_field_attributes(columns).items():
                            # the defaults or the nullable status of the column
                            # does not need to be the default or the nullable
                            # of the hybrid property
                            # changed 4/7/2017 DJK; editable added to avoid setting fields editable
                            # when they should not be editable
                            # Note that a primary key can be set editable by this change!!
                            if k in ['default', 'nullable', 'editable']:
                                continue
                            attributes[k] = v
                break
        # @todo : investigate if the property can be fetched from the descriptor
        #         instead of going through the mapper
        try:
            mapper = self.get_mapper()
            property = mapper.get_property(field_name) if mapper else None
            if isinstance(property, orm.properties.ColumnProperty):
                columns = property.columns
                sql_attributes = self.get_sql_field_attributes( columns )
                attributes.update( sql_attributes )
            elif isinstance(property, orm.properties.RelationshipProperty):
                target = forced_attributes.get( 'target',
                                                property.mapper.class_ )

                attributes.update( target = target,
                                   editable = property.viewonly==False,
                                   nullable = True)
                foreign_keys = list( property._user_defined_foreign_keys )
                foreign_keys.extend( list(property._calculated_foreign_keys) )

                if property.direction == orm.interfaces.ONETOMANY:
                    attributes.update( direction = 'onetomany' )
                elif property.direction == orm.interfaces.MANYTOONE:
                    attributes.update(
                        #
                        # @todo: take into account all foreign keys instead
                        # of only the first one
                        #
                        nullable = foreign_keys[0].nullable,
                        direction = 'manytoone',
                        filter_strategy = list_filter.Many2OneFilter,
                    )
                elif property.direction == orm.interfaces.MANYTOMANY:
                    attributes.update( direction = 'manytomany' )
                else:
                    raise Exception('RelationshipProperty has unknown direction')

                if property.uselist == True:
                    attributes.update(
                        delegate = delegates.One2ManyDelegate,
                        python_type = list,
                        create_inline = False,
                    )
                else:
                    attributes.update(
                        delegate = delegates.Many2OneDelegate,
                        python_type = str,
                    )

        except InvalidRequestError:
            #
            # If the field name is not a property of the mapper, then use
            # the default stuff
            #
            pass
        # Check __entity_args__ for 'editable' & 'editable_fields'
        entity_arg_editable = self.entity._get_entity_arg('editable')
        if entity_arg_editable is not None and not entity_arg_editable:
            entity_arg_editable_fields = self.entity._get_entity_arg('editable_fields')
            if entity_arg_editable_fields is None or field_name not in entity_arg_editable_fields:
                attributes['editable'] = False
        return attributes

    def _expand_field_attributes(self, field_attributes, field_name):
        """Given a set field attributes, expand the set with attributes
        derived from the given attributes.
        """
        #
        # In case of a text 'target' field attribute, resolve it
        #
        from sqlalchemy.orm.mapper import _mapper_registry
        target = field_attributes.get('target', None)
        if isinstance(target, str):
            for mapped_class in _mapper_registry.keys():
                if mapped_class.class_.__name__ == target:
                    field_attributes['target'] = mapped_class.class_
                    break
            else:
                raise Exception('No mapped class found for target %s'%target)
        super()._expand_field_attributes(field_attributes, field_name)

    def get_session(self, obj):
        if obj is not None:
            return orm.object_session(obj)

    def get_dynamic_field_attributes(self, obj, field_names):
        """Takes the dynamic field attributes from through the ObjectAdmin its
        get_dynamic_field_attributes and make relational fields not editable
        in case the object is not yet persisted.
        """
        directions = ('onetomany', 'manytomany' )
        persistent = self.is_persistent( obj )
        iter1, iter2 = itertools.tee( field_names )
        attributes_iterator = super(EntityAdmin, self).get_dynamic_field_attributes( obj, iter1 )
        for attributes, field_name in zip( attributes_iterator, iter2 ):
            if not persistent:
                all_attributes = self.get_field_attributes( field_name )
                if all_attributes.get('direction', False) in directions:
                    admin = all_attributes.get('admin')
                    # Temporary hack to allow admins of target entities in one2many/many2many relations to be editable
                    # with a pending owning instance.
                    # This should be used with extreme care though, as this behaviour is not generally supported by list actions,
                    # and thus specialized actions should be used by the target admin to handle the persistence flow correctly.
                    # This is a temporary measure in order to work towards supporting this behaviour in general in the future.
                    if (admin is not None) and (not admin.allow_relation_with_pending_owner):
                        attributes['editable'] = False
            yield attributes

    def get_completions(self, obj, field_name, prefix, **kwargs):
        """
        Overwrites `ObjectAdmin.get_completions` and searches for autocompletion
        along relationships.
        """
        all_attributes = self.get_field_attributes(field_name)
        admin = all_attributes.get('admin')
        session = orm.object_session(obj)
        if (admin is not None) and (session is not None) and not (prefix is None or len(prefix.strip())==0):
            for action_route in admin.get_list_toolbar_actions():
                search_filter = initial_naming_context.resolve(action_route.route)
                if isinstance(search_filter, list_filter.SearchFilter):
                    query = admin.get_query(session)
                    query = search_filter.decorate_query(query, (prefix, *[search_strategy for search_strategy in admin._get_search_fields(prefix)]), **kwargs)
                    return [e for e in query.limit(20).all()]
        return super(EntityAdmin, self).get_completions(obj, field_name, prefix, **kwargs)

    @register_list_actions('_admin_route', '_filter_actions')
    def get_filters( self ):
        """Returns the filters applicable for these entities each filter is

        :return: [filter, filter, ...]
        """

        def filter_generator():
            for structure in self.list_filter:
                if not isinstance(structure, list_filter.Filter):
                    structure = list_filter.GroupBoxFilter(structure)
                yield structure

        return list(filter_generator())

    def primary_key( self, obj ):
        """Get the primary key of an object
        :param obj: the object to get the primary key from
        :return: a tuple with with components of the primary key, or none
            if the object has no primary key yet or any more.
        """
        if not self.is_persistent( obj ):
            return []
        # this function is called on compound objects as well, so the
        # mapper might be different from the mapper related to this admin
        mapper = orm.object_mapper(obj)
        return mapper.primary_key_from_instance( obj )

    def get_modifications( self, obj ):
        """Get the modifications on an object since the last flush.
        :param obj: the object for which to get the modifications
        :return: a dictionary with the changed attributes and their old
           value
        """
        state = orm.attributes.instance_state( obj )
        dict_ = state.dict
        modifications = dict()
        for attr in state.manager.attributes:
            if not hasattr( attr.impl, 'get_history' ):
                continue
            (added, unchanged, deleted) = \
                attr.impl.get_history(state, dict_, passive=orm.base.PASSIVE_NO_FETCH)
            if added or deleted:
                old_value = None
                if deleted:
                    old_value = deleted[0]
                    #
                    # in case of relations, get the primary key of the object
                    # instead of the object itself
                    #
                    try:
                        mapper = orm.class_mapper( type( old_value ) )
                        old_value = mapper.primary_key_from_instance( old_value )
                    except UnmappedClassError:
                        pass
                modifications[ attr.key ] = old_value
        return modifications

    def add( self, obj ):
        """Adds the entity instance to the default session, if it is not
        yet attached to a session"""
        session = Session.object_session( obj )
        if session == None:
            Session().add( obj )

    def delete(self, entity_instance):
        """Delete an entity instance"""
        session = Session.object_session( entity_instance )
        #
        # new and deleted instances cannot be deleted
        #
        if session:

            # First check the instance is allowed to be deleted and raise otherwise.
            self.deletable_or_raise(entity_instance)

            if entity_instance in session.new:
                session.expunge(entity_instance)
            elif entity_instance not in session.deleted:
                #
                # only if we know the primary key, we can keep track of its history
                #
                primary_key = self.primary_key( entity_instance )
                if not None in primary_key:
                    # save the state before the update
                    memento = self.get_memento()
                    if memento != None:
                        modifications = entity_to_dict( entity_instance )
                        change = memento_change( model = str( self.entity.__name__ ),
                                                 memento_type = 'before_delete',
                                                 primary_key = primary_key,
                                                 previous_attributes = modifications )
                        memento.register_changes( [change] )
                session.delete( entity_instance )
                session.flush()

    def expunge(self, entity_instance):
        """Expunge the entity from the session"""
        session = orm.object_session( entity_instance )
        if session:
            objects_to_expunge = set([entity_instance])
            self._expand_compounding_objects( objects_to_expunge )
            for obj in objects_to_expunge:
                if obj in session:
                    session.expunge( obj )

    def _expand_compounding_objects( self, objs ):
        """
        Given a set of objects, expand this set with all compounding objects.
        :param objs: a `set` of objects
        """
        assert isinstance( objs, set )
        additional_objects = set(objs)
        while additional_objects:
            objs.update( additional_objects )
            additional_objects.clear()
            for obj_to_flush in objs:
                related_admin = self.get_related_admin( type(obj_to_flush ) )
                for compounding_object in related_admin.get_compounding_objects( obj_to_flush ):
                    if compounding_object not in objs:
                        additional_objects.add( compounding_object )

    def flush(self, entity_instance):
        """Flush the pending changes of this entity instance to the backend"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        if session:
            objects_to_flush = set([entity_instance])
            self._expand_compounding_objects( objects_to_flush )
            #
            # Create a list of changes
            #
            changes = []
            for obj_to_flush in objects_to_flush:
                if obj_to_flush in session.dirty:
                    modifications = {}
                    try:
                        modifications = self.get_modifications( obj_to_flush )
                    except Exception as e:
                        # todo : there seems to be a bug in sqlalchemy that causes the
                        #        get history to fail in some cases
                        logger.error( 'could not get modifications from object', exc_info = e )
                    primary_key = self.primary_key( obj_to_flush )
                    if modifications and (None not in primary_key):
                        change = memento_change( model = str(type(obj_to_flush).__name__),
                                                 memento_type = 'before_update',
                                                 primary_key = primary_key,
                                                 previous_attributes = modifications )
                        changes.append( change )
            session.flush( objects_to_flush )
            #
            # If needed, track the changes
            #
            memento = self.get_memento()
            if changes and memento != None:
                memento.register_changes( changes )

    def refresh(self, entity_instance):
        """Undo the pending changes to the backend and restore the original
        state"""
        session = orm.object_session( entity_instance )
        if session:
            objects_to_refresh = set([entity_instance])
            self._expand_compounding_objects( objects_to_refresh )
            for obj in objects_to_refresh:
                if obj in session:
                    state = instance_state( obj )
                    if state.has_identity:
                        session.refresh( obj )
                    else:
                        session.expunge( obj )

    def is_persistent(self, obj):
        """:return: True if the object has a persisted state, False otherwise"""
        session = orm.object_session(obj)
        if session is not None:
            if obj in session.new:
                return False
            if obj in session.deleted:
                return False
            return True
        return False

    def is_dirty(self, obj):
        session = orm.object_session(obj)
        if session is not None:
            return (obj in session.dirty)
        return True
            
    def is_deleted(self, obj):
        """
        :return: True if the object has been deleted from the persistent
            state, False otherwise"""
        state = instance_state( obj )
        if state != None and state.deleted:
            return True
        return False

    def is_readable(self, obj):
        """
        :return: True if the object is readable, False otherwise.
            Deleted objects are not considered to be readable."""
        state = instance_state( obj )
        if state is None:
            return False
        if state.deleted or state.detached:
            return False
        return True

    def get_all_fields_and_attributes(self):
        """In addition to all the fields that are defined in the views
        or through the field_attributes, this method returns all the fields
        that have been mapped.
        """
        fields = super(EntityAdmin, self).get_all_fields_and_attributes()
        for mapper_property in self.mapper.iterate_properties:
            if isinstance(mapper_property, orm.properties.ColumnProperty):
                field_name = mapper_property.key
                fields[field_name] = self.get_field_attributes( field_name )
        return fields

    def _get_search_fields(self, substring):
        """
        Generate a list of fields in which to search.  By default this method
        returns the fields in the `list_search` attribute as well as the 
        properties that are mapped to a column in the database.  Any property that
        is not a simple Column might result in very slow searches, so those should
        be put explicitly in the `list_search` attribute.

        :param substring: that part of the complete search string for which
           the search fields are requested.  This allows analysis of the search
           string to improve the search behavior

        :return: a list with the names of the fields in which to search
        """
        if self._search_fields is None:
            self._search_fields = list(self.list_search)
            # list to avoid p3k fixes
            # Only include basic search columns if it is set as such (True by default).
            if self.basic_search:
                for field_name, col_property in list(self.mapper.column_attrs.items()):
                    if isinstance(col_property.expression, schema.Column):
                        search_strategy = self.get_field_attributes(field_name).get('search_strategy')
                        self._search_fields.append(search_strategy)
        return self._search_fields

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
        serialized = obj.to_dict(deep=self.copy_deep, exclude=[c.name for c in self.mapper.primary_key]+self.copy_exclude)
        #
        # make sure we don't move duplicated OneToMany relations from the
        # old object to the new, but instead duplicate them, by manipulating
        # the serialized structure
        #
        # @todo: this should be recursive
        for relationship_property in self.mapper.relationships:
            if relationship_property.direction == orm.interfaces.ONETOMANY:
                target = relationship_property.mapper.class_
                for relation in serialized.get(relationship_property.key, []):
                    relation_mapper = orm.class_mapper(target)
                    for primary_key_field in relation_mapper.primary_key:
                        # remove the primary key field, since setting it
                        # to None might overwrite a value set at object
                        # construction time
                        relation.pop(primary_key_field.name, None)
        #
        # deserialize into the new object
        #
        new_obj.from_dict( serialized )
        #
        # recreate the ManyToOne relations
        #
        for relationship_property in self.mapper.relationships:
            if relationship_property.direction == orm.interfaces.MANYTOONE:
                setattr( new_obj,
                         relationship_property.key,
                         getattr( obj, relationship_property.key ) )
        return new_obj

    def is_editable(self):
        """Return True if the Entity is editable.

        An entity is considered editable if there is no __entity_args__ { 'editable': False }
        """
        editable = self.entity._get_entity_arg('editable')
        if editable is None:
            return True
        return editable

    def _get_field_strategies(self, priority_level=None):
        """
        Return this admins available field filter strategies.
        By default, this returns the ´field_filter´ attribute, expanded with the corresponding filter strategies for this admin's entity mapper columns if basic filtering is enabled.
        """
        field_strategies = list(self.field_filter)
        # Only include filter strategies for basic columns if it is set as such (True by default).
        if self.basic_filters:
            for field_name, col_property in list(self.mapper.column_attrs.items()):
                if isinstance(col_property.expression, schema.Column):
                    field_attributes = self.get_field_attributes(field_name)
                    field_strategies.append(field_attributes.get('filter_strategy'))
        for relationship_property in self.mapper.relationships:
            if relationship_property.direction == orm.interfaces.MANYTOONE or relationship_property.uselist:
                field_attributes = self.get_field_attributes(relationship_property.key)
                field_strategies.append(field_attributes.get('filter_strategy'))

        if priority_level is not None:
            return [strategy for strategy in field_strategies if strategy.priority_level == priority_level]
        return field_strategies

    def get_discriminator_value(self, obj):
        return self.entity.get_discriminator_value(obj)

    def set_discriminator_value(self, obj, primary_discriminator_value, *secondary_discriminator_values):
        self.entity.set_discriminator_value(obj, primary_discriminator_value, *secondary_discriminator_values)
