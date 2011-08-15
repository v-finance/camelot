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

from optparse import OptionParser
from code import InteractiveConsole
import sys

from camelot.core.conf import settings

#
# Description of the application, out of which the help text as well as the
# __doc__ strings can be generated
#

usage = "usage: %prog [options] command"

description = """
camelot_manage is oriented towards administrators of an installed
camelot application. It is used for interacting the database, the model
and migration of the database to a certain schema revision.

To use this application, PYTHONPATH should contain a valid settings.py file that
will be used to resolve the database engine and the model.
"""

command_description = [
    ('console', """Launches a python console with the model all setup for command line
interaction.

Within the example movie project one could do
the following to print a list of all movie titles to the screen::

    from model import Movie
    for movie in Movie.query.all():
    print movie.title
"""),
    ('db_version', """Get the version of the database schema from the current database"""),

    ('version', """Get the latest available database schema version"""),

    ('upgrade', """Upgrade or downgrade the database to the specified version, use upgrade version_number."""),

    ('version_control', """Put the database under version control"""),
   
    ('schema_display', """Generate a graph of the database schema.  The result is stored in schema.png.  This
option requires pydot to be installed."""),
]

#
# Generate a docstring in restructured text format
#

__doc__ = description

for command, desc in command_description:
    __doc__ += "\n.. cmdoption:: %s\n\n"%command
    for line in desc.split('\n'):
        __doc__ += "    %s\n"%line

__doc__ += """
   .. image:: /_static/schema.png
      :width: 400"""

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
        
For the creation and development of Camelot projects, see camelot_admin

"""
        return OptionParser.format_help(self) + ''.join(command_help)

class FileCacher:
    "Cache the stdout text so we can analyze it before returning it"
    def __init__(self): self.reset()
    def reset(self): self.out = []
    def write(self,line): self.out.append(line)
    def flush(self):
        output = '\n'.join(self.out)
        self.reset()
        return output
    
class Shell(InteractiveConsole):
    "Wrapper around Python that can filter input/output to the shell"
    def __init__(self, locals={}):
        self.stdout = sys.stdout
        self.cache = FileCacher()
        InteractiveConsole.__init__(self, locals)
        return
    def get_output(self): sys.stdout = self.cache
    def return_output(self): sys.stdout = self.stdout
    def push(self,line):
        line = line.replace('\r','')
        self.get_output()
        # you can filter input here by doing something like
        # line = filter(line)
        InteractiveConsole.push(self,line)
        self.return_output()
        output = self.cache.flush()
        # you can filter the output here by doing something like
        # output = filter(output)
        print output # or do something else with it
        return 
    
def schema_display(image_path='schema.png'):
    from camelot.core.schema_display import create_uml_graph
    from sqlalchemy import orm
    from elixir import entities
    mappers = [orm.class_mapper(e) for e in entities]
    graph = create_uml_graph(mappers,
        show_operations=False, # not necessary in this case
        show_multiplicity_one=False # some people like to see the ones, some don't
    )
    graph.write_png(image_path)
     
def setup_model():
    settings.setup_model()
     
def main():
    import camelot
    import logging
    logging.basicConfig(level=logging.INFO)
    #logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    parser = CommandOptionParser(usage=usage,
                                 description=description, 
                                 version=camelot.__version__)
    (_options, args) = parser.parse_args()
    if not args:
        parser.print_help()
    elif args[0]=='console':
        setup_model()
        sh = Shell()
        sh.interact()
    elif args[0]=='schema_display':
        setup_model()
        schema_display()
    elif args[0] in ('version_control', 'db_version', 'version', 'upgrade'):
        from migrate.versioning.repository import Repository
        from migrate.versioning.schema import ControlledSchema
        from migrate.versioning.exceptions import DatabaseNotControlledError
        from sqlalchemy.exc import NoSuchTableError
        migrate_engine = settings.ENGINE()
        repository = Repository(settings.REPOSITORY)
        schema = None
        try:
            schema = ControlledSchema(migrate_engine, repository)
        except (NoSuchTableError, DatabaseNotControlledError):
            print 'database not yet under version control, putting it under version_control first.'
        if args[0]=='version_control' or schema is None:
            migrate_connection = migrate_engine.connect()
            transaction = migrate_connection.begin()
            try:
                schema = ControlledSchema.create(migrate_engine, repository)
                transaction.commit()
            except:
                transaction.rollback()
                raise
            finally:
                migrate_connection.close()
            print 'database was put under version control'
        if schema:
            if args[0]=='db_version':
                print schema.version
            elif args[0]=='version':
                print repository.latest
            elif args[0]=='upgrade':
                migrate_connection = migrate_engine.connect()
                if len(args)>=2:
                    version = int(args[1])
                else:
                    version = repository.latest
                #
                # perform each upgrade step in a separate transaction, since
                # one upgrade might depend on an other being fully executed
                #
                try:
                    if schema.version == version:
                        print 'database is already at requested version'
                    if schema.version <= version:
                        step = 1
                    else:
                        step = -1
                    for i in range(schema.version+step, version+step, step):
                        transaction = migrate_connection.begin()
                        try:
                            schema.upgrade(i)
                            transaction.commit()
                            if step==1:
                                print 'upgrade %s'%i
                            else:
                                print 'downgrade %s'%i
                        except:
                            transaction.rollback()
                            raise
                finally:
                    migrate_connection.close()
    else:
        parser.print_help()
             
if __name__ == '__main__':
    main()


