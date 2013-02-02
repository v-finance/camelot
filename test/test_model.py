import datetime
import os

from sqlalchemy import orm
from sqlalchemy import schema, types

from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Session
from camelot.model import party
from camelot.test import ModelThreadTestCase
from camelot.test.action import MockModelContext
from .test_orm import TestMetaData

class ModelCase( ModelThreadTestCase ):
    """Test the build in camelot model"""
        
    def test_memento( self ):
        from camelot.model import memento
        from camelot.model.authentication import get_current_authentication
        m = memento.Memento( primary_key = 1,
                             model = 'TestCase',
                             authentication = get_current_authentication(),
                             memento_type = 1,
                             previous_attributes = {'name':u'memento'} )
        self.assertTrue( m.previous )
        
    def test_i18n( self ):
        from camelot.model.i18n import Translation, ExportAsPO
        session = Session()
        session.execute( Translation.__table__.delete() )
        self.assertEqual( Translation.translate( 'bucket', 'nl_BE' ), None )
        # run twice to check all branches in the code
        Translation.translate_or_register( 'bucket', 'nl_BE' )
        Translation.translate_or_register( 'bucket', 'nl_BE' )
        self.assertEqual( Translation.translate( 'bucket', 'nl_BE' ), 'bucket' )
        self.assertEqual( Translation.translate( '', 'nl_BE' ), '' )
        self.assertEqual( Translation.translate_or_register( '', 'nl_BE' ), '' )
        # clear the cache
        Translation._cache.clear()
        # fill the cache again
        translation = Translation( language = 'nl_BE', source = 'bucket',
                                   value = 'emmer', uid=1 )
        orm.object_session( translation ).flush()
        self.assertEqual( Translation.translate( 'bucket', 'nl_BE' ), 'emmer' )
        export_action = ExportAsPO()
        model_context = MockModelContext()
        model_context.obj = translation
        try:
            generator = export_action.model_run( model_context )
            file_step = generator.next()
            generator.send( ['/tmp/test.po'] )
        except StopIteration:
            pass
        
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

class PartyCase( ModelThreadTestCase ):
    """Test the build in party - address - contact mechanism model"""
  
    def setUp(self):
        super( PartyCase, self ).setUp()
        from camelot.admin.application_admin import ApplicationAdmin
        self.session = Session()
        self.app_admin = ApplicationAdmin()
        self.person_admin = self.app_admin.get_related_admin( party.Person )
        self.organization_admin = self.app_admin.get_related_admin( party.Organization )
        
    def tearDown(self):
        self.session.expunge_all()
       
    def test_party( self ):
        p = party.Party()
        self.assertFalse( p.name )
        
    def test_geographic_boundary( self ):
        belgium = party.Country.get_or_create( code = u'BE', 
                                               name = u'Belgium' )
        self.assertTrue( unicode( belgium ) )
        city = party.City.get_or_create( country = belgium,
                                         code = '1000',
                                         name = 'Brussels' )
        return city
        
    def test_address( self ):
        city = self.test_geographic_boundary()
        address = party.Address.get_or_create( street1 = 'Avenue Louise',
                                               street2 = None,
                                               city = city )
        self.assertTrue( unicode( address ) )
        return address
    
    def test_party_address( self ):
        city = self.test_geographic_boundary()
        org = self.test_organization()
        party_address = party.PartyAddress( party = org )
        party_address.street1 = 'Avenue Louise 5'
        party_address.street2 = 'Boite 4'
        party_address.city = city
        party_address_admin = party.AddressAdmin( self.app_admin, party.PartyAddress )
        party_address_admin.flush( party_address )
        party_address_admin.refresh( party_address )
        # test hybrid property getters on Party and PartyAddress
        self.assertEqual( party_address.street1, 'Avenue Louise 5' )
        self.assertEqual( party_address.street2, 'Boite 4' )
        self.assertEqual( party_address.city, city )
        self.assertEqual( org.street1, 'Avenue Louise 5' )
        self.assertEqual( org.street2, 'Boite 4' )
        self.assertEqual( org.city, city )        
        self.assertTrue( unicode( party_address ) )
        query = self.session.query( party.PartyAddress )
        self.assertTrue( query.filter( party.PartyAddress.street1 == 'Avenue Louise 5' ).first() )
        self.assertTrue( query.filter( party.PartyAddress.street2 == 'Boite 4' ).first() )
        # if party address changes, party should be updated
        depending_objects = list( party_address_admin.get_depending_objects( party_address ) )
        self.assertTrue( org in depending_objects )
        # if address changes, party address and party should be updated
        address = party_address.address
        address_admin = self.app_admin.get_related_admin( party.Address )
        depending_objects = list( address_admin.get_depending_objects( address ) )
        self.assertTrue( party_address in depending_objects )
        self.assertTrue( org in depending_objects )
        # test hybrid property setters on Party
        org.street1 = 'Rue Belliard 1'
        org.street2 = 'Second floor'
        org.city = None
        
    def test_person( self ):
        person = party.Person( first_name = u'Robin',
                               last_name = u'The brave' )
        self.assertEqual( person.email, None )
        self.assertEqual( person.phone, None )
        self.assertEqual( person.fax, None )
        self.assertEqual( person.street1, None )
        self.assertEqual( person.street2, None )
        self.assertEqual( person.city, None )
        self.person_admin.flush( person )
        person2 = party.Person( first_name = u'Robin' )
        self.assertFalse( person2.note )
        person2.last_name = u'The brave'
        # gui should warn this person exists
        self.assertTrue( person2.note )
        return person
        
    def test_contact_mechanism( self ):
        contact_mechanism = party.ContactMechanism( mechanism = (u'email', u'info@test.be') )
        self.assertTrue( unicode( contact_mechanism ) )
        
    def test_person_contact_mechanism( self ):
        # create a new person
        person = party.Person( first_name = u'Robin',
                               last_name = u'The brave' )
        self.person_admin.flush( person )
        self.assertEqual( person.email, None )
        # set the contact mechanism
        mechanism_1 = (u'email', u'robin@test.org')
        person.email = mechanism_1
        self.person_admin.flush( person )
        self.assertEqual( person.email, mechanism_1 )
        # change the contact mechanism, after a flush
        mechanism_2 = (u'email', u'robin@test.com')
        person.email = mechanism_2
        self.person_admin.flush( person )
        self.assertEqual( person.email, mechanism_2 )
        # remove the contact mechanism after a flush
        person.email = ('email', '')
        self.assertEqual( person.email, None )
        self.person_admin.flush( person )
        self.assertEqual( person.email, None )
        admin = party.PartyContactMechanismAdmin( self.app_admin, 
                                                  party.PartyContactMechanism )
        contact_mechanism = party.ContactMechanism( mechanism = mechanism_1 )
        party_contact_mechanism = party.PartyContactMechanism( party = person,
                                                               contact_mechanism = contact_mechanism )
        admin.flush( party_contact_mechanism )
        admin.refresh( party_contact_mechanism )
        list( admin.get_depending_objects( party_contact_mechanism ) )
        #
        # if the contact mechanism changes, the party person should be 
        # updated as well
        #
        contact_mechanism_admin = self.app_admin.get_related_admin( party.ContactMechanism )
        depending_objects = list( contact_mechanism_admin.get_depending_objects( contact_mechanism ) )
        self.assertTrue( person in depending_objects )
        self.assertTrue( party_contact_mechanism in depending_objects )
        #
        # if the party contact mechanism changes, the party should be updated
        # as well
        depending_objects = list( admin.get_depending_objects( party_contact_mechanism ) )
        self.assertTrue( person in depending_objects )
        # delete the person
        self.person_admin.delete( person )
        
    def test_organization( self ):
        org = party.Organization( name = 'PSF' )
        org.email = ('email', 'info@python.org')
        org.phone = ('phone', '1234')
        org.fax = ('fax', '4567')
        self.organization_admin.flush( org )
        self.assertTrue( unicode( org ) )
        self.assertEqual( org.number_of_shares_issued, 0 )
        query = orm.object_session( org ).query( party.Organization )
        self.assertTrue( query.filter( party.Organization.email == ('email', 'info@python.org') ).first() )
        self.assertTrue( query.filter( party.Organization.phone == ('phone', '1234') ).first() )
        self.assertTrue( query.filter( party.Organization.fax == ('fax', '4567') ).first() )
        return org
    
    def test_party_relationship( self ):
        person = self.test_person()
        org = self.test_organization()
        employee = party.EmployerEmployee( established_from = org,
                                           established_to = person )
        self.assertTrue( unicode( employee ) )
        
    def test_party_contact_mechanism( self ):
        person = self.test_person()
        party_contact_mechanism = party.PartyContactMechanism( party = person )
        party_contact_mechanism.mechanism = (u'email', u'info@test.be')
        party_contact_mechanism.mechanism = (u'email', u'info2@test.be')
        self.session.flush()
        self.assertTrue( unicode( party_contact_mechanism ) )
        query = self.session.query( party.PartyContactMechanism )
        self.assertTrue( query.filter( party.PartyContactMechanism.mechanism == (u'email', u'info2@test.be') ).first() )
        # party contact mechanism is only valid when contact mechanism is
        # valid
        party_contact_mechanism_admin = self.app_admin.get_related_admin( party.PartyContactMechanism )
        compounding_objects = list( party_contact_mechanism_admin.get_compounding_objects( party_contact_mechanism ) )
        self.assertTrue( party_contact_mechanism.contact_mechanism in compounding_objects )
        party_contact_mechanism_validator = party_contact_mechanism_admin.get_validator()
        self.assertFalse( party_contact_mechanism_validator.validate_object( party_contact_mechanism ) )
        party_contact_mechanism.contact_mechanism.mechanism = None
        self.assertTrue( party_contact_mechanism_validator.validate_object( party_contact_mechanism ) )
        # the party is only valid when the contact mechanism is
        # valid
        party_admin = self.app_admin.get_related_admin( party.Person )
        party_validator = party_admin.get_validator()
        self.assertTrue( party_validator.validate_object( person ) )
        
    def test_party_category( self ):
        org = self.test_organization()
        category = party.PartyCategory( name = u'Imortant' )
        category.parties.append( org )
        self.session.flush()
        self.assertTrue( list( category.get_contact_mechanisms( u'email') ) )
        self.assertTrue( unicode( category ) )

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
