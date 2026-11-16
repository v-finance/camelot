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
from pathlib import PurePosixPath
import typing

from pydantic import AnyUrl

from camelot.admin.action import ActionStep

from ...core.serializable import DataclassSerializable, Serializable

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
    # TODO FIXME: Documentation needs to be updated

    url: AnyUrl
    blocking = False

    def get_path(self):
        """For testing purposes"""
        return self.url.path

    def __post_init__(self):
        assert isinstance(self.url, AnyUrl)

    def __str__(self):
        return 'Open file {}'.format(self.url.path)


@dataclass
class OpenClientDirectory(ActionStep, DataclassSerializable):
    path: PurePosixPath
    blocking = False


@dataclass
class DirectoryInfo(Serializable):
    exists: bool
    readable: bool
    writable: bool
    entries: typing.List[str]


@dataclass
class ClientDirectoryInfo(ActionStep, DataclassSerializable):
    """
    Retrieve information about a client side directory.

    :param path: the absolute path to the directory
    :param files: if not `None`, a filter on the names of the files to include

    The :keyword:`yield` statement will return a `DirectoryInfo` object.
    """

    path: [str]
    files: typing.Optional[str] = None

    @classmethod
    def deserialize_result(cls, model_context, response):
        return DirectoryInfo(**response)