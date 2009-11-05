from sqlalchemy import *
from migrate import *
from migrate.changeset import *
from elixir import *
from elixir.ext.associable import *

import datetime

import camelot.types

metadata = MetaData(migrate_engine)
__metadata__ = metadata

#
# Make sure these entities don't get mixed up with those in the model itself,
# so put them in a separate collection
#

initial_entities = EntityCollection()
__entity_collection__ = initial_entities

#
# Initial Camelot models
#

def end_of_times():
    return datetime.date(year=2400, month=12, day=31)

class Fixture(Entity):
    using_options(tablename='fixture')
    model = Field(Unicode(256), index=True, required=True)
    primary_key = Field(INT(), index=True, required=True)
    fixture_key = Field(Unicode(256), index=True, required=True)
    fixture_class = Field(Unicode(256), index=True, required=False)

class Translation(Entity):
    using_options(tablename='translation')
    language = Field(Unicode(20), index=True)
    source = Field(Unicode(500), index=True)
    value = Field(Unicode(500))
    cid = Field(INT(), default=0, index=True)
    uid = Field(INT(), default=0, index=True)

class Memento(Entity):
    using_options(tablename='memento')
    model = Field(Unicode(256), index=True, required=True)
    primary_key = Field(INT(), index=True, required=True)
    creation_date = Field(DateTime(), default=datetime.datetime.now)
    authentication = ManyToOne('AuthenticationMechanism',
                               required=True,
                               ondelete='restrict',
                               onupdate='cascade')

class BeforeUpdate(Memento):
    using_options(inheritance='multi', tablename='memento_update',)
    previous_attributes = Field(PickleType())

class BeforeDelete(Memento):
    using_options(inheritance='multi', tablename='memento_delete',)
    previous_attributes = Field(PickleType())

class Create(Memento):
    using_options(inheritance='multi', tablename='memento_create',)

class Synchronized(Entity):
    using_options(tablename='synchronized')
    database = Field(Unicode(30), index=True)
    tablename = Field(Unicode(30), index=True)
    primary_key = Field(Integer(), index=True)
    last_update = Field(DateTime(), index=True, default=datetime.datetime.now, onupdate=datetime.datetime.now)

is_synchronized = associable(Synchronized)

class PartyRelationship(Entity):
    using_options(tablename='party_relationship')
    from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
    thru_date = Field(Date(), default=end_of_times, required=True, index=True)
    comment = Field(camelot.types.RichText())
    is_synchronized('synchronized', lazy=True)

class EmployerEmployee(PartyRelationship):
    using_options(tablename='party_relationship_empl', inheritance='multi')
    established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
    established_to = ManyToOne('Person', required=True, ondelete='cascade', onupdate='cascade')

class DirectedDirector(PartyRelationship):
    using_options(tablename='party_relationship_dir', inheritance='multi')
    established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
    established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
    title = Field(Unicode(256))
    represented_by = OneToMany('RepresentedRepresentor', inverse='established_to')

class RepresentedRepresentor(Entity):
    using_options(tablename='party_representor')
    from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
    thru_date = Field(Date(), default=end_of_times, required=True, index=True)
    comment = Field(camelot.types.RichText())
    established_from = ManyToOne('Person', required=True, ondelete='cascade', onupdate='cascade')
    established_to = ManyToOne('DirectedDirector', required=True, ondelete='cascade', onupdate='cascade')

class SupplierCustomer(PartyRelationship):
    using_options(tablename='party_relationship_suppl', inheritance='multi')
    established_from = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
    established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')

class SharedShareholder(PartyRelationship):
    using_options(tablename='party_relationship_shares', inheritance='multi')
    established_from = ManyToOne('Organization', required=True, ondelete='cascade', onupdate='cascade')
    established_to = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
    shares = Field(Integer())

class Party(Entity):
    using_options(tablename='party')
    is_synchronized('synchronized', lazy=True)
    addresses = OneToMany('PartyAddress', lazy=True)
    contact_mechanisms = OneToMany('PartyContactMechanism', lazy=True)
    shares = OneToMany('SharedShareholder', inverse='established_to')
    directed_organizations = OneToMany('DirectedDirector', inverse='established_to')

class Organization(Party):
    using_options(tablename='organization', inheritance='multi')
    name = Field(Unicode(50), required=True, index=True)
    logo = Field(camelot.types.Image(upload_to='organization-logo'), deferred=True)
    tax_id = Field(Unicode(20))
    directors = OneToMany('DirectedDirector', inverse='established_from')
    employees = OneToMany('EmployerEmployee', inverse='established_from')
    suppliers = OneToMany('SupplierCustomer', inverse='established_to')
    customers = OneToMany('SupplierCustomer', inverse='established_from')
    shareholders = OneToMany('SharedShareholder', inverse='established_from')

class AuthenticationMechanism(Entity):
    using_options(tablename='authentication_mechanism')
    last_login = Field(DateTime())
    is_active = Field(Boolean, default=True, index=True)

class UsernameAuthenticationMechanism(AuthenticationMechanism):
    using_options(tablename='authentication_mechanism_username', inheritance='multi')
    username = Field(Unicode(40), required=True, index=True, unique=True)
    password = Field(Unicode(200), required=False, index=False, default=None)

class Person(Party):
    using_options(tablename='person', inheritance='multi')
    first_name = Field(Unicode(40), required=True)
    last_name =  Field(Unicode(40), required=True)
    middle_name = Field(Unicode(40))
    personal_title = Field(Unicode(10))
    suffix = Field(Unicode(3))
    sex = Field(Unicode(1), default=u'M')
    birthdate = Field(Date())
    martial_status = Field(Unicode(1))
    social_security_number = Field(Unicode(12))
    passport_number = Field(Unicode(20))
    passport_expiry_date = Field(Date())
    is_staff = Field(Boolean, default=False, index=True)
    is_superuser = Field(Boolean, default=False, index=True)
    picture = Field(camelot.types.Image(upload_to='person-pictures'), deferred=True)
    comment = Field(camelot.types.RichText())
    employers = OneToMany('EmployerEmployee', inverse='established_to')

class GeographicBoundary(Entity):
    using_options(tablename='geographic_boundary')

class Country(GeographicBoundary):
    using_options(tablename='geographic_boundary_country', inheritance='multi')

class City(GeographicBoundary):
    using_options(tablename='geographic_boundary_city', inheritance='multi')
    country = ManyToOne('Country', required=True, ondelete='cascade', onupdate='cascade')

class Address(Entity):
    using_options(tablename='address')
    street1 = Field(Unicode(128), required=True)
    street2 = Field(Unicode(128))
    city = ManyToOne('City', required=True, ondelete='cascade', onupdate='cascade')
    is_synchronized('synchronized', lazy=True)

class PartyAddressRoleType(Entity):
    using_options(tablename='party_address_role_type')
    code = Field(Unicode(10))
    description = Field(Unicode(40))

class PartyAuthentication(Entity):
    using_options(tablename='party_authentication')
    address = ManyToOne('AuthenticationMechanism', required=True, ondelete='cascade', onupdate='cascade')
    from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
    thru_date = Field(Date(), default=end_of_times, required=True, index=True)
    comment = Field(Unicode(256))

class PartyAddress(Entity):
    using_options(tablename='party_address')
    party = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
    address = ManyToOne('Address', required=True, ondelete='cascade', onupdate='cascade')
    from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
    thru_date = Field(Date(), default=end_of_times, required=True, index=True)
    comment = Field(Unicode(256))

class ContactMechanism(Entity):
    using_options(tablename='contact_mechanism')
    mechanism = Field(camelot.types.VirtualAddress(256), required=True)
    party_address = ManyToOne('PartyAddress', ondelete='set null', onupdate='cascade')

class PartyContactMechanism(Entity):
    using_options(tablename='party_contact_mechanism')
    party = ManyToOne('Party', required=True, ondelete='cascade', onupdate='cascade')
    contact_mechanism = ManyToOne('ContactMechanism', required=True, ondelete='cascade', onupdate='cascade')
    from_date = Field(Date(), default=datetime.date.today, required=True, index=True)
    thru_date = Field(Date(), default=end_of_times, index=True)
    comment = Field(Unicode(256))

setup_entities(initial_entities)

def upgrade():
    metadata.create_all()

def downgrade():
    metadata.drop_all()
