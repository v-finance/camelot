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

"""
Tool to assist in the management of Camelot projects.

version_control

Puts the database under version control

eg : python manage.py console
launches a python console with the model being set up

"""

from code import InteractiveConsole
import sys

import settings

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
      
def main():
    from optparse import OptionParser
    import camelot
    parser = OptionParser(__doc__, version=camelot.__version__)
    (_options, args) = parser.parse_args()
    if not args:
        parser.print_help()
    elif args[0]=='console':
        settings.setup_model()
        sh = Shell()
        sh.interact()
    elif args[0]=='schema_display':
        settings.setup_model()
        schema_display()
    elif args[0] in ('version_control', 'db_version', 'version', 'upgrade'):
        from migrate.versioning.repository import Repository
        from migrate.versioning.schema import ControlledSchema
        from sqlalchemy.exceptions import NoSuchTableError
        migrate_engine = settings.ENGINE()
        repository = Repository(settings.REPOSITORY)
        schema = None
        if args[0]=='version_control':
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
        try:
            schema = ControlledSchema(migrate_engine, repository)
        except NoSuchTableError, _e:
            print 'database not yet under version control, use the version_control command first.'
        if schema:
            if args[0]=='db_version':
                print schema.version
            elif args[0]=='version':
                print repository.latest
            elif args[0]=='upgrade':
                migrate_connection = migrate_engine.connect()
                transaction = migrate_connection.begin()
                try:
                    schema.upgrade(args[1])
                    transaction.commit()
                    print schema.version
                except:
                    transaction.rollback()
                    raise
                finally:
                    migrate_connection.close()
    else:
        parser.print_help()          
             
if __name__ == '__main__':
    main()
