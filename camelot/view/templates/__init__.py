from jinja import FileSystemLoader
from camelot.core.resources import resource_filename

import camelot.view

loader = FileSystemLoader(resource_filename(camelot.view.__name__, 'templates', 'CAMELOT_MAIN_DIRECTORY'))
