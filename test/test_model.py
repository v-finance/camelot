import datetime
import os

from sqlalchemy import orm
from sqlalchemy import schema, types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Session
from camelot.test import ModelThreadTestCase
from camelot.test.action import MockModelContext
from .test_orm import TestMetaData

class ModelCase( ModelThreadTestCase ):
    """Test the build in camelot model"""
  
    def setUp(self):
        super( ModelCase, self ).setUp()
        from camelot.model.party import Person
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( Person )
        
    def test_i18n( self ):
        from camelot.model.i18n import Translation
        session = Session()
        session.execute( Translation.__table__.delete() )
        self.assertEqual( Translation.translate( 'bucket', 'nl_BE' ), None )
        Translation.translate_or_register( 'bucket', 'nl_BE' )
        self.assertEqual( Translation.translate( 'bucket', 'nl_BE' ), 'bucket' )
        
    def test_batch_job( self ):
        from camelot.model.batch_job import BatchJob, BatchJobType
        batch_job_type = BatchJobType.get_or_create( u'Synchronize' )
        batch_job = BatchJob.create( batch_job_type )
        self.assertTrue( unicode( batch_job_type ) )
        self.assertFalse( batch_job.is_canceled() )
        batch_job.change_status( 'canceled' )
        self.assertTrue( batch_job.is_canceled() )
        # run batch job without exception
        with batch_job:
            batch_job.add_strings_to_message( [ u'Doing something' ] )
            batch_job.add_strings_to_message( [ u'Done' ], color = 'green' )
        self.assertEqual( batch_job.current_status, 'success' )
        # run batch job with exception
        batch_job = BatchJob.create( batch_job_type )
        with batch_job:
            batch_job.add_strings_to_message( [ u'Doing something' ] )
            raise Exception('Something went wrong')
        self.assertEqual( batch_job.current_status, 'errors' )
    
    def test_current_authentication( self ):
        from camelot.model.authentication import get_current_authentication
        authentication = get_current_authentication()
        # current authentication cache should survive 
        # a session expire + expunge
        orm.object_session( authentication ).expire_all()
        orm.object_session( authentication ).expunge_all()
        authentication = get_current_authentication()
        self.assertTrue( authentication.username )
        self.assertTrue( unicode( authentication ) )
        
    def test_person_contact_mechanism( self ):
        from camelot.model.party import Person
        mechanism_1 = (u'email', u'robin@test.org')
        mechanism_2 = (u'email', u'robin@test.com')
        person = Person( first_name = u'Robin',
                         last_name = u'The brave' )
        self.assertEqual( person.email, None )
        person.email = mechanism_1
        self.person_admin.flush( person )
        self.assertEqual( person.email, mechanism_1 )
        person.email = mechanism_2
        self.assertEqual( person.email, mechanism_2 )
        self.person_admin.delete( person )
        person = Person( first_name = u'Robin',
                         last_name = u'The brave' )
        self.person_admin.flush( person )
        self.assertEqual( person.email, None )
        person.email = mechanism_2
        person.email = None
        self.assertEqual( person.email, None )
        self.person_admin.flush( person )
        self.assertEqual( person.email, None )

class FixtureCase( ModelThreadTestCase ):
    """Test the build in camelot model for fixtures"""
      
    def test_fixture( self ):
        from camelot.model.party import Person
        from camelot.model.fixture import Fixture
        session = Session()
        self.assertEqual( Fixture.find_fixture_key( Person, -1 ), None )
        p1 = Person()
        self.assertEqual( Fixture.find_fixture_key_and_class( p1 ), 
                          (None, None) )
        session.expunge( p1 )
        # insert a new Fixture
        p2 = Fixture.insert_or_update_fixture( Person, 'test',
                                               {'first_name':'Peter',
                                                'last_name':'Principle'},
                                               fixture_class = 'test' )
        # see if we can find it back
        self.assertEqual( Fixture.find_fixture_key( Person, p2.id ), 'test' )
        self.assertEqual( Fixture.find_fixture_key_and_class( p2 ), 
                          ('test', 'test') )
        self.assertEqual( Fixture.find_fixture_keys_and_classes( Person )[p2.id],
                          ('test', 'test') )
        # delete the person, and insert it back in the same fixture
        session.delete( p2 )
        session.flush()
        p3 = Fixture.insert_or_update_fixture( Person, 'test',
                                               {'first_name':'Peter',
                                                'last_name':'Principle'},
                                               fixture_class = 'test' )
        self.assertNotEqual( p2, p3 )
        # remove all fixtures
        Fixture.remove_all_fixtures( Person )
        
    def test_fixture_version( self ):
        from camelot.model.party import Person
        from camelot.model.fixture import FixtureVersion
        self.assertEqual( FixtureVersion.get_current_version( u'unexisting' ),
                          0 )        
        FixtureVersion.set_current_version( u'demo_data', 0 )
        self.assertEqual( FixtureVersion.get_current_version( u'demo_data' ),
                          0 )
        example_file = os.path.join( os.path.dirname(__file__), 
                                     '..', 
                                     'camelot_example',
                                     'import_example.csv' )
        person_count_before_import = Person.query.count()
        # begin load csv if fixture version
        import csv
        if FixtureVersion.get_current_version( u'demo_data' ) == 0:
            reader = csv.reader( open( example_file ) )
            for line in reader:
                Person( first_name = line[0], last_name = line[1] )
            FixtureVersion.set_current_version( u'demo_data', 1 )
            Person.query.session.flush()
        # end load csv if fixture version
        self.assertTrue( Person.query.count() > person_count_before_import )
        self.assertEqual( FixtureVersion.get_current_version( u'demo_data' ),
                          1 )
        
class StatusCase( TestMetaData ):
    
    def test_status_type( self ):
        Entity, session = self.Entity, self.session
        
        #begin status type definition
        from camelot.model import type_and_status
        
        class Invoice( Entity, type_and_status.StatusMixin ):
            book_date = schema.Column( types.Date(), nullable = False )
            status = type_and_status.Status()
            
        #end status type definition
        self.create_all()
        self.assertTrue( issubclass( Invoice._status_type, type_and_status.StatusType ) )
        self.assertTrue( issubclass( Invoice._status_history, type_and_status.StatusHistory ) )
        #begin status types definition
        draft = Invoice._status_type( code = 'DRAFT' )
        ready = Invoice._status_type( code = 'READY' )
        session.flush()
        #end status types definition
        self.assertTrue( unicode( ready ) )
        #begin status type use
        invoice = Invoice( book_date = datetime.date.today() )
        self.assertEqual( invoice.current_status, None )
        invoice.change_status( draft, status_from_date = datetime.date.today() )
        #end status type use
        self.assertEqual( invoice.current_status, draft )
        self.assertEqual( invoice.get_status_from_date( draft ), datetime.date.today() )
        self.assertTrue( len( invoice.status ) )
        for history in invoice.status:
            self.assertTrue( unicode( history ) )
        
    def test_status_enumeration( self ):
        Entity, session = self.Entity, self.session
        
        #begin status enumeration definition
        from camelot.model import type_and_status
        
        class Invoice( Entity, type_and_status.StatusMixin ):
            book_date = schema.Column( types.Date(), nullable = False )
            status = type_and_status.Status( enumeration = [ (1, 'DRAFT'),
                                                             (2, 'READY') ] )
            
            class Admin( EntityAdmin ):
                list_display = ['book_date', 'current_status']
                list_actions = [ type_and_status.ChangeStatus( 'DRAFT' ),
                                 type_and_status.ChangeStatus( 'READY' ) ]
                form_actions = list_actions
                
        #end status enumeration definition
        self.create_all()
        self.assertTrue( issubclass( Invoice._status_history, type_and_status.StatusHistory ) )
        #begin status enumeration use
        invoice = Invoice( book_date = datetime.date.today() )
        self.assertEqual( invoice.current_status, None )
        invoice.change_status( 'DRAFT', status_from_date = datetime.date.today() )
        self.assertEqual( invoice.current_status, 'DRAFT' )
        self.assertEqual( invoice.get_status_from_date( 'DRAFT' ), datetime.date.today() )
        draft_invoices = Invoice.query.filter( Invoice.current_status == 'DRAFT' ).count()
        ready_invoices = Invoice.query.filter( Invoice.current_status == 'READY' ).count()        
        #end status enumeration use
        self.assertEqual( draft_invoices, 1 )
        self.assertEqual( ready_invoices, 0 )
        ready_action = Invoice.Admin.list_actions[-1]
        model_context = MockModelContext()
        model_context.obj = invoice
        list( ready_action.model_run( model_context ) )
        self.assertTrue( invoice.current_status, 'READY' )
