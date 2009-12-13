#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from optparse import OptionParser

#
# Description of the application, out of which the help text as well as the
# __doc__ strings can be generated
#

description = """camelot_admin is a tool to assist in the creation and development of Camelot
projects.
"""

usage = "usage: %prog [options] command"

command_description = [
    ('startproject', """Starts a new project, use startproject project_name."""),
]

#
# Generate a docstring in restructured text format
#

__doc__ = description

for command, desc in command_description:
    __doc__ += "\n.. cmdoption:: %s\n\n"%command
    for line in desc.split('\n'):
        __doc__ += "    %s\n"%line
        
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
    
def startproject(project):
    import shutil, os, sys
    if os.path.exists(project):
        raise Exception('Directory %s allready exists, cannot start a project in it'%project)
    
    def ignore(directory, content):
        """ignore .svn files"""
        for c in content:
            if c.startswith('.'):
                yield c
                
    # ignore is only supported as of python 2.6
    v = sys.version_info
    if v[0]>2 or (v[0]==2 and v[1]>=6):
        shutil.copytree(os.path.join(os.path.dirname(__file__), '..', 'empty_project'), 
                        project, ignore=ignore)
    else:
        shutil.copytree(os.path.join(os.path.dirname(__file__), '..', 'empty_project'), 
                        project)    
    # creating a repository doesn't seems to work when migrate is easy intalled
    #from migrate.versioning.api import create
    #create(os.path.join(project, 'repository'), project)
      
commands = locals()

def main():
    import camelot
    parser = CommandOptionParser(description=description,
                                 usage=usage,
                                 version=camelot.__version__,)
    (_options, args) = parser.parse_args()
    if not len(args)==2:
        parser.print_help()
    else:
        command, _project = args 
        commands[command](*args[1:])
    
if __name__ == '__main__':
    main()
