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

from camelot.core.orm import Entity, Session
from camelot.types import PrimaryKey



from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Integer

"""Classes to support the loading and updating of required datasets into the 
database.  The use of this classes is documented in the reference
documentation : :ref:`doc-fixtures`"""

class Fixture( Entity ):
    """Keep track of static data loaded into the database.  This class keeps
    track of data inserted into the database by storing the primary key and
    the class name of the inserted data, and associating this with a `fixture
    key` specified by the developer.  

    The developer can then use the `fixture key` to find out if this data has
    been stored in the database, or to update it in future versions of the 
    application.
    
    Only classes which have an integer field as their primary key can be 
    tracked."""
    
    __tablename__ = 'fixture'
    
    model = Column( Unicode( 255 ), index = True, nullable=False )
    primary_key = Column( PrimaryKey(), 
                          index = True, nullable=False )
    fixture_key = Column( Unicode( 255 ), index = True, nullable=False )
    fixture_class = Column( Unicode( 255 ), index = True, nullable=True )

    @classmethod
    def find_fixture_reference( cls, 
                                entity, 
                                fixture_key, 
                                fixture_class = None ):
        """Find the :class:`Fixture` instance that refers to the data
        stored for a fixture key.
        
        :param entity: the class of the stored data
        :param fixture_key: a string used to refer to the stored data
        :param fixture_class: a string used to refer to a group of stored data
        :return: a :class:`Fixture` instance refering to the stored data, or
            None of no data was found.
        """
        entity_name = str( entity.__name__ )
        return Session().query( cls ).filter_by( model = str( entity_name ), 
                                                 fixture_key = fixture_key, 
                                                 fixture_class = fixture_class ).first()

    @classmethod
    def find_fixture( cls, entity, fixture_key, fixture_class = None ):
        """Find data that has been stored for a fixture key.

        :param entity: the class of the stored data
        :param fixture_key: a string used to refer to the stored data
        :param fixture_class: a string used to refer to a group of stored data
        :return: a instance of type entity, or None if no fixture is found"""
        reference = cls.find_fixture_reference( entity, 
                                                fixture_key, 
                                                fixture_class )
        if reference:
            return entity.get( reference.primary_key )

    @classmethod
    def find_fixture_key( cls, entity, primary_key ):
        """Find the fixture key for an object of type entity with primary key

        :param entity: the class of the stored data
        :param primary_key: the integer primary key of the stored data
        :return: a string with the fixture_key that refers to this data, None
            if no such data is found
        """
        entity_name = str( entity.__name__ )
        fixture = Session().query( cls ).filter_by( model = entity_name, 
                                                    primary_key = primary_key ).first()
        if fixture:
            return fixture.fixture_key
        else:
            return None
        
    @classmethod
    def find_fixture_key_and_class( cls, obj ):
        """Find out if an object was stored in the database through the fixture
        mechanism and return its `fixture_key` and `fixture_class`

        :param obj: the object stored in the database
        :return: (fixture_key, fixture_class) if the object was registered
        through the fixture mechanism, (None, None) otherwise
        """
        entity_name = str( obj.__class__.__name__ )
        fixture = Session().query( cls ).filter_by( model = entity_name, 
                                                    primary_key = obj.id ).first()
        if fixture:
            return ( fixture.fixture_key, fixture.fixture_class )
        else:
            return ( None, None )
        
    @classmethod
    def find_fixture_keys_and_classes( cls, entity ):
        """Load all fixture keys of a certain entity class in batch.

        :param entity: the class of the stored data
        :return: a dictionary mapping the primary key of a on object of type 
            entity to a tuple of type (fixture key, fixture class)
        """
        entity_name = str( entity.__name__ )
        fixtures = Session().query( cls ).filter_by( model = entity_name ).all()
        return dict( ( f.primary_key, (f.fixture_key, 
                                       f.fixture_class) ) for f in fixtures )

    @classmethod
    def insert_or_update_fixture( cls, 
                                  entity, 
                                  fixture_key, 
                                  values, 
                                  fixture_class = None ):
        """Store data in the database through the fixture mechanism, to be
        able to keep track of it later.
        
        :param entity: the class of the stored data
        :param fixture_key: a string used to refer to the stored data
        :param values: a dictionary with the data that should be insert or
           updated in the database
        :param fixture_class: a string used to refer to a group of stored data
        :return: an object of type entity, either created or modified
        """
        from sqlalchemy.orm.session import Session
        obj = cls.find_fixture( entity, fixture_key, fixture_class )
        store_fixture = False
        if not obj:
            obj = entity()
            store_fixture = True
        obj.from_dict( values )
        Session.object_session( obj ).flush()
        if store_fixture:
            #
            # The fixture itself might have been deleted, but the reference 
            # might be intact, so this should be updated
            #
            reference = cls.find_fixture_reference( entity, 
                                                    fixture_key, 
                                                    fixture_class )
            if not reference:
                reference = cls( model = str( entity.__name__ ), 
                                 primary_key = obj.id, 
                                 fixture_key = fixture_key, 
                                 fixture_class = fixture_class )
            else:
                reference.primary_key = obj.id
            Session.object_session( reference ).flush()
        return obj
    
    @classmethod
    def remove_all_fixtures( cls, entity ):
        """
        Remove all data of a certain class from the database, if it was stored
        through the fixture mechanism.
        
        :param entity: the class of the stored data
        """
        keys_and_classes = cls.find_fixture_keys_and_classes(entity).values()
        for fixture_key, fixture_class in keys_and_classes:
            cls.remove_fixture( entity, fixture_key, fixture_class )
            
    @classmethod
    def remove_fixture( cls, entity, fixture_key, fixture_class ):
        """
        Remove data from the database, if it was stored through the fixture 
        mechanism.
        
        :param entity: the class of the stored data
        :param fixture_key: a string used to refer to the stored data
        :param fixture_class: a string used to refer to a group of stored data

        """
        # remove the object itself
        from sqlalchemy.orm.session import Session
        obj = cls.find_fixture( entity, fixture_key, fixture_class)
        obj.delete()
        Session.object_session( obj ).flush()
        # if this succeeeds, remove the reference
        reference = cls.find_fixture_reference( entity, 
                                                fixture_key, 
                                                fixture_class )
        reference.delete()
        Session.object_session( reference ).flush()
        
class FixtureVersion( Entity ):
    """Keep track of the version the fixtures have in the current database, the 
    subversion revision number is a good candidate to be used as a fixture 
    version.
    """
    
    __tablename__ = 'fixture_version'
    
    fixture_version = Column( Integer, index = True, nullable=False, default=0 )
    fixture_class = Column( Unicode( 255 ), index = True, nullable=True,
                            primary_key=True )
    
    @classmethod
    def get_current_version( cls, fixture_class = None, session = None):
        """Get the current version of the fixtures in the database for a certain 
        fixture class.
        
        :param fixture_class: the fixture class for which to get the version
        :param session: the session to use to query the database, if `None` is
            given, the default Camelot session is used
        
        :return: an integer representing the current version, 0 if no version found
        """
        if session is None:
            session = Session()
        obj = session.query( cls ).filter_by(fixture_class = fixture_class).first()
        if obj:
            return obj.fixture_version
        return 0
        
    @classmethod
    def set_current_version( cls, fixture_class = None, fixture_version = 0,
                             session = None):
        """Set the current version of the fixtures in the database for a certain 
        fixture class.
        
        :param fixture_class: the fixture class for which to get the version
        :param fixture_version: the version number to which to set the fixture 
            version
        :param session: the session to use to query the database, if `None` is
            given, the default Camelot session is used
        """
        if session is None:
            session = Session()
        obj = session.query( cls ).filter_by(fixture_class = fixture_class).first()
        if not obj:
            obj = FixtureVersion(fixture_class = fixture_class,
                                 _session = session)
        obj.fixture_version = fixture_version
        session.flush()

