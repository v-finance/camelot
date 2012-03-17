"""
Tests for the Admin classes
"""

from camelot.test import ModelThreadTestCase

class ObjectAdminCase( ModelThreadTestCase ):
    """Test the ObjectAdmin
    """

    def setUp(self):
        super( ObjectAdminCase, self ).setUp()
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        
    def test_not_editable_admin_class_decorator( self ):
        from camelot.model.i18n import Translation
        from camelot.admin.not_editable_admin import not_editable_admin
        
        OriginalAdmin = Translation.Admin
        original_admin = OriginalAdmin( self.app_admin, Translation )
        self.assertTrue( len( original_admin.get_list_actions() ) )
        self.assertTrue( original_admin.get_field_attributes( 'value' )['editable'] )
        
        #
        # enable the actions
        #
        NewAdmin = not_editable_admin( Translation.Admin, 
                                       actions = True )
        new_admin = NewAdmin( self.app_admin, Translation )
        self.assertTrue( len( new_admin.get_list_actions() ) )
        self.assertFalse( new_admin.get_field_attributes( 'value' )['editable'] )
        self.assertFalse( new_admin.get_field_attributes( 'source' )['editable'] )
        
        #
        # disable the actions
        #
        NewAdmin = not_editable_admin( Translation.Admin, 
                                       actions = False )
        new_admin = NewAdmin( self.app_admin, Translation )
        self.assertFalse( len( new_admin.get_list_actions() ) )
        self.assertFalse( new_admin.get_field_attributes( 'value' )['editable'] )
        self.assertFalse( new_admin.get_field_attributes( 'source' )['editable'] )

        #
        # keep the value field editalbe
        #
        NewAdmin = not_editable_admin( Translation.Admin, 
                                       editable_fields = ['value'] )
        new_admin = NewAdmin( self.app_admin, Translation )
        self.assertFalse( len( new_admin.get_list_actions() ) )
        self.assertTrue( new_admin.get_field_attributes( 'value' )['editable'] )
        self.assertFalse( new_admin.get_field_attributes( 'source' )['editable'] )
