#  ============================================================================
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
#  ============================================================================

import logging
logger = logging.getLogger('camelot.view.elixir_admin')

import sqlalchemy.sql.expression

from camelot.admin.object_admin import ObjectAdmin
from camelot.view.model_thread import post, model_function, gui_function
from camelot.core.utils import ugettext_lazy
from camelot.admin.validator.entity_validator import EntityValidator


class EntityAdmin(ObjectAdmin):
    """Admin class specific for classes that are mapped by sqlalchemy.
This allows for much more introspection than the standard ObjectAdmin.
    
It has additional class attributes that customise its behaviour.

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

.. image:: ../_static/filter/group_box_filter.png


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
 
    """

    list_search = []
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
        return self.entity.query

    @model_function
    def get_verbose_identifier(self, obj):
        if obj:
            primary_key = self.mapper.primary_key_from_instance(obj)
            if not None in primary_key:
                primary_key_representation = u','.join([unicode(v) for v in primary_key])
                if hasattr(obj, '__unicode__'):
                    return u'%s %s : %s' % (
                        unicode(self.get_verbose_name()),
                        primary_key_representation,
                        unicode(obj)
                    )
                else:
                    return u'%s %s' % (
                        self.get_verbose_name(),
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

            def get_entity_admin(target):
                """Helper function that instantiated an Admin object for a
                target entity class.

                :param target: an entity class for which an Admin object is
                needed.
                """
                try:
                    fa = self.field_attributes[field_name]
                    target = fa.get('target', target)
                    admin_class = fa['admin']
                    return admin_class(self.app_admin, target)
                except KeyError:
                    return self.get_related_entity_admin(target)
            #
            # Get the default field_attributes trough introspection if the
            # field is a mapped field
            #
            from sqlalchemy import orm
            from sqlalchemy.exceptions import InvalidRequestError
            from field_attributes import _sqlalchemy_to_python_type_

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
                    if not isinstance(
                        property.columns[0],
                        sqlalchemy.sql.expression._Label
                    ):
                        attributes['nullable'] = property.columns[0].nullable
                        attributes['default'] = property.columns[0].default
                elif isinstance(property, orm.properties.PropertyLoader):
                    target = property._get_target().class_
                    foreign_keys = list(property._foreign_keys)
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

            #
            # Overrule introspected field_attributes with those defined
            #
            attributes.update(forced_attributes)

            #
            # In case of a 'target' field attribute, instantiate an appropriate
            # 'admin' attribute
            #
            if 'target' in attributes:
                attributes['admin'] = get_entity_admin(attributes['target'])
            
            self._field_attributes[field_name] = attributes
            return attributes

    @model_function
    def get_list_charts(self):
        return self.list_charts

    @model_function
    def get_filters(self):
        """Returns the filters applicable for these entities each filter is

        :return: [(filter_name, [(option_name, query_decorator), ...), ... ]
        """
        from filters import structure_to_filter

        def filter_generator():
            for structure in self.list_filter:
                filter = structure_to_filter(structure)
                yield (filter, filter.get_name_and_options(self))

        return list(filter_generator())

    @model_function
    def set_defaults(self, entity_instance, include_nullable_fields=True):
        """Set the defaults of an object
        :param include_nullable_fields: also set defaults for nullable fields, depending
        on the context, this should be set to False to allow the user to set the field
        to None
        """
        from sqlalchemy.schema import ColumnDefault
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
                # set allready
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
        from art import Icon
        from proxy.queryproxy import QueryTableProxy
        from PyQt4 import QtCore

        class SelectQueryTableProxy(QueryTableProxy):
            header_icon = Icon('tango/16x16/emblems/emblem-symbolic-link.png')

        class SelectView(admin.TableView):
            table_model = SelectQueryTableProxy
            entity_selected_signal = QtCore.pyqtSignal(object)
            title_format = 'Select %s'

            def __init__(self, admin, parent):
                super(SelectView, self).__init__(
                    admin,
                    search_text=search_text, parent=parent
                )
                self.row_selected_signal.connect( self.sectionClicked )
                self.setUpdatesEnabled(True)

            def emit_entity_selected(self, instance_getter):
                self.entity_selected_signal.emit( instance_getter )

            @QtCore.pyqtSlot(int)
            def sectionClicked(self, index):
                # table model will be set by the model thread, we can't
                # decently select if it has not been set yet
                if self._table_model:

                    def create_constant_getter(cst):
                        return lambda:cst

                    def create_instance_getter():
                        entity = self._table_model._get_object(index)
                        return create_constant_getter(entity)

                    post(create_instance_getter, self.emit_entity_selected)

        widget = SelectView(admin, parent)
        widget.setUpdatesEnabled(True)
        widget.setMinimumSize(admin.list_size[0], admin.list_size[1])
        widget.update()
        return widget

    @gui_function
    def create_table_view(self, query_getter=None, parent=None):
        """Returns a Qt widget containing a table view, for a certain query,
        using this Admin class; the table widget contains a model
        QueryTableModel

        :param query_getter: sqlalchemy query object

        :param parent: the widget that will contain the table view
        """
        from camelot.view.workspace import show_top_level

        from proxy.queryproxy import QueryTableProxy
        tableview = self.TableView(self)

        def createOpenForm(self, tableview):

            def openForm(index):
                model = QueryTableProxy(
                    tableview.admin,
                    tableview._table_model.get_query_getter(),
                    tableview.admin.get_fields,
                    max_number_of_rows=1
                )
                title = ''
                formview = tableview.admin.create_form_view(
                    title, model, index, parent=None
                )
                show_top_level( formview, tableview )
                # @todo: dirty trick to keep reference
                #self.__form = formview

            return openForm

        tableview.row_selected_signal.connect(
            createOpenForm(self, tableview)
        )

        return tableview

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
                 (entity_instance in session): # if the object is not in the session, it might allready be deleted
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
    def flush(self, entity_instance):
        """Flush the pending changes of this entity instance to the backend"""
        from sqlalchemy.orm.session import Session
        session = Session.object_session( entity_instance )
        if not session:
            logger.error('Programming Error : entity %s cannot be flushed because it has no session'%(unicode(entity_instance)))
        session.flush( [entity_instance] )


    @model_function
    def copy(self, entity_instance):
        """Duplicate this entity instance"""
        new_entity_instance = entity_instance.__class__()
        new_entity_instance.from_dict( entity_instance.to_dict(exclude=[c.name for c in self.mapper.primary_key]) )
        return new_entity_instance
