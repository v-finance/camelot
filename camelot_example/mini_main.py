"""
Run the example application with a reduced main window
"""

import main

def main():
    from camelot.view.main import main
    from camelot_example.application_admin import MiniApplicationAdmin
    main( MiniApplicationAdmin() )
    
if __name__ == '__main__':
    main()