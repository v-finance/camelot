"""
Run the example application with a reduced main window
"""

from camelot.core.conf import settings
from .main import example_settings

def main():
    from camelot.view.main import main
    from camelot_example.application_admin import MiniApplicationAdmin
    settings.append(example_settings)
    main( MiniApplicationAdmin() )
    
if __name__ == '__main__':
    main()
