#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui, QtCore
  
from camelot.admin.action import ActionStep

class OpenFile( ActionStep ):
    
    def __init__( self, path ):
        """
        Open a file with the preferred application from the user.  The absolute
        path is preferred, as this is most likely to work when running from an
        egg and in all kinds of setups.
        
        :param path: the absolute path to the file to open
        """
        self._path = path

    def gui_run( self, gui_context ):
        #
        # support for windows shares
        #
        if not self._path.startswith(r'\\'):
            url = QtCore.QUrl.fromLocalFile( self._path )
        else:
            url = QtCore.QUrl( self._path, QtCore.QUrl.TolerantMode )
        QtGui.QDesktopServices.openUrl( url )
    
class OpenStream( OpenFile ):

    def __init__( self, stream, suffix='.txt' ):
        """Write a stream to a temporary file and open that file with the 
        preferred application of the user.
        
        :param stream: the stream to write to a file
        :param suffix: the suffix of the temporary file
        """
        import os
        import tempfile
        file_descriptor, file_name = tempfile.mkstemp( suffix=suffix )
        output_stream = os.fdopen( file_descriptor, 'wb' )
        output_stream.writelines( stream )
        output_stream.close()
        super( OpenStream, self ).__init__( file_name )

class OpenJinjaTemplate( OpenFile ):
    
    def __init__( self,
                  environment,
                  template, 
                  suffix='.txt', 
                  context={}, ):
        """Render a jinja template into a temporary file and open that
        file with the prefered application of the user.
        
        :param environment: a :class:`jinja2.Environment` object to be used
            to load templates from.
            
        :param template: the name of the template as it can be fetched from
            the Jinja environment.
        
        :param suffix: the suffix of the temporary file to create, this will
            determine the application used to open the file.
            
        :param context: a dictionary with objects to be used when rendering
            the template
        """
        template = environment.get_template( template )
        stream = template.render( context )        
        super( OpenJinjaTemplate, self).__init__( stream, suffix=suffix )
