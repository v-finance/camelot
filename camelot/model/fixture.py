#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
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
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
from camelot.model import metadata
from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from sqlalchemy.types import Unicode, INT
"""Classes to support the loading of required datasets into the 
database"""


__metadata__ = metadata

class Fixture( Entity ):
    """Keep track of static data loaded into the database"""
    using_options( tablename = 'fixture' )
    model = Field( Unicode( 256 ), index = True, required = True )
    primary_key = Field( INT(), index = True, required = True )
    fixture_key = Field( Unicode( 256 ), index = True, required = True )
    fixture_class = Field( Unicode( 256 ), index = True, required = False )

    @classmethod
    def findFixtureReference( cls, entity, fixture_key, fixture_class = None ):
        entity_name = unicode( entity.__name__ )
        return cls.query.filter_by( model = unicode( entity_name ), fixture_key = fixture_key, fixture_class = fixture_class ).first()

    @classmethod
    def findFixture( cls, entity, fixture_key, fixture_class = None ):
        """Find a registered fixture, return None if no fixture is found"""
        reference = cls.findFixtureReference( entity, fixture_key, fixture_class )
        if reference:
            return entity.get( reference.primary_key )

    @classmethod
    def findFixtureKey( cls, entity, primary_key ):
        """Find the fixture key for an object of type entity with primary key
        :return: fixture_key        
        """
        entity_name = unicode( entity.__name__ )
        fixture = cls.query.filter_by( model = entity_name, primary_key = primary_key ).first()
        if fixture:
            return fixture.fixture_key
        else:
            return None
        
    @classmethod
    def findFixtureKeyAndClass( cls, obj ):
        """Find the fixture key and class of an object
        @param obj: the object we are looking for 
        @return: (fixture_key, fixture_class) if the object is a registered fixture, (None, None) otherwise
        """
        entity_name = unicode( obj.__class__.__name__ )
        fixture = cls.query.filter_by( model = entity_name, primary_key = obj.id ).first()
        if fixture:
            return ( fixture.fixture_key, fixture.fixture_class )
        else:
            return ( None, None )
        
    @classmethod
    def findFixtureKeysAndClasses( cls, entity ):
        """Load all fixture keys of a certain entity in batch
        :param entity: the model class for which the fixtures should be found
        :return: a dictionary mapping the primary key of a on object of type entity to its (fixture key, fixture class)
        """
        entity_name = unicode( entity.__name__ )
        return dict((fixture.primary_key, (fixture.fixture_key, fixture.fixture_class)) for fixture in cls.query.filter_by( model = entity_name ).all())

    @classmethod
    def insertOrUpdateFixture( cls, entity, fixture_key, values, fixture_class = None ):
        from sqlalchemy.orm.session import Session
        obj = cls.findFixture( entity, fixture_key, fixture_class )
        store_fixture = False
        if not obj:
            obj = entity()
            store_fixture = True
        obj.from_dict( values )
        Session.object_session( obj ).flush( [obj] )
        if store_fixture:
            #
            # The fixture itself might have been deleted, but the reference might be intact,
            # so this should be updated
            #
            reference = cls.findFixtureReference( entity, fixture_key, fixture_class )
            if not reference:
                reference = cls( model = unicode( entity.__name__ ), primary_key = obj.id, fixture_key = fixture_key, fixture_class = fixture_class )
            else:
                reference.primary_key = obj.id
            Session.object_session( reference ).flush( [reference] )
        return obj
    
    @classmethod
    def removeAllFixtures( cls, entity ):
        for fixture_key, fixture_class in cls.findFixtureKeysAndClasses( entity ).values():
            cls.removeFixture(entity, fixture_key, fixture_class)
            
    @classmethod
    def removeFixture( cls, entity, fixture_key, fixture_class ):
        """Remove a fixture from the database"""
        # remove the object itself
        from sqlalchemy.orm.session import Session
        obj = cls.findFixture( entity, fixture_key, fixture_class)
        print 'remove', unicode(obj)
        obj.delete()
        Session.object_session( obj ).flush( [obj] )
        # if this succeeeds, remove the reference
        reference = cls.findFixtureReference(entity, fixture_key, fixture_class)
        reference.delete()
        Session.object_session( reference ).flush( [reference] )
        

class FixtureVersion( Entity ):
    """Keep track of the version the fixtures have in the current database, the subversion
    revision number is a good candidate to be used as a fixture version.
    
    :return: an integer representing the current version, 0 if no version found
    """
    using_options( tablename = 'fixture_version' )
    fixture_version = Field( INT(), index = True, required = True, default=0 )
    fixture_class = Field( Unicode( 256 ), index = True, required = False, unique=True )    
    
    @classmethod
    def get_current_version( cls, fixture_class = None ):
        """Get the current version of the fixtures in the database for a certain 
        fixture class.
        
        :param fixture_class: the fixture class for which to get the version
        """
        obj = cls.query.filter_by( fixture_class = fixture_class ).first()
        if obj:
            return obj.fixture_version
        return 0
        
    @classmethod
    def set_current_version( cls, fixture_class = None, fixture_version = 0 ):
        """Set the current version of the fixtures in the database for a certain 
        fixture class.
        
        :param fixture_class: the fixture class for which to get the version
        :param fixture_version: the version number to which to set the fixture version
        """
        from sqlalchemy.orm.session import Session
        obj = cls.query.filter_by( fixture_class = fixture_class ).first()
        if not obj:
            obj = FixtureVersion( fixture_class = fixture_class )
        obj.fixture_version = fixture_version
        Session.object_session( obj ).flush( [obj] ) 

