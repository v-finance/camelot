"""
Test the quality of the source code
"""

import os
import unittest

source_code = os.path.join( os.path.dirname( __file__ ) , '..', 'camelot' )

class SourceQualityCase( unittest.TestCase ):
    
    def test_deprecated( self ):
        # make sure no deprecated functions are used
        
        deprecated = [
            'setMargin',
            ]
        
        for (dirpath, _dirnames, filenames) in os.walk( source_code ):
            for filename in filenames:
                if os.path.splitext( filename )[-1] == '.py':
                    code = open( os.path.join( dirpath, filename ) ).read()
                    for expr in deprecated:
                        if expr in code:
                            raise Exception( '%s in %s/%s'%( expr, 
                                                             dirpath,
                                                             filename ) )
                    