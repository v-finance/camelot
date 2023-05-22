# -*- coding: utf-8 -*-
import datetime
import os
import tempfile
import unittest

from camelot.core.conf import SimpleSettings, settings
from camelot.core.memento import SqlMemento, memento_change, memento_types
from camelot.core.naming import (
    AlreadyBoundException, BindingType, Constant, ConstantNamingContext, EntityNamingContext,
    ImmutableBindingException, initial_naming_context, InitialNamingContext,
    NameNotFoundException, NamingContext, NamingException, UnboundException, WeakRefNamingContext,
)
from camelot.core.orm import Entity, EntityBase, Session
from camelot.core.profile import Profile, ProfileStore
from camelot.core.qt import QtCore, py_to_variant, variant_to_py
from camelot.core.singleton import QSingleton
from camelot.core.sql import metadata
from camelot.model import party

from decimal import Decimal
from sqlalchemy import MetaData, schema, types
from sqlalchemy.ext.declarative import declarative_base

from .test_model import ExampleModelMixinCase, LoadSampleData
from .test_orm import EntityMetaMock

memento_id_counter = 0
session_id = str(Session().hash_key)

class MementoCase(unittest.TestCase, ExampleModelMixinCase):
    """test functions from camelot.core.memento
    """
    
    def setUp( self ):
        super( MementoCase, self ).setUp()
        self.setup_sample_model()
        global memento_id_counter
        custom_memento_types = memento_types + [(100, 'custom')]
        self.memento = SqlMemento( memento_types = custom_memento_types )
        memento_id_counter += 1
        self.id_counter = memento_id_counter
        self.model = 'TestMemento'

    def tearDown(self):
        self.tear_down_sample_model()

    def test_lifecycle( self ):
        memento_changes = [
            memento_change( self.model, 
                            [self.id_counter], 
                            None, 'create' ),            
            memento_change( self.model, 
                            [self.id_counter], 
                            {'name':'foo'}, 'before_update' ),
            memento_change( self.model, 
                            [self.id_counter], 
                            {'name':'bar'}, 'before_delete' ),            
            ]
        
        self.memento.register_changes( memento_changes )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {} ) )
        self.assertEqual( len(changes), 3 )
        
    def test_no_error( self ):
        memento_changes = [
            memento_change( None, 
                            [self.id_counter], 
                            None, None ),                     
            ]
        self.memento.register_changes( memento_changes )
        
    def test_custom_memento_type( self ):
        memento_changes = [
            memento_change( self.model, 
                            [self.id_counter], 
                            {}, 'custom' ),                     
            ]
        self.memento.register_changes( memento_changes )
        changes = list( self.memento.get_changes( self.model,
                                                  [self.id_counter],
                                                  {} ) )
        self.assertEqual( len(changes), 1 )
       
class ProfileCase(unittest.TestCase):
    """Test the save/restore and selection functions of the database profile
    """
    
    def setUp( self ):
        # Tests executed by the launcher should not use the vfinance QSettings
        QtCore.QCoreApplication.setApplicationName('camelot-tests')

    def test_profile_state( self ):
        name, host, password = u'profile_tést', u'192.168.1.1', u'top-sécrèt'
        profile = Profile( name=name, host=host, password=password )
        state = profile.__getstate__()
        # name should not be encrypted, others should
        self.assertEqual( state['profilename'], name )
        self.assertEqual( state['host'], host )
        self.assertEqual( state['pass'], password )
        new_profile = Profile(name=None)
        new_profile.__setstate__( state )
        self.assertEqual( new_profile.name, name )
        self.assertEqual( new_profile.host, host )
        self.assertEqual( new_profile.password, password )

    def test_registry_settings(self):
        # construct a profile store from application settings
        store = ProfileStore()
        store.read_profiles()
        # continue test with a profile store from file, to avoid test inference

    def test_profile_store( self ):
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        store = ProfileStore(filename)
        self.assertEqual( store.read_profiles(), [] )
        self.assertEqual( store.get_last_profile(), None )
        profile_1 = Profile('prôfile_1')
        profile_1.dialect = 'sqlite'
        profile_1.locale_language = 'en_US'
        profile_2 = Profile('prôfile_2')
        profile_2.dialect = 'mysql'
        profile_2.locale_language = 'en_GB'
        store.write_profiles( [profile_1, profile_2] )
        self.assertEqual( len(store.read_profiles()), 2 )
        store.set_last_profile( profile_1 )
        self.assertTrue( store.get_last_profile().name, 'prôfile_1' )
        self.assertTrue( store.get_last_profile().dialect, 'sqlite' )
        self.assertTrue( store.get_last_profile().locale_language, 'en_US' )
        store.set_last_profile( profile_2 )
        self.assertTrue( store.get_last_profile().name, 'prôfile_2' )
        self.assertTrue( store.get_last_profile().dialect, 'mysql' )
        self.assertTrue( store.get_last_profile().locale_language, 'en_GB' )
        # os.remove(filename)

        return store

class ConfCase(unittest.TestCase):
    """Test the global configuration"""
    
    def test_import_settings(self):
        self.assertEqual( settings.get('FOO', None), None )
        self.assertRaises( AttributeError, lambda:settings.FOO )
        self.assertTrue( settings.CAMELOT_MEDIA_ROOT.endswith( 'media' ) )
        self.assertFalse( hasattr( settings, 'FOO' ) )
        
        class AdditionalSettings( object ):
            FOO = True
            
        settings.append( AdditionalSettings() )
        self.assertTrue( hasattr( settings, 'FOO' ) )
        try:
            settings.append_settings_module()
        except ImportError:
            pass
        
    def test_simple_settings(self):
        settings = SimpleSettings( 'Conceptive Engineering', 'Camelot Test')
        self.assertTrue( settings.ENGINE() )
        self.assertTrue( settings.CAMELOT_MEDIA_ROOT() )

class QtCase(unittest.TestCase):
    """Test the qt binding abstraction module
    """

    def test_variant(self):
        for obj in ['a', 5]:
            self.assertEqual(variant_to_py(py_to_variant(obj)), obj)

    def test_qsingleton(self):

        class NewQObject(QtCore.QObject, metaclass=QSingleton):
            pass

        obj1 = NewQObject()
        obj2 = NewQObject()

        self.assertTrue(obj1 is obj2)

class AbstractNamingContextCaseMixin(object):

    context_name = None
    context_cls = None

    # Name values that should throw an invalid_name NamingException with corresponding reason.
    invalid_names = [
        # value   reason
        (None,    NamingException.Message.invalid_name_type),
        ('',      NamingException.Message.invalid_atomic_name_length),
        (tuple(), NamingException.Message.multiary_name_expected),
        (('',),   NamingException.Message.invalid_atomic_name_length),
        ((None,), NamingException.Message.invalid_composite_name_parts)
    ]
    valid_names = ['test', ('test',), ('first', 'second')]

    def new_context(self):
        return self.context_cls()

    def test_qualified_name(self):
        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.get_qual_name('test')
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.get_qual_name(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # Verify the qualified name resolution of a context concatenates its name prefix with the provid name:
        # So the qualified result should just be the composite form of the provided name.
        for valid_name in self.valid_names:
            qual_name = (*self.context_name, *(valid_name if isinstance(valid_name, tuple) else [valid_name]))
            self.assertEqual(self.context.get_qual_name(valid_name), qual_name)

    def test_resolve(self):
        # Verify general exceptions raised when resolving a name-object binding.
        # Regular behaviour should be tested in other tests throughout this case after binding.

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.resolve('test')
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.resolve(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

    # Some naming contexts implementation may not implement the complete AbstractNamingContext interface,
    # so assert a NotImplementedError by default so corresponding test cases verify this.
    def test_resolve_context(self):
        with self.assertRaises(NotImplementedError):
            self.context.resolve_context('test')

    def test_bind(self):
        with self.assertRaises(NotImplementedError):
            self.context.bind('test', 1)

    def test_rebind(self):
        with self.assertRaises(NotImplementedError):
            self.context.rebind('test', 1)

    def test_bind_context(self):
        subcontext = self.new_context()
        with self.assertRaises(NotImplementedError):
            self.context.bind_context('subcontext', subcontext)

    def test_rebind_context(self):
        subcontext = self.new_context()
        with self.assertRaises(NotImplementedError):
            self.context.rebind_context('subcontext', subcontext)

    def test_unbind(self):
        with self.assertRaises(NotImplementedError):
            self.context.unbind('test')

    def test_unbind_context(self):
        with self.assertRaises(NotImplementedError):
            self.context.unbind_context('test')

class Object(object):
    pass

class NamingContextCaseMixin(AbstractNamingContextCaseMixin):

    def test_qualified_name(self):
        super().test_qualified_name()
        # Add a subcontext to the context and verify that its qualified name resolution includes
        # the name of its associated context:
        subcontext = self.context.bind_new_context('subcontext')
        self.assertEqual(subcontext.get_qual_name('test'), (*self.context_name, 'subcontext', 'test'))

    def test_list(self):
        initial_size_before_bind = len(list(initial_naming_context.list()))
        if not isinstance(self.context, InitialNamingContext):
            initial_naming_context.bind_context(self.context_name, self.context)
            obj =  Object()
            self.context.bind('obj1', obj)
            context_size = len(list(self.context.list()))
            self.assertEqual(context_size, 1)
            initial_size_after_bind = len(list(initial_naming_context.list()))
            self.assertEqual(initial_size_after_bind, initial_size_before_bind+context_size)
            # keep obj alive to be able to test the weak ref naming context
            del obj

    def test_bind(self):
        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.bind('test', 1)
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.bind(invalid_name, 2)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # Test the binding of an object to the context, which should return the fully qualified binding name,
        # and verify it can be looked back up on both the context (with the bound name),
        # and on the initial context (using the returned fully qualified name).
        name, obj = 'obj1', Object()
        qual_name = self.context.bind(name, obj)
        self.assertEqual(qual_name, (*self.context_name, name))
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertIn(tuple([name]), self.context)
        self.assertEqual(self.context.resolve(name), obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj)

        # Verify that trying to bind again under the same name throws the appropriate exception:
        with self.assertRaises(AlreadyBoundException):
            self.context.bind(name, Object())

        # Trying to bind an object using a composite name for which no subcontext binding could be found:
        name, obj = ('subcontext', 'obj2'), Object()
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.bind(name, obj)
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

        # Add a subcontext, and verify binding an object to it through the main context using the composite name:
        subcontext = self.context.bind_new_context('subcontext')
        qual_name = self.context.bind(name, obj)
        self.assertEqual(qual_name, (*self.context_name, *name))
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertIn('obj2', subcontext)
        self.assertEqual(self.context.resolve(name), obj)
        self.assertEqual(subcontext.resolve('obj2'), obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj)

        # Add immutable bindings and verify that the appropriate exception is thrown
        # when trying to mutate them:
        obj = Object()
        self.context.bind('immutable', obj, immutable=True)
        with self.assertRaises(ImmutableBindingException) as exc:
            self.context.rebind('immutable', obj)
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
        self.assertEqual(exc.exception.name, 'immutable')

    def test_rebind(self):
        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.rebind('test', 1)
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.rebind(invalid_name, 2)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # Test rebinding without an existing binding, which should behave like the regular bind():
        name, obj = 'obj1', Object()
        qual_name = self.context.rebind(name, obj)
        self.assertEqual(qual_name, (*self.context_name, name))
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertIn(tuple([name]), self.context)
        self.assertEqual(self.context.resolve(name), obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj)

        # Rebinding again under same name now should replace
        # the binding (in contrast to the AlreadyBoundException thrown with the regular bind).
        obj2 = Object()
        self.context.rebind(name, obj2)
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertEqual(self.context.resolve(name), obj2)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj2)

        # Trying to rebind an object using a composite name for which no subcontext binding could be found:
        name, obj = ('subcontext', 'obj2'), Object()
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.rebind(name, obj)
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

        # Add a subcontext, and verify rebinding an object initially to it through the main context using the composite name:
        subcontext = self.context.bind_new_context('subcontext')
        qual_name = self.context.bind(name, obj)
        self.assertEqual(qual_name, (*self.context_name, *name))
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertIn('obj2', subcontext)
        self.assertEqual(self.context.resolve(name), obj)
        self.assertEqual(subcontext.resolve('obj2'), obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj)

        # Composite rebinding under same name
        obj2 = Object()
        self.context.rebind(name, obj2)
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn(name, self.context)
        self.assertEqual(self.context.resolve(name), obj2)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj2)

        # Test binding a context as a regular object to another object.
        # Context need to be bound, so bind to the initial context, and add some binding:
        context_obj = initial_naming_context.bind_new_context('context2')
        name, obj = 'test', Object()
        context_obj.bind(name, obj)        
        # Then regularly bind the second context as an object to the subcontext created above:
        qual_name = subcontext.bind('context_obj', context_obj)
        self.assertEqual(qual_name, subcontext.get_qual_name('context_obj'))
        self.assertIn(qual_name, initial_naming_context)
        self.assertIn('context_obj', subcontext)
        self.assertEqual(subcontext.resolve('context_obj'), context_obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), context_obj)
        # It should not be able to be resolved as a context:
        with self.assertRaises(NameNotFoundException) as exc:
            subcontext.resolve_context('context_obj')
        self.assertEqual(exc.exception.name, 'context_obj')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        # Verify that the added context object does not participate in the recursive resolve
        # and should throw a not found exception:
        with self.assertRaises(NameNotFoundException) as exc:
            subcontext.resolve(('context_obj', 'test'))
        self.assertEqual(exc.exception.name, 'context_obj')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

    def test_bind_context(self):
        name, subcontext = 'subcontext', NamingContext()

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.bind_context('subcontext', subcontext)
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.bind_context(invalid_name, subcontext)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # The passed object should be asserted to be an instance of NamingContext:
        for invalid_context in [None, '', Object()]:
            with self.assertRaises(NamingException) as exc:
                self.context.bind_context(name, invalid_context)
            self.assertEqual(exc.exception.message, NamingException.Message.context_expected)

        # Test the binding of a subcontext to the context, which should return the fully qualified binding name,
        # and verify it can be looked back up on both the context (with the bound name),
        # and on the initial context (using the returned fully qualified name).
        qual_name = self.context.bind_context(name, subcontext)
        self.assertEqual(qual_name, (*self.context_name, name))
        # The qualified name should not be included in the context's contains definition as that only accounts for object bindings.
        self.assertNotIn(qual_name, initial_naming_context)
        self.assertNotIn(name, self.context)
        self.assertNotIn(tuple([name]), self.context)
        # It should however be possible to look the context back up again using the (qualified) name using resolve_context:
        self.assertEqual(self.context.resolve_context(name), subcontext)
        self.assertEqual(initial_naming_context.resolve_context(qual_name), subcontext)

        # Verify that trying to bind again under the same name throws the appropriate exception:
        with self.assertRaises(AlreadyBoundException):
            self.context.bind_context(name, NamingContext())

        # Trying to bind a subcontext using a composite name for which no subcontext binding could be found:
        name, subsubcontext = ('subcontext2', 'subsubcontext'), NamingContext()
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.bind_context(name, subsubcontext)
        self.assertEqual(exc.exception.name, 'subcontext2')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

        # Add the subcontext, and verify binding a subcontext to it through the main context using the composite name:
        subcontext = self.context.bind_new_context('subcontext2')
        qual_name = self.context.bind_context(name, subsubcontext)
        self.assertEqual(qual_name, (*self.context_name, *name))
        self.assertNotIn(qual_name, initial_naming_context)
        self.assertNotIn(name, self.context)
        self.assertNotIn('subsubcontext', subcontext)
        self.assertEqual(self.context.resolve_context(name), subsubcontext)
        self.assertEqual(subcontext.resolve_context('subsubcontext'), subsubcontext)
        self.assertEqual(initial_naming_context.resolve_context(qual_name), subsubcontext)

        # Add immutable binding and verify that the appropriate exception is thrown
        # when trying to rebind it:
        immutable_context = self.context.bind_new_context('immutable', immutable=True)
        with self.assertRaises(ImmutableBindingException) as exc:
            self.context.rebind_context('immutable', immutable_context)
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        self.assertEqual(exc.exception.name, 'immutable')

    def test_rebind_context(self):
        name, subcontext = 'subcontext', NamingContext()

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.rebind_context('subcontext', subcontext)
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.rebind_context(invalid_name, subcontext)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # The passed object should be asserted to be an instance of NamingContext:
        for invalid_context in [None, '', Object()]:
            with self.assertRaises(NamingException) as exc:
                self.context.rebind_context(name, invalid_context)
            self.assertEqual(exc.exception.message, NamingException.Message.context_expected)

        # Test the rebinding of a subcontext to the context, with no existing context binding, which should behave as a regular bind_context()
        qual_name = self.context.rebind_context(name, subcontext)
        self.assertEqual(qual_name, (*self.context_name, name))
        # The qualified name should not be included in the context's contains definition as that only accounts for object bindings.
        self.assertNotIn(qual_name, initial_naming_context)
        self.assertNotIn(name, self.context)
        self.assertNotIn(tuple([name]), self.context)
        # It should however be possible to look the context back up again using the (qualified) name using resolve_context:
        self.assertEqual(self.context.resolve_context(name), subcontext)
        self.assertEqual(initial_naming_context.resolve_context(qual_name), subcontext)

        # Rebinding a context again under same name now should replace
        # the binding (in contrast to the AlreadyBoundException thrown with the regular bind_context).        
        subcontext2 = NamingContext()
        self.context.rebind_context(name, subcontext2)
        self.assertNotIn(qual_name, initial_naming_context)
        self.assertNotIn(name, self.context)
        self.assertNotIn(tuple([name]), self.context)
        self.assertEqual(self.context.resolve_context(name), subcontext2)
        self.assertEqual(initial_naming_context.resolve_context(qual_name), subcontext2)

        # Trying to rebind a subcontext using a composite name for which no subcontext binding could be found:
        name, subsubcontext = ('subcontext2', 'subsubcontext'), NamingContext()
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.rebind_context(name, subsubcontext)
        self.assertEqual(exc.exception.name, 'subcontext2')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

        # Add the subcontext, and verify rebinding a subcontext to it through the main context using the composite name:
        subcontext = self.context.bind_new_context('subcontext2')
        qual_name = self.context.rebind_context(name, subsubcontext)
        self.assertEqual(qual_name, (*self.context_name, *name))
        self.assertNotIn(qual_name, initial_naming_context)
        self.assertNotIn(name, self.context)
        self.assertNotIn('subsubcontext', subcontext)
        self.assertEqual(self.context.resolve_context(name), subsubcontext)
        self.assertEqual(subcontext.resolve_context('subsubcontext'), subsubcontext)
        self.assertEqual(initial_naming_context.resolve_context(qual_name), subsubcontext)

    def test_unbind(self):
        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.unbind('test')
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        self.context.bind_new_context('subcontext')
        name1, obj1 = 'obj1', Object()
        name2, obj2 = ('subcontext', 'obj2'), Object()

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.unbind(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # Unbinding should fail when no existing binding was found:
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.unbind(name1)
        self.assertEqual(exc.exception.name, name1)
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.unbind(name2)
        self.assertEqual(exc.exception.name, name2[-1])
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        # Add binding to be able to verify unbinding it:
        qual_name_1 = self.context.bind(name1, obj1)
        self.assertIn(name1, self.context)
        self.assertIn(qual_name_1, initial_naming_context)
        self.assertEqual(self.context.resolve(name1), obj1)
        self.assertEqual(initial_naming_context.resolve(qual_name_1), obj1)
        # Unbind it and verify the object is not present in context and the initial context anymore,
        # and that resolving it fails:
        self.context.unbind(name1)
        self.assertNotIn(name1, self.context)
        self.assertNotIn(qual_name_1, initial_naming_context)
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.resolve(name1)
        self.assertEqual(exc.exception.name, name1)
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
        with self.assertRaises(NameNotFoundException) as exc:
            initial_naming_context.resolve(qual_name_1)
        self.assertEqual(exc.exception.name, name1)
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        # Add binding to subcontext and verify unbinding it one the main context using the composite name:
        qual_name_2 = self.context.bind(name2, obj2)   
        self.assertIn(name2, self.context)
        self.assertIn(qual_name_2, initial_naming_context)
        self.assertEqual(self.context.resolve(name2), obj2)
        self.assertEqual(initial_naming_context.resolve(qual_name_2), obj2)
        # Unbind it and verify the object is not present in context and the initial context anymore,
        # and that resolving it fails:
        self.context.unbind(name2)
        self.assertNotIn(name2, self.context)
        self.assertNotIn(qual_name_2, initial_naming_context)
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.resolve(name2)
        self.assertEqual(exc.exception.name, name2[-1])
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
        with self.assertRaises(NameNotFoundException) as exc:
            initial_naming_context.resolve(qual_name_2)
        self.assertEqual(exc.exception.name, name2[-1])
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        # Add immutable bindings and verify that the appropriate exception is thrown
        # when trying to unbind it:
        obj = Object()
        self.context.bind('immutable', obj, immutable=True)
        with self.assertRaises(ImmutableBindingException) as exc:
            self.context.unbind('immutable')
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
        self.assertEqual(exc.exception.name, 'immutable')

    def test_unbind_context(self):
        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.unbind_context(None)
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.unbind_context(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

        # Unbinding should fail when no existing binding was found:
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.unbind_context('subcontext')
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)

        # Bind new context to be able to verify unbinding it:
        subcontext = self.context.bind_new_context('subcontext')
        name, obj = 'obj', Object()
        qual_name = subcontext.bind(name, obj)
        self.assertIn(name, subcontext)
        self.assertIn(('subcontext', name), self.context)
        self.assertIn(qual_name, initial_naming_context)
        self.assertEqual(self.context.resolve(('subcontext', name)), obj)
        self.assertEqual(initial_naming_context.resolve(qual_name), obj)
        # Unbind the subcontext it and verify the object is not present in the main context and the initial context anymore,
        # and that resolving it and its bounded objects fails:
        self.context.unbind_context('subcontext')
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.resolve_context('subcontext')
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        self.assertNotIn(('subcontext', name), self.context)
        self.assertNotIn(qual_name, initial_naming_context)
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.resolve(('subcontext', name))
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        with self.assertRaises(NameNotFoundException) as exc:
            initial_naming_context.resolve(qual_name)
        self.assertEqual(exc.exception.name, 'subcontext')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        # The unbound context should now also throw unbound exceptions:
        with self.assertRaises(UnboundException):
            subcontext.bind('test', Object())

        # Add immutable binding and verify that the appropriate exception is thrown
        # when trying to rebind it:
        self.context.bind_new_context('immutable', immutable=True)
        with self.assertRaises(ImmutableBindingException) as exc:
            self.context.unbind_context('immutable')
        self.assertEqual(exc.exception.binding_type, BindingType.named_context)
        self.assertEqual(exc.exception.name, 'immutable')

    def test_resolve_context(self):
        # Verify general exceptions raised for name-context resolving.
        # Regular behaviour is tested in this case throughout after binding values.

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(self.context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                self.context.resolve_context('test')
            # Bind the context to the initial context
            initial_naming_context.bind_context(self.context_name, self.context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name, reason in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                self.context.resolve_context(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name, invalid_name)
            self.assertEqual(exc.exception.reason, reason, invalid_name)

class AbstractNamingContextCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        # Store a copy of initial context's bindings before each test,
        # so that they can be reinstated in the tear down afterwards.
        self.initial_context_bindings = InitialNamingContext()._bindings
        InitialNamingContext()._bindings = {btype: bstorage.copy() for btype, bstorage in InitialNamingContext()._bindings.items()}
        self.context = self.new_context()

    def tearDown(self):
        super().tearDown()
        # Reinstate initial context's bindings.
        InitialNamingContext()._bindings = self.initial_context_bindings

class NamingContextCase(AbstractNamingContextCase, NamingContextCaseMixin):

    context_name = ('context',)
    context_cls = NamingContext

class ConstantNamingContextCaseMixin(AbstractNamingContextCaseMixin):

    context_cls = ConstantNamingContext
    constant_type = None

    # Constant naming context only allows singular names, and allows the empty string:
    invalid_names = [
        (None,             NamingException.Message.invalid_name_type),
        (tuple(),          NamingException.Message.multiary_name_expected),
        ((1,),             NamingException.Message.invalid_composite_name_parts),
        ((None,),          NamingException.Message.invalid_composite_name_parts),
        (('test', ''),     NamingException.Message.singular_name_expected),
        (('test', None),   NamingException.Message.invalid_composite_name_parts),
        (('test', 'test'), NamingException.Message.singular_name_expected),
    ]
    valid_names = ['', 'x', '-1', '0', '1', 'True', '1.5', 'test']

    # Names may be valid arguments, but still fail the resolve (e.g. the conversion to the constant type).
    # So define the compatible and incompatible set to verify in concrete cases.
    incompatible_names = None
    compatible_names = None

    def new_context(self):
        return self.context_cls(self.constant_type)

    def test_resolve(self):
        super().test_resolve()
        # Verify that incompatible names raise a NameNotFoundException:
        for incompatible_name in self.incompatible_names:
            with self.assertRaises(NameNotFoundException) as exc:
                self.context.resolve(incompatible_name)
            self.assertEqual(exc.exception.name, self.context.get_composite_name(incompatible_name))
            self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        # Verify compatible names resolve to the expected objects:
        # Both string names as singular composite names should be allowed:
        for name, expected in self.compatible_names:
            self.assertEqual(self.context.resolve(name), expected)
            if not isinstance(name, tuple):
                self.assertEqual(self.context.resolve(tuple([name])), expected)

class StringNamingContextCase(AbstractNamingContextCase, ConstantNamingContextCaseMixin):

    context_name = ('str',)
    constant_type = Constant.string

    incompatible_names = []
    compatible_names = [(name, name) for name in ConstantNamingContextCaseMixin.valid_names]

class IntegerNamingContextCase(AbstractNamingContextCase, ConstantNamingContextCaseMixin):

    context_name = ('int',)
    constant_type = Constant.integer

    incompatible_names = ['', 'x', 'True', '1.5', 'test']
    compatible_names = [('-1', -1), ('0', 0), ('2', 2)]

class DecimalNamingContextCase(AbstractNamingContextCase, ConstantNamingContextCaseMixin):

    context_name = ('decimal',)
    constant_type = Constant.decimal

    incompatible_names = ['', 'x', 'True', 'test']
    compatible_names = [('-1', Decimal(-1)), ('0', Decimal(0)), ('2', Decimal(2)), ('1.5', Decimal(1.5))]

class DatetimeNamingContextCase(AbstractNamingContextCase, ConstantNamingContextCaseMixin):

    context_name = ('datetime',)
    constant_type = Constant.time

    invalid_names = [
        (None,             NamingException.Message.invalid_name_type),
        (tuple(),          NamingException.Message.multiary_name_expected),
        ((1,),             NamingException.Message.invalid_composite_name_parts),
        ((None,),          NamingException.Message.invalid_composite_name_parts),
        (('test', ''),     NamingException.Message.invalid_composite_name_length),
        (('test', None),   NamingException.Message.invalid_composite_name_parts),
        (('test', 'test'), NamingException.Message.invalid_composite_name_length),
        ('',               NamingException.Message.invalid_atomic_name_numeric),
        ('x',              NamingException.Message.invalid_atomic_name_numeric),
        (('2021',),        NamingException.Message.invalid_composite_name_length),
        (('2021', '5'),    NamingException.Message.invalid_composite_name_length),
    ]
    valid_names = [('2021','2','7','12','12','1'), ('2022','4','13','13','51','46'), ('2021','02','7','12','12','1'), ('2021', '13', '33', '12', '00', '10')]
    incompatible_names = [('2021', '13', '33', '12', '00', '10')]
    compatible_names = [
        (('2021','2','7','12','12','1'), datetime.datetime(2021, 2, 7, 12, 12, 1)),
        (('2021','02','7','12','12','1'), datetime.datetime(2021, 2, 7, 12, 12, 1)),
        (('2022','4','13','13','51','46'), datetime.datetime(2022, 4, 13, 13, 51, 46)),
    ]

class DateNamingContextCase(AbstractNamingContextCase, ConstantNamingContextCaseMixin):

    context_name = ('date',)
    constant_type = Constant.date

    invalid_names = [
        (None,             NamingException.Message.invalid_name_type),
        (tuple(),          NamingException.Message.multiary_name_expected),
        ((1,),             NamingException.Message.invalid_composite_name_parts),
        ((None,),          NamingException.Message.invalid_composite_name_parts),
        (('test', ''),     NamingException.Message.invalid_composite_name_length),
        (('test', None),   NamingException.Message.invalid_composite_name_parts),
        (('test', 'test'), NamingException.Message.invalid_composite_name_length),
        ('',               NamingException.Message.invalid_atomic_name_numeric),
        ('x',              NamingException.Message.invalid_atomic_name_numeric),
        (('2021',),        NamingException.Message.invalid_composite_name_length),
        (('2021', '5'),    NamingException.Message.invalid_composite_name_length),
    ]
    valid_names = [('2021','2','7'), ('2022','4','13'), ('2021', '13', '33')]
    incompatible_names = [('2021', '13', '33')]
    compatible_names = [
        (('2021','2','7'), datetime.date(2021, 2, 7)),
        (('2022','4','13'), datetime.date(2022, 4, 13)),
    ]

class InitialNamingContextCase(NamingContextCase, ExampleModelMixinCase):

    context_name = tuple()
    context_cls = InitialNamingContext

    @classmethod
    def setUpClass(cls):
        super(InitialNamingContextCase, cls).setUpClass()
        cls.setup_sample_model()
        LoadSampleData().model_run(None, None)
        cls.session = Session()

        class CompositePkEntity(Entity):

            id_1 = schema.Column(types.Integer, primary_key=True)
            id_2 = schema.Column(types.Integer, primary_key=True)

        metadata.create_all()
        cls.binary_entity_1 = CompositePkEntity(id_1=1, id_2=1)
        cls.binary_entity_2 = CompositePkEntity(id_1=1, id_2=2)
        cls.session.flush()

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_sample_model()

    def test_singleton(self):
        # Verify the InitialNamingContext is a singleton.
        self.assertEqual(initial_naming_context, InitialNamingContext())
        self.assertEqual(InitialNamingContext(), InitialNamingContext())
        initial_naming_context.bind('test', object())
        self.assertEqual(initial_naming_context._bindings, InitialNamingContext()._bindings)

    def test_resolve(self):
        super().test_resolve()
        entity1 = party.Organization(name='1')
        entity2 = party.Person(first_name='Test', last_name='Dummy')
        self.session.flush()

        # Verify that the constant naming contexts are available by default on the initial context:
        # * Boolean values
        self.assertEqual(self.context.resolve(('constant', 'true')), True)
        self.assertEqual(self.context.resolve(('constant', 'false')), False)
        # * None value
        self.assertEqual(self.context.resolve(('constant', 'null')), None)
        # * Int values
        self.assertEqual(self.context.resolve(('constant', 'int', '-1')), -1)
        self.assertEqual(self.context.resolve(('constant', 'int', '0')), 0)
        self.assertEqual(self.context.resolve(('constant', 'int', '2')), 2)
        # * String values
        self.assertEqual(self.context.resolve(('constant', 'str', '')), '')
        self.assertEqual(self.context.resolve(('constant', 'str', 'x')), 'x')
        self.assertEqual(self.context.resolve(('constant', 'str', 'test')), 'test')
        # * Decimal values
        self.assertEqual(self.context.resolve(('constant', 'decimal', '-2')), Decimal(-2))
        self.assertEqual(self.context.resolve(('constant', 'decimal', '-1.0')), Decimal(-1.0))
        self.assertEqual(self.context.resolve(('constant', 'decimal', '0')), Decimal(0))
        self.assertEqual(self.context.resolve(('constant', 'decimal', '0.0')), Decimal(0.0))
        self.assertEqual(self.context.resolve(('constant', 'decimal', '2')), Decimal(2))
        # Datetimes
        self.assertEqual(self.context.resolve(('constant', 'datetime', '2022', '04', '13', '13', '51', '46')), datetime.datetime(2022, 4, 13, 13, 51, 46))
        self.assertEqual(self.context.resolve(('constant', 'datetime', '2021', '02', '05', '22', '00', '01')), datetime.datetime(2021, 2, 5, 22, 0, 1))
        # Dates
        self.assertEqual(self.context.resolve(('constant', 'date', '2022', '04', '13')), datetime.date(2022, 4, 13))
        self.assertEqual(self.context.resolve(('constant', 'date', '2021', '02', '05')), datetime.date(2021, 2, 5))
        # Entities
        self.assertEqual(self.context.resolve(('entity', 'organization', session_id, str(entity1.id))), entity1)
        self.assertEqual(self.context.resolve(('entity', 'person', session_id, str(entity2.id))), entity2)
        self.assertEqual(self.context.resolve(('entity', 'composite_pk_entity', session_id, str(self.binary_entity_1.id_1), str(self.binary_entity_1.id_2))), self.binary_entity_1)
        self.assertEqual(self.context.resolve(('entity', 'composite_pk_entity', session_id, str(self.binary_entity_2.id_1), str(self.binary_entity_2.id_2))), self.binary_entity_2)

        # Verify that subcontexts and/or values are immutabe on the initial naming context:
        for subcontext in ['constant', 'entity', 'object']:
            with self.assertRaises(ImmutableBindingException):
                self.context.rebind_context(subcontext, NamingContext())
            with self.assertRaises(ImmutableBindingException):
                self.context.unbind_context(subcontext)

        constants = self.context.resolve_context('constant')
        with self.assertRaises(ImmutableBindingException):
            constants.rebind_context('str', NamingContext())
        with self.assertRaises(ImmutableBindingException):
            constants.unbind_context('str')

    def test_bind_object(self):
        obj1 = object()
        obj2 = object()
        entity1 = party.Organization(name='1')
        entity2 = party.Person(first_name='Test', last_name='Dummy')
        self.session.flush()

        for obj, expected_name in [
            (None,            ('constant', 'null')),
            (True,            ('constant', 'true')),
            (False,           ('constant', 'false')),
            ('test',          ('constant', 'str', 'test')),
            ('',              ('constant', 'str', '')),
            (1,               ('constant', 'int', '1')),
            (0,               ('constant', 'int', '0')),
            (-1,              ('constant', 'int', '-1')),
            (Decimal('-2.1'), ('constant', 'decimal', '-2.1')),
            (Decimal('0.0'),  ('constant', 'decimal', '0')), # Should remove trailing zeros.
            (Decimal('3.5'),  ('constant', 'decimal', '3.5')),
            (Decimal('4.7500'),('constant', 'decimal', '4.75')),
            (obj1,            ('object', str(id(obj1)))),
            (obj2,            ('object', str(id(obj2)),)),
            (entity1,         ('entity', 'organization', session_id, str(entity1.id))),
            (entity2,         ('entity', 'person', session_id, str(entity2.id))),
            (self.binary_entity_1, ('entity', 'composite_pk_entity', session_id, str(self.binary_entity_1.id_1), str(self.binary_entity_1.id_2))),
            (self.binary_entity_2, ('entity', 'composite_pk_entity', session_id, str(self.binary_entity_2.id_1), str(self.binary_entity_2.id_2))),
            (datetime.datetime(2022, 4, 13, 13, 51, 46), ('constant', 'datetime', '2022', '4', '13', '13', '51', '46')),
            (datetime.date(2022, 4, 13),                 ('constant', 'date', '2022', '4', '13')),
            ]:
            name = self.context._bind_object(obj)
            self.assertEqual(name, expected_name)
            self.assertIn(name, self.context)
            self.assertEqual(obj, self.context.resolve(name))

        # Floats should not be implemented:
        with self.assertRaises(NotImplementedError):
            self.context._bind_object(3.5)

        # Only flushed entities should be supported:
        with self.assertRaises(NotImplementedError):
            self.context._bind_object(party.Person(first_name='Crash test', last_name='Dummy'))
        self.session.delete(entity1)
        self.session.flush()
        with self.assertRaises(NotImplementedError):
            self.context._bind_object(entity1)
        # Only entities bound to a session should be supported:
        self.session.expunge(entity2)
        with self.assertRaises(NotImplementedError):
            self.context._bind_object(entity2)

class EntityNamingContextCaseMixin(AbstractNamingContextCaseMixin):

    context_cls = EntityNamingContext
    entity = None

    # Entity naming context only allows singular names, and numeric atomic names.
    invalid_names = [
        (None,                          NamingException.Message.invalid_name_type),
        ('',                            NamingException.Message.invalid_atomic_name_numeric),
        (tuple(),                       NamingException.Message.multiary_name_expected),
        ((session_id, '',),             NamingException.Message.invalid_atomic_name_numeric),
        ((session_id, None,),           NamingException.Message.invalid_composite_name_parts),
        ((session_id, 1,),              NamingException.Message.invalid_composite_name_parts),
        ((session_id, None,),           NamingException.Message.invalid_composite_name_parts),
        ((session_id, 'test', ''),      NamingException.Message.invalid_composite_name_length),
        ((session_id, 'test', None),    NamingException.Message.invalid_composite_name_parts),
        ((session_id, 'test', 'test'),  NamingException.Message.invalid_composite_name_length),
    ]
    valid_names = [
        (session_id, '0'),
        (session_id, '1'),
        (session_id, '2'),
        (session_id, '9999'),
        # With unexisting session id:
        ('9999', '0'),
        ('9999', '1'),
        ('9999', '2'),
        ('9999', '9999'),
    ]
    incompatible_names = [
        (session_id, '0'),
        (session_id, '9999'),
        # With unexisting session id:
        ('9999', '0'),
        ('9999', '1'),
        ('9999', '2'),
        ('9999', '9999'),
    ]
    compatible_names = [
        (session_id, '1'),
        (session_id, '2'),
    ]

    def new_context(self):
        return self.context_cls(self.entity)

    def test_resolve(self):
        super().test_resolve()

        # Verify that incompatible names raise a NameNotFoundException:
        for incompatible_name in self.incompatible_names:
            with self.assertRaises(NameNotFoundException) as exc:
                self.context.resolve(incompatible_name)
            self.assertEqual(exc.exception.name, incompatible_name[0] if isinstance(incompatible_name, tuple) else incompatible_name)
            self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        # Verify compatible names resolve to the expected entity instances:
        # Both string names as singular composite names should be allowed:
        for name in self.compatible_names:
            expected_instance = self.session.query(self.entity).get(name[1:])
            self.assertIsNotNone(expected_instance)
            self.assertEqual(self.context.resolve(name), expected_instance)
            if not isinstance(name, tuple):
                self.assertEqual(self.context.resolve(tuple([name])), expected_instance)

class AbstractEntityNamingContextCase(AbstractNamingContextCase, ExampleModelMixinCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_sample_model()
        list(LoadSampleData().model_run(None, None))
        cls.session = Session()

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_sample_model()

class PersonEntityNamingContextCase(AbstractEntityNamingContextCase, EntityNamingContextCaseMixin):

    entity = party.Person
    context_name = ('person',)

class OrganizationEntityNamingContextCase(AbstractEntityNamingContextCase, EntityNamingContextCaseMixin):

    entity = party.Organization
    context_name = ('organization',)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Make sure at least 2 organization exist.
        org1 = party.Organization( name = 'Test1' )
        org2 = party.Organization( name = 'Test2' )
        cls.session.flush()
        cls.compatible_names = [
            (session_id, str(org1.id)),
            (session_id, str(org2.id)),
        ]

class AbstractCompositePKEntityNamingContextCase(AbstractEntityNamingContextCase):

    invalid_names = [
        (None,                             NamingException.Message.invalid_name_type),
        ('',                               NamingException.Message.invalid_atomic_name_numeric),
        (tuple(),                          NamingException.Message.multiary_name_expected),
        ((None,),                          NamingException.Message.invalid_composite_name_parts),
        ((1,),                             NamingException.Message.invalid_composite_name_parts),
        ((None,),                          NamingException.Message.invalid_composite_name_parts),
        (('test', None),                   NamingException.Message.invalid_composite_name_parts),
        (('',),                            NamingException.Message.invalid_composite_name_length),
        ((session_id, '1', '1', '1', '1'), NamingException.Message.invalid_composite_name_length),
    ]

    @classmethod
    def setUpClass(cls):
        AbstractEntityNamingContextCase.setUpClass()

        cls.metadata = MetaData()
        cls.class_registry = dict()
        cls.Entity = declarative_base( cls = EntityBase,
                                        metadata = cls.metadata,
                                        metaclass = EntityMetaMock,
                                        class_registry = cls.class_registry,
                                        constructor = None,
                                        name = 'Entity' )
        cls.metadata.bind = 'sqlite://'
        cls.session = Session()

    @classmethod
    def tearDownCls(cls):
        AbstractEntityNamingContextCase.tearDownClass()
        cls.metadata.drop_all()
        cls.metadata.clear()

class BinaryPKEntityNamingContextCase(AbstractCompositePKEntityNamingContextCase, EntityNamingContextCaseMixin):

    context_name = ('entity2',)
    invalid_names = AbstractCompositePKEntityNamingContextCase.invalid_names + [
        ('0',                          NamingException.Message.invalid_composite_name_length),
        ('1',                          NamingException.Message.invalid_composite_name_length),
        ('2',                          NamingException.Message.invalid_composite_name_length),
        ('9999',                       NamingException.Message.invalid_composite_name_length),
        (('test', session_id, ''),     NamingException.Message.invalid_atomic_name_numeric),
        (('test', session_id, 'test'), NamingException.Message.invalid_atomic_name_numeric),
    ]
    valid_names = [
        (session_id, '0', '0'),
        (session_id, '1', '1'),
        (session_id, '1', '2'),
        (session_id, '2', '2'),
        (session_id, '9999', '9999'),
    ]
    incompatible_names = [
        (session_id, '0', '0'),
        (session_id, '2', '2'),
        (session_id, '9999', '9999'),
    ]
    compatible_names = [
        (session_id, '1', '1'),
        (session_id, '1', '2'),
    ]

    @classmethod
    def setUpClass(cls):
        AbstractCompositePKEntityNamingContextCase.setUpClass()

        class PK2Entity(cls.Entity):

            id_1 = schema.Column(types.Integer, primary_key=True)
            id_2 = schema.Column(types.Integer, primary_key=True)

        cls.metadata.create_all()
        cls.entity = PK2Entity
        a1 = PK2Entity(id_1=1, id_2=1)
        a2 = PK2Entity(id_1=1, id_2=2)
        cls.session.flush()
        cls.compatible_names = [
            (session_id, str(a1.id_1), str(a1.id_2)),
            (session_id, str(a2.id_1), str(a2.id_2)),
        ]

class TernaryPKEntityNamingContextCase(AbstractCompositePKEntityNamingContextCase, EntityNamingContextCaseMixin):

    context_name = ('entity3',)
    invalid_names = AbstractCompositePKEntityNamingContextCase.invalid_names + [
        ('0',              NamingException.Message.invalid_composite_name_length),
        ('1',              NamingException.Message.invalid_composite_name_length),
        ('2',              NamingException.Message.invalid_composite_name_length),
        ('9999',           NamingException.Message.invalid_composite_name_length),
        (('0', '0'),       NamingException.Message.invalid_composite_name_length),
        (('1', '1'),       NamingException.Message.invalid_composite_name_length),
        (('1', '2'),       NamingException.Message.invalid_composite_name_length),
        (('2', '2'),       NamingException.Message.invalid_composite_name_length),
        (('9999', '9999'), NamingException.Message.invalid_composite_name_length),
        (('test', ''),     NamingException.Message.invalid_composite_name_length),
        (('test', 'test'), NamingException.Message.invalid_composite_name_length),
    ]
    valid_names = [
        (session_id, '0', '0', '0'),
        (session_id, '1', '1', '1'),
        (session_id, '1', '2', '3'),
        (session_id, '2', '2', '2'),
        (session_id, '9999', '9999', '9999'),
    ]
    incompatible_names = [
        (session_id, '0', '0', '0'),
        (session_id, '2', '2', '2'),
        (session_id, '9999', '9999', '9999'),
    ]
    compatible_names = [
        (session_id, '1', '1', '1'),
        (session_id, '1', '2', '3'),
    ]

    @classmethod
    def setUpClass(cls):
        AbstractCompositePKEntityNamingContextCase.setUpClass()

        class PK3Entity(cls.Entity):

            id_1 = schema.Column(types.Integer, primary_key=True)
            id_2 = schema.Column(types.Integer, primary_key=True)
            id_3 = schema.Column(types.Integer, primary_key=True)

        cls.metadata.create_all()
        cls.entity = PK3Entity
        a1 = PK3Entity(id_1=1, id_2=1, id_3=1)
        a2 = PK3Entity(id_1=1, id_2=2, id_3=3)
        cls.session.flush()
        cls.compatible_names = [
            (session_id, str(a1.id_1), str(a1.id_2), str(a1.id_3)),
            (session_id, str(a2.id_1), str(a2.id_2), str(a2.id_3)),
        ]

class WeakRefNamingContextCase(AbstractNamingContextCase, NamingContextCaseMixin):

    context_name = ('weakref',)
    context_cls = WeakRefNamingContext

    def test_bind(self):
        # Verify that objects bound to a WeakRefNamingContext are removed once they are not hard referenced anymore,
        # regardless of their mutability:
        super().test_bind()

        # * binding an unreferenced object:
        for immutable in [True, False]:
            self.context.bind('test', Object(), immutable)
            with self.assertRaises(NameNotFoundException) as exc:
                self.context.resolve('test')
            self.assertEqual(exc.exception.name, 'test')
            self.assertEqual(exc.exception.binding_type, BindingType.named_object)

        obj = Object()
        self.context.bind('test', obj, immutable)
        self.assertEqual(obj, self.context.resolve('test'))
        # * removing the last hard reference post-binding:
        del obj
        with self.assertRaises(NameNotFoundException) as exc:
            self.context.resolve('test')
        self.assertEqual(exc.exception.name, 'test')
        self.assertEqual(exc.exception.binding_type, BindingType.named_object)
