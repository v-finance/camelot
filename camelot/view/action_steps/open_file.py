#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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
from camelot.core.templates import environment

class OpenFile( ActionStep ):
    """
    Open a file with the preferred application from the user.  The absolute
    path is preferred, as this is most likely to work when running from an
    egg and in all kinds of setups.
    
    :param file_name: the absolute path to the file to open
    
    The :keyword:`yield` statement will return :keyword:`True` if the file was
    opend successfull.
    """
        
    def __init__( self, path ):
        self.path = path

    def get_path( self ):
        """
        :return: the path to the file that will be opened, use this method
        to verify the content of the file in unit tests
        """
        return self.path

    @classmethod
    def create_temporary_file( self, suffix ):
        """
        Create a temporary filename that can be used to write to, and open
        later on.
        
        :param suffix: the suffix of the file to create
        :return: the filename of the temporary file
        """
        import tempfile
        import os
        file_descriptor, file_name = tempfile.mkstemp( suffix=suffix )
        os.close( file_descriptor )
        return file_name
        
    def gui_run( self, gui_context ):
        #
        # support for windows shares
        #
        if not self.path.startswith(r'\\'):
            url = QtCore.QUrl.fromLocalFile( self.path )
        else:
            url = QtCore.QUrl( self.path, QtCore.QUrl.TolerantMode )
        return QtGui.QDesktopServices.openUrl( url )
    
class OpenStream( OpenFile ):
    """Write a stream to a temporary file and open that file with the 
    preferred application of the user.
    
    :param stream: the stream to write to a file
    :param suffix: the suffix of the temporary file
    """

    def __init__( self, stream, suffix='.txt' ):
        import os
        import tempfile
        file_descriptor, file_name = tempfile.mkstemp( suffix=suffix )
        output_stream = os.fdopen( file_descriptor, 'wb' )
        output_stream.write( stream.read() )
        output_stream.close()
        super( OpenStream, self ).__init__( file_name )

class OpenString( OpenFile ):
    """Write a string to a temporary file and open that file with the
    preferred application of the user.
        
    :param string: the string to write to a file
    :param suffix: the suffix of the temporary file
    """

    def __init__( self, string, suffix='.txt' ):
        import os
        import tempfile
        file_descriptor, file_name = tempfile.mkstemp( suffix=suffix )
        output_stream = os.fdopen( file_descriptor, 'wb' )
        output_stream.write( string )
        output_stream.close()
        super( OpenString, self ).__init__( file_name )
        
class OpenJinjaTemplate( OpenStream ):
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
    
    def __init__( self,
                  template, 
                  context={},
                  environment = environment,
                  suffix='.txt' ):
        from cStringIO import StringIO
        template = environment.get_template( template )
        template_stream = template.stream( context )
        output_stream = StringIO()
        template_stream.dump( output_stream, encoding='utf-8' )
        output_stream.seek( 0 )
        super( OpenJinjaTemplate, self).__init__( output_stream, suffix=suffix )

class WordJinjaTemplate( OpenFile ):
    """Render a jinja template into a temporary file and open that
    file with microsoft word through the use of COM objects.
    
    :param environment: a :class:`jinja2.Environment` object to be used
        to load templates from.
        
    :param template: the name of the template as it can be fetched from
        the Jinja environment.
    
    :param suffix: the suffix of the temporary file to create, this will
        determine the application used to open the file.
        
    :param context: a dictionary with objects to be used when rendering
        the template
    """
   
    def __init__( self,
                  template, 
                  context={},
                  environment = environment,
                  suffix='.xml' ):
        path = self.create_temporary_file( suffix )
        template = environment.get_template( template )
        template_stream = template.stream( context )
        template_stream.dump( open( path, 'wb' ), encoding='utf-8' )
        super( WordJinjaTemplate, self ).__init__( path )
        
    def gui_run( self, gui_context ):
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = True
            doc = word_app.Documents.Open( self.path )
            doc.Activate()
            word_app.Activate()
        # fallback in case of not on windows
        except ImportError:
            super( WordJinjaTemplate, self ).gui_run( gui_context )

