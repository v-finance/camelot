#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
  name = 'Camelot',
  version = '04.09',
  description = 'A python GUI framework on top of  Sqlalchemy  and PyQt, inspired by the Django admin interface. Start building desktop applications at warp speed, simply by adding some additional information to you model definition.',
  author = 'Conceptive Engineering',
  author_email = 'project-camelot@conceptive.be',
  url = 'http://www.conceptive.be/projects/camelot/',
  include_package_data = True,
  license = 'GPL, Commercial',
  platform = 'Linux, Windows, OS X',
  install_requires = ['SQLAlchemy==0.4.7', 
                      'Elixir>=0.6.1', 
                      'sqlalchemy-migrate>=0.5.3',
                      'pyExcelerator>=0.6.4a',
                      'Jinja>=1.2',
                      'PIL>=1.1.6', ],
  packages = find_packages() )

