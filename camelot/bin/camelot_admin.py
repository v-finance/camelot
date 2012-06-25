#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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

import logging
from optparse import OptionParser

logging.basicConfig( level = logging.INFO )
LOGGER = logging.getLogger( 'camelot.bin.camelot_admin' )

#
# Description of the application, out of which the help text as well as the
# __doc__ strings can be generated
#

description = """camelot_admin is a tool to assist in the creation and development of Camelot
projects.  Use this application without any options to start a GUI to create
a new Camelot project.
"""

usage = "usage: %prog [options] command"

command_description = [
    ('startproject', """Starts a new project, use startproject project_name.
"""),
    ('makemessages', """Outputs a message file with all field names of all 
entities.  This command requires settings.py of the project to be in the 
PYTHONPATH"""),
    ('apidoc', """Extract API documentation from source code, to be used
with sphinx.
"""),
    ('license_update', """Change the license header of a project,
use license_update project_directory license_file"""),
    ('to_pyside', """Takes a folder with PyQt4 source code and translates it to
PySide source code.  Usage ::
   
   to_pyside source destination"""),
]

#
# Generate a docstring in restructured text format
#

__doc__ = description

for command, desc in command_description:
    __doc__ += "\n.. cmdoption:: %s\n\n" % command
    for line in desc.split('\n'):
        __doc__ += "    %s\n" % line
        
#
# A custom OptionParser that generates help information on the commands
#
class CommandOptionParser(OptionParser):
    
    def format_help(self, formatter=None):
        command_help = """
The available commands are :

"""
        command_help += '\n\n'.join(['%s\n%s\n%s'%(command,'-'*len(command), desc) for command,desc in command_description])
        command_help += """
        
For the management of deployed Camelot applications, see camelot_manage

"""
        return OptionParser.format_help(self) + ''.join(command_help)
    
def apidoc(source, destination):

    import os
   
    def is_module_directory( dirname ):
        """:return: True if the directory is a python module, False otherwise"""
        if not os.path.isdir( dirname ):
            return False
        if os.path.basename( dirname ).startswith( '.' ):
            return False
        return os.path.exists( os.path.join( dirname, '__init__.py' ) ) 

    def document_directory(_arg, dirname, names):
        """create .rst files for a directory of source files"""
        if is_module_directory( dirname ):
            targetdir = os.path.join( destination, dirname[len(source)+1:] )
            if not os.path.exists( targetdir ):
                os.makedirs( targetdir )
            srcs = [n for n in names if n.endswith('.py') and not n.startswith('__')]
            dirs = [n for n in names if is_module_directory( os.path.join( dirname, n ) )]
            title = os.path.basename( dirname )
            if dirname == source:
                title = '%s API'%(dirname.capitalize())
            ifn = os.path.join( targetdir, 'index.rst' )
            module_name = dirname.replace('/', '.')
            with open( ifn, 'w' ) as index:
               lines = [ '=' * len(title),
                         title,
                         '=' * len(title),
                         '',
                         '',
                         '.. automodule:: %s'%module_name,
                         '   :members:'
               ]
               toclines = []
               for sn in srcs:
                  sname = sn[:-3]
                  sfn = sname + '.rst'
                  toclines.append( '   %s'%sfn )
                  with open( os.path.join( targetdir, sfn ), 'w' ) as sf:
                      slines  = ['-' * len(sname),
                                 sname,
                                 '-' * len(sname),
                                 '',
                                 '', 
                                 '.. automodule:: %s'%(module_name + '.' + sname),
                                 '   :members:', ]
                      sf.writelines( '%s\n'%line for line in slines )
               toclines.extend( '   %s/index.rst'%dn for dn in dirs )
               if toclines:
                   toclines.sort()
                   lines.extend( ['',
                                  '.. toctree::',
                                  ''] )
                   lines.extend( toclines )
               index.writelines( '%s\n'%line for line in lines )
                    
            LOGGER.info( '%s : %s -> %s'%(dirname, destination, targetdir) )
        
    os.path.walk(source, document_directory, None)
    
def license_update(project, license_file):

    import os
    
    new_license = open(license_file).read()

    def translate_file(dirname, name):
        """translate a single file"""
        filename = os.path.join(dirname, name)
        LOGGER.info( 'converting %s'%filename )
        source = open(filename).read()
        output = open(filename, 'w')
        output.write(new_license)
        old_license_line = True
        for line in source.split('\n'):
            if not len(line) or line[0]!='#':
                old_license_line = False
            if not old_license_line:
                output.write(line)
                output.write('\n')
        
    def translate_directory(_arg, dirname, names):
        """recursively translate a directory"""
        for name in names:
            if name.endswith('.py'):
                translate_file(dirname, name)
            
    os.path.walk(project, translate_directory, None)
    
def to_pyside( source, destination ):
    import os.path
    import shutil
    # first take a copy
    if os.path.exists( destination ):
        shutil.rmtree( destination )
    shutil.copytree( source, destination )
   
    def replace_word(original_str, old_word, new_word):
        return new_word.join((t for t in original_str.split(old_word)))

    def translate_file( dirname, name ):
        """translate a single file"""
        filename = os.path.join(dirname, name)
        LOGGER.info( 'converting %s'%filename )
        source = open(filename).read()
        output = open(filename, 'w')
        source = replace_word( source, 'PyQt4', 'PySide' )
        source = replace_word( source, 'pyqtSlot', 'Slot' )
        source = replace_word( source, 'pyqtSignal', 'Signal' )
        source = replace_word( source, 'pyqtProperty', 'Property' )
        source = replace_word( source, 'QtCore.QString', 'str' )
        source = replace_word( source, 'QtCore.QVariant.', 'QtCore.Q')
        source = replace_word( source, 'QtCore.QVariant(', '(' )
        source = replace_word( source, 'QVariant', '()' )
        source = replace_word( source, '.toByteArray()', '' )
        source = replace_word( source, '.toString()', '' )
        source = replace_word( source, '.toBool()', '' )
        source = replace_word( source, '.toSize()', '' )
        source = replace_word( source, '.toLongLong()', ', True' )
        source = replace_word( source, ').isValid()', ')' )
        output.write( source )
        
    def translate_directory( dirname, names ):
        """recursively translate a directory"""
        for name in names:
            if name.endswith('.py'):
                translate_file(dirname, name)
            
    for ( dirpath, _dirnames, filenames ) in os.walk( destination ):
        translate_directory( dirpath, filenames )
    
    
def startproject(module):
    import os
    from camelot.bin.meta import CreateNewProject, NewProjectOptions
    if os.path.exists(module):
        raise Exception('Directory %s already exists, cannot start a project in it'%module)
    
    options = NewProjectOptions()
    options.module = module
    
    action = CreateNewProject()
    action.start_project( options )

def makemessages():
    from camelot.core.conf import settings
    LOGGER.error( 'Not yet implemented' )
    settings.setup_model()
    
def meta():
    """launch meta camelot, in a separate function to make sure camelot_admin
    does not depend on PyQt, otherwise it is imposible to run to_pyside without
    having PyQt installed"""
    from camelot.bin.meta import launch_meta_camelot
    launch_meta_camelot()
    
commands = locals()

def main():
    import camelot    
    parser = CommandOptionParser( description = description,
                                  usage = usage,
                                  version = camelot.__version__, )
    ( _options, args ) = parser.parse_args()
    if not len( args ):
        meta()
    elif not len( args )>=2:
        parser.print_help()
    else:
        command, command_args = args[0], args[1:] 
        commands[command]( *command_args )

if __name__ == '__main__':
    main()

