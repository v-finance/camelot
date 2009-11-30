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
from camelot.core.utils import ugettext as _
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
                    unicode(self.get_verbose_name().capitalize()),
                    unicode(obj.id),
                    unicode(obj)
                )
            else:
                return u'%s %s' % (
                    self.get_verbose_name().capitalize(),
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
            from camelot.view.controls import delegates
            #
            # Default attributes for all fields
            #
            attributes = dict(
                python_type = str,
                length = None,
                tooltip = None,
                background_color = None,
                minimal_column_width = 0,
                editable = False,
                nullable = True,
                widget = 'str',
                blank = True,
                delegate = delegates.PlainTextDelegate,
                validator_list = [],
                name = unicode(_(field_name.replace('_', ' '))).capitalize()
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
            mapper = orm.class_mapper(self.entity)
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

            # if name should be translated, do so now
            attributes['name'] = unicode(attributes['name']).capitalize()

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
    def set_defaults(self, entity_instance):
        """Set the defaults of an object"""
        from sqlalchemy.schema import ColumnDefault
        for field, attributes in self.get_fields():
            try:
                default = attributes['default']
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
            except KeyError, _e:
                pass

    @gui_function
    def create_new_view(admin, parent=None, oncreate=None, onexpunge=None):
        """Create a Qt widget containing a form to create a new instance of the
        entity related to this admin class

        The returned class has an 'entity_created_signal' that will be fired
        when a valid new entity was created by the form
        """
        from PyQt4 import QtCore
        from PyQt4 import QtGui
        from PyQt4.QtCore import SIGNAL
        from camelot.view.controls.view import AbstractView
        from proxy.collection_proxy import CollectionProxy
        new_object = []

        @model_function
        def collection_getter():
            if not new_object:
                entity_instance = admin.entity()
                if oncreate:
                    oncreate(entity_instance)
                # Give the default fields their value
                admin.set_defaults(entity_instance)
                new_object.append(entity_instance)
            return new_object

        model = CollectionProxy(
            admin,
            collection_getter,
            admin.get_fields,
            max_number_of_rows=1
        )
        validator = admin.create_validator(model)

        class NewForm(AbstractView):

            def __init__(self, parent):
                AbstractView.__init__(self, parent)
                self.widget_layout = QtGui.QVBoxLayout()
                self.widget_layout.setMargin(0)
                title = _('new')
                index = 0
                self.form_view = admin.create_form_view(
                    title, model, index, parent
                )
                self.widget_layout.insertWidget(0, self.form_view)
                self.setLayout(self.widget_layout)
                self.validate_before_close = True
                self.entity_created_signal = SIGNAL('entity_created')
                #
                # every time data has been changed, it could become valid,
                # when this is the case, it should be propagated
                #
                self.connect(
                    model,
                    SIGNAL(
                        'dataChanged(const QModelIndex &, const QModelIndex &)'
                    ),
                    self.dataChanged
                )
                self.connect(
                    self.form_view,
                    AbstractView.title_changed_signal,
                    self.change_title
                )

            def emit_if_valid(self, valid):
                if valid:

                    def create_instance_getter(new_object):
                        return lambda:new_object[0]

                    self.emit(
                        self.entity_created_signal,
                        create_instance_getter(new_object)
                    )

            def dataChanged(self, index1, index2):

                def validate():
                    return validator.isValid(0)

                post(validate, self.emit_if_valid)

            def showMessage(self, valid):
                from camelot.view.workspace import get_workspace
                if not valid:
                    row = 0
                    reply = validator.validityDialog(row, self).exec_()
                    if reply == QtGui.QMessageBox.Discard:
                        # clear mapping to prevent data being written again to
                        # the model, after we reverted the row
                        self.form_view.widget_mapper.clearMapping()

                        def onexpunge_on_all():
                            if onexpunge:
                                for o in new_object:
                                    onexpunge(o)

                        post(onexpunge_on_all)
                        self.validate_before_close = False

                        for window in get_workspace().subWindowList():
                            if window.widget() == self:
                                window.close()
                else:
                    def create_instance_getter(new_object):
                        return lambda:new_object[0]

                    for _o in new_object:
                        self.emit(
                            self.entity_created_signal,
                            create_instance_getter(new_object)
                        )
                    self.validate_before_close = False
                    from camelot.view.workspace import NoDesktopWorkspace
                    workspace = get_workspace()
                    if isinstance(workspace, (NoDesktopWorkspace,)):
                        self.close()
                    else:
                        for window in get_workspace().subWindowList():
                            if window.widget() == self:
                                window.close()

            def validateClose(self):
                logger.debug(
                    'validate before close : %s' %
                    self.validate_before_close
                )
                if self.validate_before_close:
                    self.form_view.widget_mapper.submit()
                    logger.debug(
                        'unflushed rows : %s' %
                        str(model.hasUnflushedRows())
                    )
                    if model.hasUnflushedRows():
                        def validate(): return validator.isValid(0)
                        post(validate, self.showMessage)
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
        if hasattr(admin, 'form_size'):
            form.setMinimumSize(admin.form_size[0], admin.form_size[1])
        return form

    @gui_function
    def create_select_view(admin, query, search_text=None, parent=None):
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
            header_icon = Icon(
                'tango/16x16/emblems/emblem-symbolic-link.png'
            ).getQIcon()

        class SelectView(TableView):

            query_table_proxy = SelectQueryTableProxy
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
        from controls.tableview import TableView
        from proxy.queryproxy import QueryTableProxy
        tableview = TableView(self)

        def createOpenForm(self, tableview):

            def openForm(index):
                from workspace import get_workspace
                model = QueryTableProxy(
                    tableview.admin,
                    tableview._table_model._query_getter,
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
                Session.object_session( entity_instance ).flush( [entity_instance] )
                Session.object_session( history ).flush( [history] )

    @model_function
    def flush(self, entity_instance):
        """Flush the pending changes of this entity instance to the backend"""
        from sqlalchemy.orm.session import Session
        Session.object_session( entity_instance ).flush( [entity_instance] )
