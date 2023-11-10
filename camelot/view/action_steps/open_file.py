#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
from dataclasses import dataclass

from camelot.admin.action import ActionStep
from camelot.core.templates import environment
from camelot.view.qml_view import qml_action_step

from ...core.serializable import DataclassSerializable


@dataclass
class OpenFile( ActionStep, DataclassSerializable ):
    """
    Open a file with the preferred application from the user.  The absolute
    path is preferred, as this is most likely to work when running from an
    egg and in all kinds of setups.
    
    :param file_name: the absolute path to the file to open
    
    The :keyword:`yield` statement will return :const:`True` if the file was
    opend successfull.
    """

    path: str
    blocking: bool = False

    def __str__( self ):
        return u'Open file {}'.format( self.path )
    
    def get_path( self ):
        """
        :return: the path to the file that will be opened, use this method
        to verify the content of the file in unit tests
        """
        return self.path

    @classmethod
    def create_temporary_file( cls, suffix ):
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

    @classmethod
    def gui_run( cls, gui_context_name, serialized_step ):
        qml_action_step(gui_context_name, 'OpenFile', serialized_step)

class OpenStream( OpenFile ):
    """Write a stream to a temporary file and open that file with the 
    preferred application of the user.
    
    :param stream: the byte stream to write to a file
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
        
    :param string: the binary string to write to a file
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
        
    def gui_run( self, gui_context_name ):
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
            super( WordJinjaTemplate, self ).gui_run( gui_context_name )



