
from camelot.test import ModelThreadTestCase

class ModelCase( ModelThreadTestCase ):
  """Test the build in camelot model"""
  
  def setUp(self):
    super( ModelCase, self ).setUp()
    from camelot.model.authentication import Person
    from camelot.view.proxy.queryproxy import QueryTableProxy
    from camelot.admin.application_admin import ApplicationAdmin
    self.app_admin = ApplicationAdmin()
    self.person_admin = self.app_admin.get_related_admin( Person )
  
  def test_person_contact_mechanism( self ):
    from camelot.model.authentication import Person
    person = Person( first_name = u'Robin',
                     last_name = u'The brave' )
    self.assertEqual( person.contact_mechanisms_email, None )
    mechanism = ('email', 'robin@test.org')
    person.contact_mechanisms_email = mechanism
    self.person_admin.flush( person )
    self.assertEqual( person.contact_mechanisms_email, mechanism )
    self.person_admin.delete( person )
    person = Person( first_name = u'Robin',
                     last_name = u'The brave' )
    self.person_admin.flush( person )
    self.assertEqual( person.contact_mechanisms_email[1], u'' )
    