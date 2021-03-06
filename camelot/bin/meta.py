#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
"""
Utility functions and classes to start a new Camelot project, this
could be the start of MetaCamelot
"""

import os
import logging

from ..core.qt import QtWidgets
from ..core.utils import ugettext_lazy as _
from ..admin.application_admin import ApplicationAdmin
from ..admin.object_admin import ObjectAdmin
from ..admin.action import Action
from ..view.controls import delegates
from ..view.main import main_action

LOGGER = logging.getLogger( 'camelot.bin.meta' )

class MetaCamelotAdmin( ApplicationAdmin ):
    """ApplicationAdmin class to be used within meta camelot"""
    
    name = 'Meta Camelot'

def launch_meta_camelot():
    action = CreateNewProject()
    main_action(action)

#
# The various features that can be set when creating a new Camelot project
#

features = [
   ('source',                '.',                                       delegates.LocalFileDelegate, '''The directory in which to create<br/>'''
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
   ('application_url',       'http://www.python-camelot.com',           delegates.PlainTextDelegate, '''Url of the application, this url should be<br/>'''
                                                                                                     '''unique for the application, as it will be used<br/>'''
                                                                                                     '''to uniquely identify the application in Windows'''),
   ('help_url',              'http://www.python-camelot.com/docs.html', delegates.PlainTextDelegate, '''Part of the website with online help'''),
   ('installer',             False,                                     delegates.BoolDelegate,      '''Build a windows installer'''),
]

#
# Templates of the files to create when starting a new project
#
 
templates = [
    ('{{options.module}}/application_admin.py', '''
from camelot.view.art import Icon
from camelot.admin.application_admin import ApplicationAdmin
from camelot.admin.section import Section
from camelot.core.utils import ugettext_lazy as _

class MyApplicationAdmin(ApplicationAdmin):
  
    name = '{{options.name}}'
    application_url = '{{options.application_url}}'
    help_url = '{{options.help_url}}'
    author = '{{options.author}}'
    domain = '{{options.domain}}'
    
    def get_sections(self):
        from camelot.model.memento import Memento
        from camelot.model.i18n import Translation
        return [ Section( _('My classes'),
                          self,
                          Icon('tango/22x22/apps/system-users.png'),
                          items = [] ),
                 Section( _('Configuration'),
                          self,
                          Icon('tango/22x22/categories/preferences-system.png'),
                          items = [Memento, Translation] )
                ]
    '''),
    
    ('__init__.py', ''),
    
    ('{{options.module}}/__init__.py', ''),

    ('{{options.module}}/test.py', '''
#
# Default unittests for a camelot application.  These unittests will create
# screenshots of all the views in the application.  Run them with this command :
#
# python -m nose.core -v -s {{options.module}}/test.py
#

import os

from camelot.test import EntityViewsTest

# screenshots will be put in this directory
static_images_path = os.path.join( os.path.dirname( __file__ ), 'images' )

class MyApplicationViewsTest( EntityViewsTest ):

    images_path = static_images_path
    '''),
    
    ('main.py', '''
import logging
from camelot.core.conf import settings, SimpleSettings

logging.basicConfig( level = logging.ERROR )
logger = logging.getLogger( 'main' )

# begin custom settings
class MySettings( SimpleSettings ):

    # add an ENGINE or a CAMELOT_MEDIA_ROOT method here to connect
    # to another database or change the location where files are stored
    #
    # def ENGINE( self ):
    #     from sqlalchemy import create_engine
    #     return create_engine( 'postgresql://user:passwd@127.0.0.1/database' )
    
    def setup_model( self ):
        """This function will be called at application startup, it is used to 
        setup the model"""
        from camelot.core.sql import metadata
        from camelot.core.orm import setup_all
        metadata.bind = self.ENGINE()
        import camelot.model.authentication
        import camelot.model.i18n
        import camelot.model.memento
        import {{options.module}}.model
        setup_all()
        metadata.create_all()

my_settings = MySettings( '{{options.author}}', '{{options.name}}' ) 
settings.append( my_settings )
# end custom settings

def start_application():
    from camelot.admin.action.application import Application
    from camelot.view.main import main_action
    from {{options.module}}.application_admin import MyApplicationAdmin
    application = Application(MyApplicationAdmin())
    main_action(application)

if __name__ == '__main__':
    start_application()
    '''),
    
    ('{{options.module}}/model.py', '''
from sqlalchemy.schema import Column
import sqlalchemy.types
    
from camelot.admin.entity_admin import EntityAdmin
from camelot.core.orm import Entity
import camelot.types
    '''),
    
    ('excludes.txt', r'''
vtk*
sphinx*

Lib\site-packages\cvxopt*
Lib\site-packages\IPython*
Lib\site-packages\logilab*
Lib\site-packages\nose*
Lib\site-packages\PIL*
Lib\site-packages\py2exe*
Lib\site-packages\pyflakes*
Lib\site-packages\pylint*
Lib\site-packages\pytz\zoneinfo\*
Lib\site-packages\rope*
Lib\site-packages\Sphinx*
Lib\site-packages\spyder*
Lib\site-packages\virtualenv*
Lib\site-packages\VTK*
Lib\site-packages\docutils*
Lib\site-packages\pyreadline*
Lib\site-packages\Bio*
Lib\site-packages\vitables*
Lib\site-packages\sympy*
Lib\site-packages\Cython*
Lib\site-packages\sympy*
Lib\site-packages\PyOpenGL*
Lib\site-packages\tables*
Lib\site-packages\zmq*

include
license
libs   
    '''),
    ('setup.py', '''
#
# Default setup file for a Camelot application
#
# To build a windows installer, execute this file with :
#
#     python setup.py egg_info bdist_cloud wininst_cloud
#
# Running from the Python SDK command line
#

import datetime
import logging

from setuptools import setup, find_packages

logging.basicConfig( level=logging.INFO )

setup(
    name = '{{options.name}}',
    version = '1.0',
    author = '{{options.author}}',
    url = '{{options.application_url}}',
    include_package_data = True,
    packages = find_packages(),
    py_modules = ['settings', 'main'],
    entry_points = {'gui_scripts':[
                     'main = main:start_application',
                    ],},
    options = {
        'bdist_cloud':{'revision':'0',
                       'branch':'master',
                       'uuid':'{{uuid}}',
                       'update_before_launch':False,
                       'default_entry_point':('gui_scripts','main'),
                       'changes':[],
                       'timestamp':datetime.datetime.now(),
                       },
        'wininst_cloud':{ 'excludes':'excludes.txt',
                          'uuid':'{{uuid}}', },
    }, 

  )

    '''),
]

class NewProjectOptions(object):
    
    def __init__(self):
        for feature in features:
            setattr( self, feature[0], feature[1] )       

    class Admin( ObjectAdmin ):
        verbose_name = _('New project')
        form_display = [feature[0] for feature in features]
        field_attributes = dict(
            ( feature[0],{ 'editable':True,
                           'delegate':feature[2],
                           'nullable':False,
                           'tooltip':feature[3]   } ) for feature in features)
        field_attributes['source']['directory'] = True
            
class CreateNewProject( Action ):
    """Action to create a new project, based on a form with
    options the user fills in."""
            
    def model_run(self, model_context):
        # begin change object
        from camelot.view import action_steps
        app_admin = MetaCamelotAdmin()
        options = NewProjectOptions()
        yield action_steps.UpdateProgress( text = 'Request information' )
        yield action_steps.ChangeObject( options, app_admin.get_related_admin(NewProjectOptions) )
        # end change object
        yield action_steps.UpdateProgress( text = 'Creating new project' )
        self.start_project( options )
        project_path = os.path.abspath( options.source )
        if options.installer:
            cloudlaunch_found = False
            try:
                import cloudlaunch
                cloudlaunch_found = True
            except Exception:
                yield action_steps.MessageBox( 'To build a Windows installer, you need to be using<br/>' \
                                               'the Conceptive Python SDK, please visit<br/>' \
                                               '<a href="http://www.conceptive.be/python-sdk.html">www.conceptive.be/python-sdk.html</a><br/>' \
                                               'for more information' )
            if cloudlaunch_found:
                LOGGER.debug( '%s imported'%( cloudlaunch.__name__ ) )
                yield action_steps.UpdateProgress( text = 'Building windows installer' )
                import distutils.core
                current_dir = os.getcwd()
                # change to the app directory for setuptools to do its job
                os.chdir( project_path )
                setup_path = os.path.join( 'setup.py' )
                distribution = distutils.core.run_setup( setup_path, 
                                                         script_args = ['egg_info', 'bdist_cloud', 'wininst_cloud'] )
                os.chdir( current_dir )
                for command, _python_version, filename in  distribution.dist_files:
                    if command == 'wininst_cloud':
                        yield action_steps.MessageBox( 'Use Inno Setup to process the file<br/>' \
                                                       '<b>%s</b><br/> to build the installer executable'% os.path.join( project_path, filename ),
                                                       standard_buttons = QtWidgets.QMessageBox.Ok )

        yield action_steps.MessageBox( 'All files for the new project<br/>' \
                                       'were created in <b>%s</b>'%project_path,
                                       standard_buttons = QtWidgets.QMessageBox.Ok )
        yield action_steps.OpenFile( project_path )
        
    def start_project( self, options ):
        from jinja2 import Template
        import uuid
        context = {'options':options, 'uuid':str(uuid.uuid4())}
        if not os.path.exists( os.path.join( options.source, options.module ) ):
            os.makedirs( os.path.join( options.source, options.module ) )
        for filename_template, code_template in templates:
            filename = Template( filename_template ).render( context )
            code = Template( code_template ).render( context )            
            fp = open( os.path.join( options.source, filename ), 
                       'w' )
            fp.write( code )
            fp.close()


