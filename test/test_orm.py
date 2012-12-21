from sqlalchemy import orm

from camelot.test import ModelThreadTestCase

class OrmCase( ModelThreadTestCase ):
    """Test the Declarative base classes"""
  
    def setUp(self):
        super( OrmCase, self ).setUp()
        from camelot.core.conf import settings
        from camelot.model import metadata
        metadata.create_all()
        self.session = orm.sessionmaker( bind = metadata.bind )()
  
    def test_batch_job( self ):
        from camelot.model.batch_job import BatchJob, BatchJobType
        from sqlalchemy.orm.attributes import InstrumentedAttribute
        #
        # are the relationship properties there
        #
        type_id_property = BatchJob.type_id
        self.assertTrue( isinstance( type_id_property, InstrumentedAttribute ) )
        type_property = BatchJob.type
        self.assertTrue( isinstance( type_property, InstrumentedAttribute ) )
        #
        # see if the queries work
        #
        type_mapper = orm.class_mapper( BatchJobType )
        type_query = self.session.query( BatchJobType )
        job_mapper = orm.class_mapper( BatchJob )
        job_query = self.session.query( BatchJob )
