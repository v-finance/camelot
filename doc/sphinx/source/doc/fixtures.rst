.. _doc-fixtures:

#################################################
 Fixtures : handling static data in the database
#################################################

Some tables need to be filled with default data when users start
to work with the application.  The Camelot fixture module 
:mod:`camelot.model.fixture` assist in handling this kind of data.
	
Suppose we have an entity `PartyCategory` to divide Persons and Organizations
into certain groups.  

.. literalinclude:: ../../../../camelot/model/authentication.py
   :start-after: begin category definition
   :end-before: end category definition
   
The complete definition of such an entity can be found in 
:class:`camelot.model.authentication.PartyCategory`.

To make things easier for the first time user, some prefab categories should
be available when the user starts the application.  Such as `Suspect`, 
`Prospect`, `VIP`.
	  
When to update fixtures
-----------------------

Most of the time static data should be created or updated right after the
model has been set up and before the user starts using the application.

The easiest place to do this is in the setup_model method inside the
settings.py module.

So we rewrite settings.py to include a call to a new update_fixtures
method::

	def update_fixtures():
	  """Update static data in the database"""
	  from camelot.model.fixture import Fixture
	  from model import MovieType
	  
	def setup_model():
	  from camelot.model import *
	  from camelot.model.memento import *
	  from camelot.model.synchronization import *
	  from camelot.model.authentication import *
	  from camelot.model.i18n import *
	  from camelot.model.fixture import *
	  from model import *
	  setup_all(create_tables=True)
	  updateLastLogin()
	  update_fixtures()
 
Creating new data
-----------------

When creating new data with the fixture module, a reference to the created
data will be stored in the fixture table along with a 'fixture key'.  This
fixture key can be used later to retrieve or update the created data.

So lets create some new movie types::

	def update_fixtures():
	  """Update static data in the database"""
	  from camelot.model.fixture import Fixture
	  from model import MovieType
	  Fixture.insertOrUpdateFixture(MovieType,
	                                fixture_key = 'comic',
	                                values = dict(name='Comic'))
	  Fixture.insertOrUpdateFixture(MovieType,
	                                fixture_key = 'scifi',
	                                values = dict(name='Science Fiction'))
	                                
Fixture keys should be unique for each Entity class.

Update fixtures
---------------

When a new version of the application gets released, we might want to change
the static data and add some icons to the movie types.  Thanks to the 'fixture key',
it's easy to retrieve and update the already inserted data, just modify the 
update_fixtures function::

	def update_fixtures():
	  """Update static data in the database"""
	  from camelot.model.fixture import Fixture
	  from model import MovieType
	  Fixture.insertOrUpdateFixture(MovieType,
	                                fixture_key = 'comic',
	                                values = dict(name='Comic', icon='spiderman.png'))
	  Fixture.insertOrUpdateFixture(MovieType,
	                                fixture_key = 'scifi',
	                                values = dict(name='Science Fiction', icon='light_saber.png'))	  

The fixture version
-------------------

In case lots of data needs to be read into the database (like a list of 
postal codeds), it might make no sense to create a new fixture for each code,
instead a fixture version number can be set to indicate a list has been read
into the database.  The :class:`camelot.model.fixture.FixtureVersion` exists
to facilitate this.

.. literalinclude:: ../../../../test/test_model.py
   :start-after: begin load csv if fixture version
   :end-before: end  load csv if fixture version
