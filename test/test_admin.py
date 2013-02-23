"""
Tests for the Admin classes
"""

from camelot.admin.application_admin import ApplicationAdmin
from camelot.test import ModelThreadTestCase

from PyQt4.QtCore import Qt

class ApplicationAdminCase( ModelThreadTestCase ):
    
    def test_application_admin( self ):
        app_admin = ApplicationAdmin()
        self.assertTrue( app_admin.get_sections() )
        self.assertTrue( app_admin.create_main_window() )
        self.assertTrue( app_admin.get_related_toolbar_actions( Qt.RightToolBarArea, 'onetomany' ) )
        self.assertTrue( app_admin.get_related_toolbar_actions( Qt.RightToolBarArea, 'manytomany' ) )
        self.assertTrue( app_admin.get_version() )
        self.assertTrue( app_admin.get_icon() )
        self.assertTrue( app_admin.get_splashscreen() )
        self.assertTrue( app_admin.get_organization_name() )
        self.assertTrue( app_admin.get_organization_domain() )
        self.assertTrue( app_admin.get_stylesheet() )
        self.assertTrue( app_admin.get_about() )
        self.assertTrue( app_admin.get_versions() )
        
    def test_admin_for_exising_database( self ):
        from .snippet.existing_database import app_admin
        self.assertTrue( app_admin.get_sections() )
        
class ObjectAdminCase( ModelThreadTestCase ):
    """Test the ObjectAdmin
    """

    def setUp(self):
        super( ObjectAdminCase, self ).setUp()
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
