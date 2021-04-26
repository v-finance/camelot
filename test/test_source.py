"""
Test the quality of the source code
"""

import os
import unittest

source_code = os.path.join( os.path.dirname( __file__ ) , '..', 'camelot' )

class SourceQualityCase( unittest.TestCase ):
    
    def walk_source_files(self):
        for (dirpath, _dirnames, filenames) in os.walk( source_code ):
            for filename in filenames:
                if os.path.splitext( filename )[-1] == '.py':
                    yield dirpath, filename

    def test_deprecated(self):
        # make sure no deprecated functions are used
        deprecated = [
            'setMargin',
            ]

        for dirpath, filename in self.walk_source_files():
            code = open( os.path.join( dirpath, filename ) ).read()
            for expr in deprecated:
                if expr in code:
                    raise Exception( '%s in %s/%s'%( expr, 
                                                     dirpath,
                                                     filename ) )

    def test_qt_incompatible(self):
        # test for the use of constructs that should be handled through
        # the qt compatibility module
        qt_incompatible = [
            'QVariant',
            'toBool',
            'toString()',
            'toSize()',
            'PyQt4',
            'pyqtSlot',
            'pyqtSignal',
            'pyqtProperty',
            'toByteArray',
            'toLongLong',
        ]

        for dirpath, filename in self.walk_source_files():
            code = open( os.path.join( dirpath, filename ) ).read()
            if filename=='qt.py':
                continue
            for expr in qt_incompatible:
                if expr in code:
                    raise Exception( '%s in %s/%s'%( expr, 
                                                     dirpath,
                                                     filename ) )

    def test_py3k( self ):
        # run the 2to3 tool, to see if nothing remains unconverted
        from lib2to3.main import main
        main('lib2to3.fixes', [source_code, '-x', 'unicode'])
