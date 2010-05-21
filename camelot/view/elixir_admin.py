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
    """

    validator = EntityValidator

    @model_function
    def get_query(self):
        """:return: an sqlalchemy query for all the objects that should be
        displayed in the table or the selection view.  Overwrite this method to
        change the default query, which selects all rows in the database.
        """
        return self.entity.query

    @model_function
    def get_subclass_entity_admin(self, entity):
        """Get the admin class for an entity that is a subclass of this admin's
        entity or this admin's entity itself.
        """
        for subclass_admin in self.get_subclasses():
            if subclass_admin.entity == entity:
                return subclass_admin
        return self

    @model_function
    def get_subclasses(self):
        """Returns admin objects for the subclasses of the Entity represented
        by this admin object.
        """
        if not self._subclasses:
            from elixir import entities
            self._subclasses = [
                e.Admin(self.app_admin, e)
                for e in entities
                    if (
                        issubclass(e, (self.entity,))
                        and hasattr(e, 'Admin')
                        and e != self.entity
                    )
            ]
        return self._subclasses

    @model_function
    def get_verbose_identifier(self, obj):
        if hasattr(obj, 'id') and obj.id:
            if hasattr(obj, '__unicode__'):
                return u'%s %s : %s' % (
                    unicode(self.get_verbose_name()),
                    unicode(obj.id),
                    unicode(obj)
                )
            else:
                return u'%s %s' % (
                    self.get_verbose_name(),
                    unicode(obj.id)
                )
        else:
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
            from sqlalchemy.orm.exc import UnmappedClassError
            from field_attributes import _sqlalchemy_to_python_type_
            try:
                mapper = orm.class_mapper(self.entity)
            except UnmappedClassError, exception:
                from elixir import entities
                mapped_entities = [str(e) for e in entities]
                logger.error(u'%s is not a mapped class, mapped classes include %s'%(self.entity, u','.join([unicode(me) for me in mapped_entities])),
                             exc_info=exception)
                raise exception
            try:
                property = mapper.get_property(
                    field_name,
                    resolve_synonyms=True
                )
                if isinstance(property, orm.properties.ColumnProperty):
                    type = property.columns[0].type
                    python_type = _sqlalchemy_to_python_type_.get(
                        type.__class__,
                        None
                    )
                    if python_type:
                        attributes.update(python_type(type))
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
                            backref = property.backref.key,
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
                            #@todo: take into account all foreign keys instead
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
            except KeyError, _e:
                pass
            if has_default:
                #
                # prevent the setting of a default value when one has been
                # set allready
                #
                value = attributes['getter'](entity_instance)
                if value:
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
                except AttributeError, e:
                    logger.error(
                        'Programming Error : could not set'
                        ' attribute %s to %s on %s' % (
                            field,
                            default_value,
                            entity_instance.__class__.__name__
                        ),
                        exc_info=e
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
        from controls.tableview import TableView
        from art import Icon
        from proxy.queryproxy import QueryTableProxy
        from PyQt4.QtCore import SIGNAL

        class SelectQueryTableProxy(QueryTableProxy):
            header_icon = Icon('tango/16x16/emblems/emblem-symbolic-link.png')

        class SelectView(TableView):

            table_model = SelectQueryTableProxy
            title_format = 'Select %s'

            def __init__(self, admin, parent):
                TableView.__init__(
                    self, admin,
                    search_text=search_text, parent=parent
                )
                self.entity_selected_signal = SIGNAL('entity_selected')
                self.connect(self, SIGNAL('row_selected'), self.sectionClicked)
                self.setUpdatesEnabled(True)

            def emit_and_close(self, instance_getter):
                self.emit(self.entity_selected_signal, instance_getter)
                from camelot.view.workspace import get_workspace
                for window in get_workspace().subWindowList():
                    if hasattr(window, 'widget') and window.widget() == self:
                        window.close()

            def sectionClicked(self, index):
                # table model will be set by the model thread, we can't
                # decently select if it has not been set yet
                if self._table_model:

                    def create_constant_getter(cst):
                        return lambda:cst

                    def create_instance_getter():
                        entity = self._table_model._get_object(index)
                        return create_constant_getter(entity)

                    post(create_instance_getter, self.emit_and_close)

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

        :param parent: the workspace widget that will contain the table view
        """

        from PyQt4 import QtCore
        from PyQt4.QtCore import SIGNAL
        
        from proxy.queryproxy import QueryTableProxy
        tableview = self.TableView(self)

        def createOpenForm(self, tableview):

            def openForm(index):
                from workspace import get_workspace
                model = QueryTableProxy(
                    tableview.admin,
                    tableview._table_model.get_query_getter(),
                    tableview.admin.get_fields,
                    max_number_of_rows=1
                )
                title = ''
                formview = tableview.admin.create_form_view(
                    title, model, index, parent
                )
                get_workspace().addSubWindow(formview)
                formview.show()

            return openForm

        tableview.connect(
            tableview,
            SIGNAL('row_selected'),
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
                if hasattr(entity_instance, 'id') and entity_instance.id:
                    pk = entity_instance.id
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
        new_entity_instance.from_dict( entity_instance.to_dict(exclude=['id']) )
        return new_entity_instance        
