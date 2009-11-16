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
