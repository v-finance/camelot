from jinja import FileSystemLoader
from pkg_resources import resource_filename

import camelot.view

loader = FileSystemLoader(resource_filename(camelot.view.__name__, 'templates'))
