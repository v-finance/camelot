"""
Tests for the Admin classes
"""

from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.entity_admin import EntityAdmin
from camelot.test import ModelThreadTestCase
from camelot.view.controls import delegates

from PyQt4.QtCore import Qt

from sqlalchemy import schema, types

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
        
class EntityAdminCase( ModelThreadTestCase ):
    """Test the EntityAdmin
    """

    def setUp( self ):
        super( EntityAdminCase, self ).setUp()
        self.app_admin = ApplicationAdmin()
        
    def test_sql_field_attributes( self ):
        #
        # test a generic SQLA field type
        #
        column_1 =  schema.Column( types.Unicode(), nullable = False )
        fa_1 = EntityAdmin.get_sql_field_attributes( [column_1] )
        self.assertTrue( fa_1['editable'] )
        self.assertFalse( fa_1['nullable'] )
        self.assertEqual( fa_1['delegate'], delegates.PlainTextDelegate )
        #
        # test sql standard types
        #
        column_2 =  schema.Column( types.FLOAT(), nullable = True )
        fa_2 = EntityAdmin.get_sql_field_attributes( [column_2] )
        self.assertTrue( fa_2['editable'] )
        self.assertTrue( fa_2['nullable'] )
        self.assertEqual( fa_2['delegate'], delegates.FloatDelegate )
        #
        # test a vendor specific field type
        #
        from sqlalchemy.dialects import mysql
        column_3 = schema.Column( mysql.BIGINT(), default = 2 )
        fa_3 = EntityAdmin.get_sql_field_attributes( [column_3] )
        self.assertTrue( fa_3['default'] )
        self.assertEqual( fa_3['delegate'], delegates.IntegerDelegate )
