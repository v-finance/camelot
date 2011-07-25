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
"""
Utility functions and classes to start a new Camelot project, this
could be the start of MetaCamelot
"""

import os

from camelot.core.conf import settings
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.application_action import ApplicationActionFromModelFunction
from camelot.view.controls import delegates

from camelot.view.main import Application

class MetaSettings(object):
    """settings target to be used within MetaCamelot, when no real
    settings are available yet"""

    CAMELOT_MEDIA_ROOT = '.'
    
    def ENGINE(self):
        return 'sqlite:///'
        
    def setup_model(self):
        pass
        
def launch_meta_camelot():
    settings.append( MetaSettings() )
    app = MetaCamelotApplication( MetaCamelotAdmin() )
    app.main()

class MetaCamelotAdmin( ApplicationAdmin ):
    """ApplicationAdmin class to be used within meta camelot"""
    
    name = 'Meta Camelot'
    
class MetaCamelotApplication( Application ):
    """A Camelot application to build new Camelot
    projects."""
    
    def initialization(self):
        new_project = CreateNewProject('New Camelot Project')
        new_project.run()

#
# The various features that can be set when creating a new Camelot project
#

features = [
   ('source',                '.',                                       delegates.PlainTextDelegate, '''The directory in which to create<br/>'''
                                                                                                     '''the sources of the new project '''),
   ('name',                  'My Application',                          delegates.PlainTextDelegate, '''The name of the application<br/>'''
                                                                                                     '''as it will appear in the main window and<br/>'''
                                                                                                     '''will be used to store settings in the<br/>'''
                                                                                                     '''registry.'''),
   ('author',                'My Company',                              delegates.PlainTextDelegate, '''The author of the application, this<br/>'''
                                                                                                     '''will be used to store settings in the<br/>'''
                                                                                                     '''registry.'''),
   ('module',                'myapplication',                           delegates.PlainTextDelegate, '''The name of the python module that<br/>'''
                                                                                                     '''will contain the application'''),
   ('domain',                'mydomain.com',                            delegates.PlainTextDelegate, '''The domain name of the author, this will<br/>'''
                                                                                                     '''be used to store settings in the registry'''),
   ('application_url',       'http://www.python-camelot.com',           delegates.PlainTextDelegate, '''Website of the application'''),
   ('help_url',              'http://www.python-camelot.com/docs.html', delegates.PlainTextDelegate, '''Part of the website with online help'''),
   ('default_models',        True,                                      delegates.BoolDelegate,      '''Use the default Camelot model for Organizations,<br/>'''
                                                                                                     '''Persons, etc.'''),
   #('integrate_cloudlaunch', False,                                     delegates.BoolDelegate,      '''Integrate updates, logging and online backups<br/>'''
                                                                                                     #'''This requires CloudLaunch to be installed<br/>'''
                                                                                                     #'''as well as credentials'''),
   #('shortcut',              True,                                      delegates.BoolDelegate,      '''Put a shortcut on the desktop to<br/>'''
                                                                                                     #'''start the application'''),
   #('author_email',          '',                                      delegates.PlainTextDelegate,   '''E-mail address of the author'''),                                 
]

#
# Templates of the files to create when starting a new project
#
 
templates = [
    ('application_admin.py', '''
from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section

class MyApplicationAdmin(ApplicationAdmin):
  
    def get_sections(self):
        from camelot.model.memento import Memento
        from camelot.model.authentication import Person, Organization
        from camelot.model.i18n import Translation
        return [Section('relation',
                        Icon('tango/22x22/apps/system-users.png'),
                        items = [Person, Organization]),
                Section('configuration',
                        Icon('tango/22x22/categories/preferences-system.png'),
                        items = [Memento, Translation])
                ]
    '''),
    
    ('__init__.py', ''),
    
    ('main.py', '''
import logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('main')

if __name__ == '__main__':
    from camelot.view.main import main
    from application_admin import MyApplicationAdmin
    main(MyApplicationAdmin())
    '''),
    
    ('model.py', '''
from camelot.model import metadata

__metadata__ = metadata
    '''),
    
    ('settings.py', '''
import logging
import os

logger = logging.getLogger('settings')

# media root needs to be an absolute path for the file open functions
# to function correctly
CAMELOT_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

# backup root is the directory where the default backups are stored
CAMELOT_BACKUP_ROOT = os.path.join(os.path.dirname(__file__), 'backup')

# default extension for backup files
CAMELOT_BACKUP_EXTENSION = 'db'

# template used to create and find default backups
CAMELOT_BACKUP_FILENAME_TEMPLATE = 'default-backup-%(text)s.' + CAMELOT_BACKUP_EXTENSION


def ENGINE():
    """This function should return a connection to the database"""
    from sqlalchemy import create_engine
    return create_engine('sqlite:///model-data.sqlite')

def setup_model():
    """This function will be called at application startup, it is used to setup
    the model"""
    import camelot.model
    from elixir import setup_all
    import model
    setup_all(create_tables=True)
    from camelot.model.authentication import updateLastLogin
    updateLastLogin()
    '''),
]
class CreateNewProject( ApplicationActionFromModelFunction ):
    """Action to create a new project, based on a form with
    options the user fills in."""
    
    class Options(object):
        
        def __init__(self):
            for feature in features:
                setattr( self, feature[0], feature[1] )           

        class Admin( ObjectAdmin ):
            form_display = [feature[0] for feature in features]
            field_attributes = dict(
                ( feature[0],{ 'editable':True,
                               'delegate':feature[2],
                               'tooltip':feature[3]   } ) for feature in features)
            
    def model_run(self, options):
        os.makedirs( os.path.join( options.source, options.module ) )
        for filename, template in templates:
            fp = open( os.path.join( options.source, options.module, filename ), 
                       'w' )
            fp.write( template )
            fp.close()
