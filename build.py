#!/usr/bin/env python
import runpy
import sys
import os
sys.argv += ['-style', 'cleanlooks']
sys.path.append( os.path.join(os.path.dirname(__file__), 'test') )
sys.path.append( os.path.dirname(__file__) )
from nose.core import main
main(argv=['build.py', '-v', '-s', '-P', 'test'], exit=False)
del sys.argv[-2:]

import sphinx
sphinx.main(['sphinx-build', '-a', '-E', 'doc/sphinx/source', 'doc/sphinx/build',])

import sys
sys.argv += ['sdist', 'bdist_egg']
runpy.run_module('setup', run_name='__main__')
