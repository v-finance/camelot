# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from .test_model import ExampleModelMixinCase
from camelot.core.conf import SimpleSettings, settings
from camelot.core.memento import SqlMemento, memento_change, memento_types
from camelot.core.naming import (
    AlreadyBoundException, BindingType, InitialNamingContext, NameNotFoundException,
    NamingContext, NamingException, UnboundException
)
from camelot.core.profile import Profile, ProfileStore
from camelot.core.qt import QtCore, py_to_variant, variant_to_py

memento_id_counter = 0

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
        profile_1 = Profile(u'prôfile_1')
        profile_1.dialect = u'sqlite'
        profile_2 = Profile(u'prôfile_2')
        profile_2.dialect = u'mysql'
        store.write_profiles( [profile_1, profile_2] )
        self.assertEqual( len(store.read_profiles()), 2 )
        store.set_last_profile( profile_1 )
        self.assertTrue( store.get_last_profile().name, u'prôfile_1' )
        self.assertTrue( store.get_last_profile().dialect, u'sqlite' )
        store.set_last_profile( profile_2 )
        self.assertTrue( store.get_last_profile().name, u'prôfile_2' )
        self.assertTrue( store.get_last_profile().dialect, u'mysql' )
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

class NamingContextCaseMixin(object):

    context_name = None
    context_cls = None
    initial_context = InitialNamingContext()

    # Name values that should throw an invalid_name NamingException.
    invalid_names = [None, '', tuple(), ('',), (None,), ('test', ''), ('test', None)]

    def test_qualified_name(self):
        context = self.context_cls()

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                context.get_qual_name('test')
            # Bind the context to the initial context
            self.initial_context.bind_context(self.context_name, context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                context.get_qual_name(invalid_name)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name)

        # Verify the qualified name resolution of a context concatenates its name prefix with the provid name:
        # So the qualified result should just be the composite form of the provided name.
        self.assertEqual(context.get_qual_name('test'),              (*self.context_name, 'test'))
        self.assertEqual(context.get_qual_name(('test',)),           (*self.context_name, 'test'))
        self.assertEqual(context.get_qual_name(('first', 'second')), (*self.context_name, 'first', 'second'))

        # Add a subcontext to the context and verify that its qualified name resolution includes
        # the name of its associated context:
        subcontext = context.bind_new_context('subcontext')
        self.assertEqual(subcontext.get_qual_name('test'), (*self.context_name, 'subcontext', 'test'))

    def test_bind(self):
        context = self.context_cls()

        # In case of a regular NamingContext, assert that the action throws the appropriate UnboundException,
        # and bind the context to the initial context.
        # Actions on the InitialNamingContext, which is bounded by default, should work out of the box.
        if not isinstance(context, InitialNamingContext):
            with self.assertRaises(UnboundException):
                context.bind('test', 1)
            # Bind the context to the initial context
            self.initial_context.bind_context(self.context_name, context)

        # Verify invalid names throw the appropriate exception:
        for invalid_name in self.invalid_names:
            with self.assertRaises(NamingException) as exc:
                context.bind(invalid_name, 2)
            self.assertEqual(exc.exception.message, NamingException.Message.invalid_name)

        # Test the binding of objects to the context, which should return the fully qualified binding name,
        # and verify the object can be looked back up on both the context (with the bound name),
        # and on the initial context (using the returned fully qualified name).
        # that should be able to be used to resolve the object from the initial naming context.
        obj1 = 1, obj2 = object()
        self.assertEqual(self.context.bind('1', obj1), (*self.context_name, '1'))
        self.assertEqual(self.context.resolve('1'), obj1)
        self.assertEqual(self.initial_context.resolve(*self.context_name, '1'), obj1)

class InitialNamingContextCase(unittest.TestCase, NamingContextCaseMixin):

    context_name = tuple()
    context_cls = InitialNamingContext

    def test_singleton(self):
        # Verify the InitialNamingContext is a singleton.
        self.assertEqual(self.initial_context, InitialNamingContext())
        self.assertEqual(InitialNamingContext(), InitialNamingContext())

class NamingContextCase(unittest.TestCase, NamingContextCaseMixin):

    context_name = ('context',)
    context_cls = NamingContext

    def tearDown(self):
        super().tearDown()
        # Remove all initial context's bindings after each test.
        self.initial_context._bindings[BindingType.named_context] = dict()
        self.initial_context._bindings[BindingType.named_object] = dict()
