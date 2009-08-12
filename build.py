#!/usr/bin/env python
import runpy
import sys
import os
sys.argv += ['-style', 'cleanlooks']
sys.path.append( os.path.join(os.path.dirname(__file__), 'test') )
runpy.run_module('test.run', run_name='__main__')
del sys.argv[-2:]

import sphinx
sphinx.main(['sphinx-build', '-a', '-E', 'doc/sphinx/source', 'doc/sphinx/build',])

import sys
sys.argv += ['sdist', 'bdist_egg']
runpy.run_module('setup', run_name='__main__')
