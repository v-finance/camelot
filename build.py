#!/usr/bin/env python
import runpy
runpy.run_module('test.run', run_name='__main__')

import sphinx
sphinx.main(['sphinx-build', '-a', 'doc/sphinx/source', 'doc/sphinx/build',])

import sys
sys.argv += ['sdist', 'bdist_egg']
runpy.run_module('setup', run_name='__main__')
