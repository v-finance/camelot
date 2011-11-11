
from camelot.test import ModelThreadTestCase

class QueryProxyCase( ModelThreadTestCase ):
  """Test the functionality of the QueryProxy to perform CRUD operations on 
  stand alone data"""
  
  def setUp(self):
    super( QueryProxyCase, self ).setUp()
    from camelot.model.authentication import Person
    from camelot.view.proxy.queryproxy import QueryTableProxy
    from camelot.admin.application_admin import ApplicationAdmin
    self.app_admin = ApplicationAdmin()
    person_admin = self.app_admin.get_related_admin( Person )
    self.person_proxy = QueryTableProxy( person_admin, 
                                         query_getter = None, 
                                         columns_getter = person_admin.get_fields )
  
  def test_sort( self ):
    from camelot.model.authentication import Person
