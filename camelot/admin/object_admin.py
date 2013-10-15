#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""Admin class for Plain Old Python Object"""

import logging
logger = logging.getLogger('camelot.view.object_admin')

from camelot.admin.action.list_action import OpenFormView
from camelot.admin.action.form_action import CloseForm
from camelot.view.controls.tableview import TableView
from camelot.view.utils import to_string
from camelot.core.utils import ugettext_lazy, ugettext as _
from camelot.view.proxy.collection_proxy import CollectionProxy
from validator.object_validator import ObjectValidator
from PyQt4 import QtCore

class FieldAttributesList(list):
    """A list with field attributes that documents them for
    sphinx"""

    def __init__(self, original_list):
        """:param original_list: the list with field attributes
        to document"""
        super(FieldAttributesList, self).__init__(original_list)
        template = "\n * :ref:`%s <field-attribute-%s>`"
        doc = '\n'.join([template%(name, name) for name in original_list])
        self.__doc__ = doc

DYNAMIC_FIELD_ATTRIBUTES = FieldAttributesList(['tooltip', 'color', 'background_color',
                                                'editable', 'choices',
                                                'prefix', 'suffix', 'arrow',
                                                'new_message',
                                                'precision'])


class ObjectAdmin(object):
    """The ObjectAdmin class describes the interface that will be used
to interact with objects of a certain class.  The behaviour of this class
and the resulting interface can be tuned by specifying specific class
attributes:

**The name used in the GUI**

The name used in the GUI for things like window titles and such can
be specified using the verbose_name attribute.

.. attribute:: verbose_name

    A human-readable name for the object, singular ::

        verbose_name = _('movie')

    If this isn't given, the class name will be used

.. attribute:: verbose_name_plural

    A human-readable name for the object, plural ::

        verbose_name_plural = _('movies')

    If this isn't given, Camelot will use verbose_name + "s"

**Fields displayed**

.. attribute:: list_display

    a list with the fields that should be displayed in a table view
    
.. attribute:: lines_per_row

    An integer number specifying the height of a row in the table view, expressed
    as the number of lines of text it should be able to display.  Defaults to 1.

.. attribute:: form_display

    a list with the fields that should be displayed in a form view, defaults to
    the same fields as those specified in list_display ::

        class Admin(EntityAdmin):
            form_display = ['title', 'rating', 'cover']

    instead of telling which fields to display. It is also possible to define
    the form itself ::

        from camelot.view.forms import Form, TabForm, WidgetOnlyForm, HBoxForm

        class Admin(EntityAdmin):
            form_display = TabForm([
            ('Movie', Form([
              HBoxForm([['title', 'rating'], WidgetOnlyForm('cover')]),
              'short_description',
              'releasedate',
              'director',
              'script',
              'genre',
              'description', 'tags'], scrollbars=True)),
            ('Cast', WidgetOnlyForm('cast'))
          ])

**Behaviour**

.. attribute:: list_action

   The :class:`camelot.admin.action.base.Action` that will be triggered when the
   user selects an item in a list of objects.  This defaults to 
   :class:`camelot.admin.action.list_action.OpenFormView`, which opens a form
   for the current object.
   
.. attribute:: form_close_action

    The action triggered when the form window is closed by the operating system or the window manager.  By default this is the
    :class:`camelot.admin.action.form_action.CloseForm` action, which validates
    the form and allows the user to discard the changes when the form is invalid.  To change the form close action in the 
    toolbar, the :meth:`camelot.admin.object_admin.ObjectAdmin.get_form_actions` method should be overwritten.
    
.. attribute:: save_mode

    Specifies when the data should be send from the view to the model and flushed
    to the database.  The default mode is 'on_change', meaning that every change
    in the view will be send immediately to the database.  Other possibilities are :

      * 'on_leave' : the data will be send from the view to the model when the view
                     is closed, eg. : the form is closed.

.. attribute:: delete_mode

    Indicates if the deletion of an object should be confirmed by the user, defaults
    to 'on_request', indicating object should be deleted when the user hits the trash
    button.  Other possibilities are :

      * 'on_confirm' : the user will be asked for confirmation before the delete
        takes place.

.. attribute:: form_size

    a tuple indicating the size of a form view, defaults to (700,500)

.. attribute:: form_actions

    Actions to be accessible by pushbuttons on the side of a form, a list of :class:`camelot.admin.action.base.Action` objects. ::

        class Admin( EntityAdmin ):
            form_actions = [CloseForm()]
            
    These actions will be triggered with a :class:`camelot.admin.action.form_action.FormActionModelContext` as the `model_context` parameter
    in the :meth:`camelot.admin.action.base.Action.model_run` method.
            
.. attribute:: related_toolbar_actions

    list of actions that appear in the toolbar of a `OneToMany` editor.

.. attribute:: drop_action

    the action that is triggered when a drag and drop occured on the table
    view 
    
**Field attributes**

.. attribute:: field_attributes

    A dictionary specifying for each field of the model some additional
    attributes on how they should be displayed.  All of these attributes
    are propagated to the constructor of the delegate of this field::

        class Movie( Entity ):
        
            title = Column( Unicode(50) )
    
            class Admin( EntityAdmin ):
                list_display = ['title']
                field_attributes = { 'title' : {'editable':False} }

    The :ref:`doc-admin-field_attributes` documentation describes the various keys
    that can be used in the field attributes class attribute of an ObjectAdmin 
    or EntityAdmin.

**Window state**

.. attribute:: form_state

    Set this attribute to `maximized` or `minimized` for respective behaviour ::

        class Movie( Entity ):
        
            title = Column( Unicode(50) )
    
            class Admin( EntityAdmin ):
                list_display = ['title']
                form_state = 'maximized'

**Varia**

.. attribute:: name

    The name of the group in settings in which user dependent settings will
    be stored, defaults to the class name for which this Admin class is used.
    
    """
    
    name = None
    verbose_name = None
    verbose_name_plural = None
    list_display = []
    lines_per_row = 1
    validator = ObjectValidator
    model = CollectionProxy
    fields = []
    form_display = []
    form_close_action = CloseForm()
    list_filter = []
    list_action = OpenFormView()
    list_actions = []
    list_size = (600, 600)
    form_size = None
    form_actions = []
    related_toolbar_actions = []
    field_attributes = {}
    form_state = None
    icon = None # Default
    #
    # Behavioral attributes
    # 
    drop_action = None
    save_mode = 'on_edit'
    delete_mode = 'on_request'

    TableView = TableView

    def __init__( self, app_admin, entity ):
        """
        :param app_admin: the application admin object for this application, 
            if None, then the default application_admin is taken
        :param entity: the entity class for which this admin instance is to be
            used
        """
        if not app_admin:
            from camelot.admin.application_admin import get_application_admin
            self.app_admin = get_application_admin()
        else:
            self.app_admin = app_admin
        if entity:
            self.entity = entity
        #
        # caches to prevent recalculation of things
        #
        self._field_attributes = dict()
        self._subclasses = None

    def __str__(self):
        return 'Admin %s' % str(self.entity.__name__)

    def __repr__(self):
        return 'ObjectAdmin(%s)' % str(self.entity.__name__)

    def get_name(self):
        """ The name of the group in settings in which user dependent settings 
        will be stored, this is either the `name` attribute of this class or, 
        the class name of the class for which this Admin class is used.
        
        :return: a string with the name of the settings group        
        """
        return self.name or self.entity.__name__

    def get_verbose_name(self):
        
#        def uncamelize(text):
#            def downcase(matchobj):
#                return "_" + matchobj.group(0).lower()
#            if text:
#                text = text[0].lower() + re.sub(r'([A-Z])', downcase, text[1:])
#            return text 

        return unicode(
            self.verbose_name or _(self.entity.__name__.capitalize())
        )

    def get_verbose_name_plural(self):
        return unicode(
            self.verbose_name_plural
            or (self.get_verbose_name() + 's')
        )
        
    def get_icon(self):
        return self.icon

    def get_verbose_identifier(self, obj):
        """Create an identifier for an object that is interpretable
        for the user, eg : the primary key of an object.  This verbose identifier can
        be used to generate a title for a form view of an object.
        """
        return u'%s : %s' % (self.get_verbose_name(), unicode(obj))

    def get_entity_admin(self, entity):
        return self.app_admin.get_entity_admin(entity)

    def get_save_mode(self):
        return self.save_mode
    
    def get_settings( self ):
        """A settings object in which settings related to this admin can be
        stored.
        
        :return: a :class:`QtCore.QSettings` object
        """
        settings = self.app_admin.get_settings()
        settings.beginGroup( self.get_name()[:255] )
        return settings
    
    def get_memento( self ):
        return self.app_admin.get_memento()

    def get_delete_mode(self):
        return self.delete_mode

    def get_delete_message(self, obj):
        return _('Are you sure you want to delete this')

    def get_form_actions( self, obj=None ):
        """Specify the list of action buttons that should appear on the side
        of the form view.
        
        :param obj: the object displayed in the form (Deprecated, use action
            states to make the appearance of actions dynamic on a form)
        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        app_admin = self.get_application_admin()
        from camelot.admin.action.form_action import structure_to_form_actions
        return app_admin.get_form_actions() + structure_to_form_actions( self.form_actions )
    
    def get_form_toolbar_actions( self, toolbar_area ):
        """
        By default this function will return the same as :meth:`camelot.admin.application_admin.ApplicationAdmin.get_form_toolbar_actions`
        
        :param toolbar_area: an instance of :class:`Qt.ToolBarArea` indicating
            where the toolbar actions will be positioned
            
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of a form view.  return
            None if no toolbar should be created.
        """        
        app_admin = self.get_application_admin()
        return app_admin.get_form_toolbar_actions( toolbar_area )

    def get_related_toolbar_actions( self, toolbar_area, direction ):
        """Specify the toolbar actions that should appear in a OneToMany editor.
        
        :param toolbar_area: the position of the toolbar
        :param direction: the direction of the relation : 'onetomany' or 
            'manytomany'
            
        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        app_admin = self.get_application_admin()
        return self.related_toolbar_actions or \
               app_admin.get_related_toolbar_actions( toolbar_area, direction )
    
    def get_list_actions(self):
        return self.list_actions
    
    def get_list_action(self):
        """Get the action that should be triggered when an object is selected
        in a table of objects.
        
        :return: by default returns the `list_action` attribute
        """
        return self.list_action

    def get_depending_objects(self, obj):
        """Overwrite this function to generate a list of objects that depend on a given
        object.  When obj is modified by the user, this function will be called to determine
        which other objects need their views updated.

        :param obj: an object of the type that is managed by this admin class
        :return: an iterator over objects that depend on obj
        """
        return []
    
    def get_compounding_objects(self, obj):
        """Overwrite this function to generate a list of objects out of which
        `obj` is build.  These objects will be validated if `obj` is 
        validated.  The effect of returning compounding objects will be :
        
          * `obj` will only be valid if all its compounding object
            are valid as well.
            
          * default values will be set for the attributes of the compounding
            objects
            
          * when an object is expired or refreshed, all its compounding objects
            will be expired and refreshed as well
            
        """
        return []

    def get_subclass_tree( self ):
        """Get a tree of admin classes representing the subclasses of the class
        represented by this admin class

        :return: [(subclass_admin, [(subsubclass_admin, [...]),...]),...]
        """
        subclasses = []
        for subclass in self.entity.__subclasses__():
            subclass_admin = self.get_related_admin( subclass )
            if subclass_admin!=self:
                subclasses.append((
                    subclass_admin,
                    subclass_admin.get_subclass_tree()
                ))

        def sort_admins(a1, a2):
            return cmp(a1[0].get_verbose_name_plural(), a2[0].get_verbose_name_plural())

        subclasses.sort(cmp=sort_admins)
        return subclasses

    def get_related_admin(self, cls):
        """Get an admin object for another object class.  Taking into account
        preferences of this admin object or for those of admin object higher up
        the chain such as the application admin object.

        :param cls: the class for which an admin object is requested
        """
        if cls == self.entity:
            return self
        related_admin = self.app_admin.get_entity_admin(cls)
        if not related_admin:
            logger.warn('no related admin found for %s' % (cls.__name__))
        return related_admin
        
    def get_static_field_attributes(self, field_names):
        """
        Convenience function to get all the field attributes
        that are static (don't depend on the object being visualized).  This
        method is only called once for a table or form view, independent of
        the number of objects/records being visualized.

        :param field_names: a list of field names
        :return: [{field_attribute_name:field_attribute_value, ...}, {}, ...]

        The returned list has the same order than the requested
        field_names.
        """
        for field_name in field_names:
            field_attributes = self.get_field_attributes(field_name)
            static_field_attributes = {}
            for name, value in field_attributes.items():
                if name not in DYNAMIC_FIELD_ATTRIBUTES or not callable(value):
                    static_field_attributes[name] = value
            yield static_field_attributes

    def get_dynamic_field_attributes(self, obj, field_names):
        """
        Convenience function to get all the field attributes
        that are dynamic (depend on the object being visualized). This method
        is called once for each object/row in a table view and once for
        each object being visualized in a form view.

        :param field_names: a list of field names
        :param obj: the object at the row for which to get the values of the dynamic field attributes
        :return: [{field_attribute_name:field_attribute_value, ...}, {}, ...]

        The returned list has the same order than the requested
        field_names.  A reimplementation of this method can look like::
        
            def get_dynamic_field_attributes(self, obj, field_names):
                for field_attributes in super( MyAdmin, self ).get_dynamic_field_attributes(obj, field_names):
                    if obj.status == 'finished':
                        field_attributes['editable'] = True
                    else:
                        field_attributes['editable'] = False
                    yield field_attributes
                
        """
        for field_name in field_names:
            field_attributes = self.get_field_attributes(field_name)
            dynamic_field_attributes = {'obj':obj}
            for name, value in field_attributes.items():
                if name not in DYNAMIC_FIELD_ATTRIBUTES:
                    continue
                if name in ('default',):
                    # the default value of a field is not needed in the GUI,
                    # and the continuous evaluation of it might be expensive,
                    # as it might be the max of a column
                    continue
                if callable(value):
                    return_value = None
                    try:
                        return_value = value(obj)
                    except (ValueError, Exception, RuntimeError, TypeError, NameError), exc:
                        logger.error(u'error in field_attribute function of %s'%name, exc_info=exc)
                    finally:
                        dynamic_field_attributes[name] = return_value
            yield dynamic_field_attributes

    def get_field_attributes(self, field_name):
        """
        Get the attributes needed to visualize the field field_name.  This
        function is called by get_static_field_attributes and
        get_dynamic_field_attributes.

        This function first tries to fill the dictionary with field
        attributes for a field with those gathered through introspection,
        and then updates them with those found in the field_attributes
        class attribute.

        :param field_name: the name of the field
        :return: a dictionary of attributes needed to visualize the field

        The values of the returned dictionary either contain the value
        of the field attribute, or in the case of dynamic field attributes,
        a function that returns the value of the field attribute.
        """
        #
        # @todo : this function should return a frozen dictionary, so no
        #         other parts of the application can modify the cached field
        #         attributes
        #
        try:
            return self._field_attributes[field_name]
        except KeyError:
            from camelot.view.controls import delegates
            #
            # Default attributes for all fields
            #
            attributes = dict(
                to_string = to_string,
                field_name=field_name,
                python_type=str,
                length=None,
                tooltip=None,
                background_color=None,
                #minimal_column_width=12,
                editable=False,
                nullable=True,
                widget='str',
                blank=True,
                delegate=delegates.PlainTextDelegate,
                validator_list=[],
                name=ugettext_lazy(field_name.replace( '_', ' ' ).capitalize())
            )
            self._expand_field_attributes(attributes, field_name)
            self._field_attributes[field_name] = attributes
            return attributes

    def _expand_field_attributes(self, field_attributes, field_name):
        """Given a set field attributes, expand the set with attributes
        derived from the given attributes and those forced through the
        `field_attributes` class attribute.
        """
        #
        # Field attributes forced by the field_attributes property
        #
        forced_attributes = self.field_attributes.get(field_name, {})
        field_attributes.update(forced_attributes)
        #
        # If no column_width is specified, try to derive one
        #
        if field_attributes.get('column_width', None) is None:
            length = min(field_attributes.get('length', 0) or 0, 50)
            field_attributes['column_width'] = max( 
                field_attributes.get('minimal_column_width', 0),
                2 + len(unicode(field_attributes['name'])),
                length
                )
        #
        # If there is an `admin` field attribute, instantiate it
        #
        target = field_attributes.get('target', None)
        if target is not None:
            admin = field_attributes.get('admin', None)
            if admin is not None:
                field_attributes['admin'] = admin(self, target)
            #
            # In case of a 'target' field attribute, add an appropriate
            # 'admin' attribute
            #
            else:
                field_attributes['admin'] = self.get_related_admin(target)

    def get_table( self ):
        """The definition of the table to be used in a list view
        :return: a `camelot.admin.table.Table` object
        """
        from camelot.admin.table import structure_to_table
        table = structure_to_table( self.list_display )
        return table
    
    def get_columns(self):
        """
        The columns to be displayed in the list view, returns a list of pairs
        of the name of the field and its attributes needed to display it
        properly

        @return: [(field_name,
                  {'widget': widget_type,
                   'editable': True or False,
                   'blank': True or False,
                   'validator_list':[...],
                   'name':'Field name'}),
                 ...]
        """
        table = self.get_table()
        return [(field, self.get_field_attributes(field))
                for field in table.get_fields() ]

    def get_validator( self, model = None, initial_validation = False ):
        """Get a validator object
        
        :return: a :class:`camelot.admin.validator.object_validator.Validator`
        """
        return self.validator( self, 
                               model = model, 
                               initial_validation = initial_validation )

    def get_fields(self):
        fields = self.get_form_display().get_fields()
        fields_and_attributes =  [
                (field, self.get_field_attributes(field))
                for field in fields
        ]
        return fields_and_attributes

    def get_application_admin( self ):
        """Provide access to the :class:`ApplicationAdmin`
        
        :return: the :class:`camelot.admin.application_admin.ApplicationAdmin`
            object for the application.
        """
        return self.app_admin.get_application_admin()

    def get_all_fields_and_attributes(self):
        """A dictionary of (field_name:field_attributes) for all fields that can
        possibly appear in a list or a form or for which field attributes have
        been defined
        """
        fields = dict(self.get_columns())
        fields.update(dict(self.get_fields()))
        return fields

    def get_filters(self):
        return []

    def get_form_display(self):
        from camelot.view.forms import Form, structure_to_form
        if self.form_display:
            return structure_to_form(self.form_display)
        if self.list_display:
            return Form( self.get_table().get_fields() )
        return Form([])

    def _apply_form_state(self, widget):
        """apply the consequences of the form_state class attribute
        to a widget"""
        if hasattr(self, 'form_state'):
            from camelot.core import constants
            if self.form_state == constants.MAXIMIZED:
                widget.setWindowState(QtCore.Qt.WindowMaximized)
            if self.form_state == constants.MINIMIZED:
                widget.setWindowState(QtCore.Qt.WindowMinimized)

    def set_field_value(self, obj, field_name, value):
        """Set the value of a field on an object.  By default this method calls
        the builtin :func:`setattr` function.
        
        :param obj: the object on which to set the value
        :param field_name: the name of the field, which by default will be used
            as the name of the attribute to set
        :param value: the value to set
        """
        setattr(obj, field_name, value)
        
    def set_defaults(self, object_instance, include_nullable_fields=True):
        """Set the defaults of an object
        :param include_nullable_fields: also set defaults for nullable fields, 
        depending on the context, this should be set to False to allow the user 
        to set the field to None
        """
        from sqlalchemy.schema import ColumnDefault
        
        if self.is_deleted( object_instance ):
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
                value = getattr(object_instance, field)
                if value not in (None, []):
                    # False is a legitimate value for Booleans, but a 
                    # one-to-many field might have a default value as well
                    continue
                if isinstance(default, ColumnDefault):
                    if default.is_scalar:
                        # avoid trip to database
                        default_value = default.arg
                    else:
                        default_value = default.execute()
                elif callable(default):
                    import inspect
                    args, _varargs, _kwargs, _defs = \
                        inspect.getargspec(default)
                    if len(args):
                        default_value = default(object_instance)
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
                    setattr(object_instance, field, default_value)
                except AttributeError, exc:
                    logger.error(
                        'Programming Error : could not set'
                        ' attribute %s to %s on %s' % (
                            field,
                            default_value,
                            object_instance.__class__.__name__
                        ),
                        exc_info=exc
                    )
        for compounding_object in self.get_compounding_objects( object_instance ):
            self.get_related_admin( type( compounding_object ) ).set_defaults( compounding_object )

    def primary_key( self, obj ):
        """Get the primary key of an object
        :param obj: the object to get the primary key from
        :return: a tuple with with components of the primary key, or an
            emtpy list if the object has no primary key yet or any more.
        """
        return []
    
    def get_modifications( self, obj ):
        """Get the modifications on an object since the last flush.
        :param obj: the object for which to get the modifications
        :return: a dictionary with the changed attributes and their old
           value
        """
        return dict()
    
    def delete(self, entity_instance):
        """Delete an entity instance"""
        del entity_instance

    def flush(self, entity_instance):
        """Flush the pending changes of this entity instance to the backend"""
        pass
    
    def expunge(self, entity_instance):
        """Remove this object from the objects being managed"""
        pass

    def refresh(self, entity_instance):
        """Undo the pending changes to the backend and restore the original
        state"""
        pass

    def add(self, entity_instance):
        """Add an entity instance as a managed entity instance"""
        pass

    def is_deleted(self, _obj):
        """
        :return: True if the object has been deleted from the persistent
            state, False otherwise"""
        return False
    
    def is_persistent(self, _obj):
        """:return: True if the object has a persisted state, False otherwise"""
        return False
    
    def copy(self, entity_instance):
        """Duplicate this entity instance"""
        new_entity_instance = entity_instance.__class__()
        return new_entity_instance

