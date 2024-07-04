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


import logging
import os
import shutil
import tempfile
from io import IOBase
from hashlib import sha1
from pathlib import Path, PurePosixPath
from typing import Dict, BinaryIO

from camelot.core.conf import settings
from camelot.core.exception import UserException
from camelot.core.utils import ugettext

# Initialize the logger
logger = logging.getLogger('camelot.core.files.storage')


class StoredFile:
    """Helper class for the File field type.
    Stored file objects can be used within the GUI thread, as none of
    its methods should block.
    """

    def __init__(self, storage: 'Storage', name: str):
        """
        :param storage: the storage in which the file is stored
        :param name: the key by which the file is known in the storage
        """
        self.storage = storage
        self.name = name

    @property
    def verbose_name(self) -> str:
        """The name of the file, as it is to be displayed in the GUI"""
        return self.name

    def __getstate__(self) -> Dict[str, str]:
        """Returns the key of the file. To support pickling stored files
        in the database in a :class:`camelot.model.memento.Memento` object
        """
        return {'name': self.name}

    def __str__(self) -> str:
        return self.verbose_name


class Storage:
    """
    Helper class that opens and saves StoredFile objects
    The default implementation stores files in the settings.CAMELOT_MEDIA_ROOT
    directory.  The storage object should only be used within the model thread,
    as all of its methods might block.

    The methods of this class don't verify if they are called on the model
    thread, because these classes can be used server side or in a non-gui
    script as well.
    """

    def __init__(self, upload_to: PurePosixPath = None):
        """
        :param upload_to: the subdirectory in which to put files
        :param stored_file_implementation: the subclass of StoredFile to be used when
        checking out files from the storage
        :param root: the root directory in which to put files, this may be a callable that
        takes no arguments. If root is a callable, it will be called in the model thread
        to get the actual root of the media store.

        The actual files will be put in root + upload to.  If None is given as root,
        the settings.CAMELOT_MEDIA_ROOT will be taken as the root directory.
        """
        if upload_to is None:
            upload_to = PurePosixPath('')
        assert isinstance(upload_to, PurePosixPath)
        self._upload_to = upload_to
        #
        # don't do anything here that might reduce the startup time, like verifying the
        # availability of the storage, since the path might be on a slow network share
        #

    @property
    def upload_to(self):
        return PurePosixPath(settings.CAMELOT_MEDIA_ROOT()).joinpath(self._upload_to)

    def available(self) -> bool:
        """
        Verify if the storage is available, or create if it doesn't exist
        :return: True if the storage is available, False otherwise
        """
        try:
            if not (p := Path(self.upload_to)).exists():
                p.mkdir(parents=True)
            return True
        except Exception as e:
            logger.warning(f'Could not access or create path {self.upload_to}, files will be unreachable', exc_info=e)
            return False

    def writeable(self):
        """Verify if the storage is available and writable

        :return: True if the storage is writable, False otherwise
        """
        if self.available():
            return os.access(Path(self.upload_to), os.W_OK)
        return False

    def exists(self, name: PurePosixPath) -> bool:
        """Check if a file exists given its name

        :param name: Name of the file
        :return: True if the file exists, False otherwise
        """
        return Path(self.path(name)).exists()

    def list_files(self, prefix='*', suffix='*'):
        """List all files with a given prefix and/or suffix available in this storage

        :return: An iterator of StoredFile objects
        """
        if suffix == '*':
            pattern = f'{prefix}*'
        else:
            pattern = f'{prefix}*{suffix}'

        upload_to_path = Path(self.upload_to)
        return (StoredFile(self, path.name) for path in upload_to_path.glob(pattern))

    def path(self, name) -> PurePosixPath:
        """Get the local filesystem path where the file can be opened using Python standard open

        :param name: Name of the file
        :return: Path of the file
        """
        return self.upload_to.joinpath(name)

    def _create_tempfile(self, suffix: str, prefix: str):
        # @todo suffix and prefix should be cleaned, because the user might be
        #       able to get directory separators in here or something related
        """Create a temporary file in the storage directory

        :param suffix: Suffix of the temporary file
        :param prefix: Prefix of the temporary file
        :return: File descriptor and file path of the temporary file
        """
        try:
            return tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.upload_to)
        except EnvironmentError as e:
            if not self.exists(self.upload_to):
                raise UserException(text=ugettext(f'The directory {self.upload_to} does not exist'),
                                    resolution=ugettext('Contact your system administrator'))
            if not self.writeable():
                raise UserException(text=ugettext(f'You have no write permissions for {self.upload_to}'),
                                    resolution=ugettext('Contact your system administrator'))
            raise UserException(text=ugettext(f'Unable to write file to {self.upload_to}'),
                                resolution=ugettext('Contact your system administrator'),
                                detail=ugettext(
                                    f'OS Error number : {e.errno}\nError : {e.strerror}\nPrefix : {prefix}\nSuffix : {suffix}'))

    def checkin(self, local_path: PurePosixPath, filename: str = None) -> StoredFile:
        """Check the file pointed to by local_path into the storage and return a StoredFile

        :param local_path: The path to the local file that needs to be checked in
        :param filename: A hint for the filename to be given to the checked in file, if None
                         is given, the filename from the local path will be taken.
        :return: StoredFile object

        The stored file is not guaranteed to have the filename asked, since the
        storage might not support this filename, or another file might be named
        like that. In each case the storage will choose the filename.
        """
        self.available()

        local_path = PurePosixPath(local_path)
        if filename is None and len(local_path.name) > 100:
            raise UserException(text=ugettext('The filename of the selected file is too long'),
                                resolution=ugettext('Please rename the file'))

        root, extension = os.path.splitext(filename or local_path.name)

        handle, to_path = self._create_tempfile(extension, root)
        os.close(handle)

        to_path = PurePosixPath(to_path)
        logger.debug(f'copy file from {local_path} to {to_path}')
        shutil.copy(Path(local_path), Path(to_path))

        return StoredFile(self, to_path.name)

    def checkin_stream(self, prefix: str, suffix: str, stream: IOBase) -> StoredFile:
        """Check the data stream as a file into the storage

        :param prefix: The prefix to use for generating a file name
        :param suffix: The suffix to use for generating a file name, e.g., '.png'
        :param stream: The data stream to be checked in
        :return: a StoredFile

        This method can also be used in combination with the StringIO module::

        import StringIO

        stream = StringIO.StringIO()
        # write everything to the stream
        stream.write( 'bla bla bla' )
        # prepare the stream for reading
        stream.seek( 0 )
        stored_file = storage.checkin_stream( 'document', '.txt', stream )
        """
        self.available()
        handle, to_path = self._create_tempfile(suffix, prefix)
        logger.debug('checkin stream to %s', to_path)

        with os.fdopen(handle, 'wb') as file:
            logger.debug('opened file')
            file.write(stream.read())
            logger.debug('written contents to file')
            file.flush()
            logger.debug('flushed file')

        logger.debug('closed file')
        return StoredFile(self, os.path.basename(to_path))

    def checkout(self, stored_file: StoredFile) -> PurePosixPath:
        """Check the file out of the storage and return a local filesystem path

        :param stored_file: StoredFile object
        :return: Path of the checked-out file
        """
        assert isinstance(stored_file, StoredFile)
        self.available()
        return self.upload_to.joinpath(stored_file.name)

    # @contextmanager: NOTE: This should be a context manager so that the file always gets closed(doesn't happen now), good luck!
    def checkout_stream(self, stored_file: PurePosixPath) -> BinaryIO:
        """Check the file out of the storage as a data stream

        :param stored_file: StoredFile object
        :return: File object
        """
        assert isinstance(stored_file, StoredFile)
        self.available()
        return Path(self.upload_to, stored_file.name).open('rb')

    def delete(self, name):
        pass


class HashStorage(Storage):

    def __init__(self, upload_to: PurePosixPath = None):
        super().__init__(upload_to)
        self.hash_folder: PurePosixPath = PurePosixPath('')

    def _create_tempfile(self, suffix: str, prefix: str):
        # @todo suffix and prefix should be cleaned, because the user might be
        #       able to get directory separators in here or something related
        """Create a temporary file in the storage directory

        :param suffix: Suffix of the temporary file
        :param prefix: Prefix of the temporary file
        :return: File descriptor and file path of the temporary file
        """
        hexhash = sha1(prefix.encode('UTF-8')).hexdigest()
        self.hash_folder = hexhash[:2]
        self.available()
        return super()._create_tempfile(suffix, hexhash)

    @property
    def upload_to(self):
        return PurePosixPath(settings.CAMELOT_MEDIA_ROOT()).joinpath(self._upload_to, self.hash_folder)

