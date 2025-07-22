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
import base64
from dataclasses import dataclass
import os

from dataclasses import field, InitVar

from camelot.admin.action import ActionStep

from ...core.serializable import DataclassSerializable

@dataclass
class OpenFile( ActionStep, DataclassSerializable ):
    """
    Open a file with the preferred application from the user.  The absolute
    path is preferred, as this is most likely to work when running from an
    egg and in all kinds of setups.
    
    :param file_name: the absolute path to the file to open
    
    The :keyword:`yield` statement will return :const:`True` if the file was
    opened successfully.
    """

    path: InitVar[str]
    type: str="url" # "url", "content" or "websocket"

    url: str = field(init=False, default=None)
    content: str = field(init=False, default=None)
    filename: str = field(init=False, default=None)

    blocking: bool = False

    def __post_init__(self, path):
        self._path = path
        if self.type not in ("content", "url", "websocket"):
                    raise ValueError(f"Invalid type: {self.type}. Must be 'content', 'url' or 'websocket'.")
        self.filename = os.path.basename(path)
        if self.type == "url":
            # Assume path is already a valid URL or file path to be used as a URL
            self.url = path
        elif self.type == "content":
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File not found: {path}")
            with open(path, "rb") as f:
                raw_data = f.read()
                self.content = base64.b64encode(raw_data).decode("utf-8")
        elif self.type == "websocket":
            self.url = path

    def __str__( self ):
        return u'Open file {}'.format( self._path )
    
    def get_path( self ):
        """
        :return: the path to the file that will be opened, use this method
        to verify the content of the file in unit tests
        """
        return self._path

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