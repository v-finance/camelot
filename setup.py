#!/usr/bin/env python
import os
import camelot
from setuptools import setup, find_packages

README = os.path.join(os.path.dirname(__file__), 'readme.txt')
long_description = open(README).read() + '\n\n'

setup(
  name = 'Camelot',
  version = camelot.__version__,
  description = 'A python GUI framework on top of  Sqlalchemy  and PyQt, inspired by the Django admin interface. Start building desktop applications at warp speed, simply by adding some additional information to you model definition.',
  long_description = long_description,
  keywords = 'qt pyqt sqlalchemy elixir desktop gui framework',
  author = 'Conceptive Engineering',
  author_email = 'project-camelot@conceptive.be',
  url = 'http://www.conceptive.be/projects/camelot/',
  include_package_data = True,
  license = 'GPL, Commercial',
  platforms = 'Linux, Windows, OS X',
  install_requires = ['SQLAlchemy==0.5.6',
                      'Elixir>=0.6.1',
                      'sqlalchemy-migrate>=0.5.3',
                      'pyExcelerator>=0.6.4a',
                      'Jinja>=1.2',
                      'chardet>=1.0.1', 
                      'Babel>=0.9.4' ],
  entry_points = {'console_scripts':[
                   'camelot_admin = camelot.bin.camelot_admin:main',
                   'camelot_manage = camelot.bin.camelot_manage:main',
                  ]
                  },
  packages = find_packages() )

