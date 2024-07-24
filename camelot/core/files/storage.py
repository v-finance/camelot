import logging
import os
import shutil
import tempfile
from hashlib import sha1
from pathlib import Path, PurePath
from typing import Dict, BinaryIO, Tuple, IO, Generator, Optional

from camelot.core.conf import settings
from camelot.core.exception import UserException
from camelot.core.utils import ugettext

# Initialize the logger
logger = logging.getLogger('camelot.core.files.storage')


class StoredFile:
    def __init__(self, storage: 'Storage', name: PurePath, verbose_name: str):
        assert isinstance(name, PurePath)
        self.storage = storage
        self.name: PurePath = name
        assert isinstance(verbose_name, str)
        self.verbose_name = verbose_name

    def __getstate__(self) -> Dict[str, str]:
        """Returns the key of the file. To support pickling stored files
        in the database in a :class:`camelot.model.memento.Memento` object
        """
        return {'name': self.name.as_posix()}

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

    def __init__(self, upload_to: PurePath):
        """
        :param upload_to: the subdirectory in which to put files

        The actual files will be put in settings.CAMELOT_MEDIA_ROOT + upload to.
        """

        assert isinstance(upload_to, PurePath)
        self._upload_to = upload_to
        #
        # don't do anything here that might reduce the startup time, like verifying the
        # availability of the storage, since the path might be on a slow network share
        #

    @property
    def upload_to(self):
        root = settings.CAMELOT_MEDIA_ROOT
        return PurePath(root).joinpath(self._upload_to)

    def available(self, subdir: str = '') -> bool:
        """
        Verify if the storage is available, or create if it doesn't exist
        :return: True if the storage is available, False otherwise
        """
        try:
            if not (p := Path(self.upload_to, subdir)).exists():
                p.mkdir(parents=True)
            return True
        except Exception as e:
            logger.warning(f'Could not access or create path {p}, files will be unreachable', exc_info=e)
            return False

    def writeable(self) -> bool:
        return os.access(Path(self.upload_to), os.W_OK) if self.available() else False

    def exists(self, name: PurePath) -> bool:
        """Check if a file exists given its name

        :param name: Name of the file
        :return: True if the file exists, False otherwise
        """
        return Path(self._path(name)).exists()

    def list_files(self, prefix='', suffix='') -> Generator[StoredFile, None, None]:
        """List all files with a given prefix and/or suffix available in this storage

        :return: An iterator of StoredFile objects
        """

        pattern = f'{prefix}*{suffix}'
        upload_to_path = Path(self.upload_to)
        return (StoredFile(self, PurePath(path.name), self._verbose_name(path)) for path in upload_to_path.glob(pattern))

    def _path(self, name: PurePath) -> PurePath:
        """Get the local filesystem path where the file can be opened using Python standard open

        :param name: Name of the file
        :return: Path of the file
        """
        return self.upload_to.joinpath(name)

    def _create_tempfile_with_user_exceptions(self, suffix: str, prefix: str) -> Tuple[int, PurePath]:
        """Create a temporary file in the storage directory

        :param suffix: Suffix of the temporary file
        :param prefix: Prefix of the temporary file
        :return: File descriptor and file path of the temporary file
        """
        try:
            handle, name = self._create_tempfile(suffix, prefix)
            return handle, PurePath(name)
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

    def _create_tempfile(self, suffix: str, prefix: str) -> Tuple[int, str]:
        return tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.upload_to)

    def checkin(self, local_path: Path, filename: PurePath = None) -> StoredFile:
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

        assert isinstance(local_path, Path)
        assert local_path.resolve(strict=True)

        if filename is None and len(local_path.name) > 100:
            raise UserException(text=ugettext('The filename of the selected file is too long'),
                                resolution=ugettext('Please rename the file'))

        name = PurePath(filename or local_path)
        root, extension = name.stem, name.suffix

        handle, to_path = self._create_tempfile_with_user_exceptions(extension, root)
        os.close(handle)

        logger.debug(f'copy file from {local_path} to {to_path}')
        shutil.copy(Path(local_path), Path(to_path))
        filepath = self._process_path(PurePath(to_path))
        return StoredFile(self, filepath, self._verbose_name(filepath, name.name))

    def checkin_stream(self, prefix: str, suffix: str, stream: IO) -> StoredFile:
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
        handle, to_path = self._create_tempfile_with_user_exceptions(suffix, prefix)
        logger.debug('checkin stream to %s', to_path)

        with os.fdopen(handle, 'wb') as file:
            logger.debug('opened file')
            file.write(stream.read())
            logger.debug('written contents to file')
            file.flush()
        filepath = self._process_path(PurePath(to_path))
        return StoredFile(self, filepath, self._verbose_name(filepath, (prefix or '') + (suffix or '')))

    def checkout(self, stored_file: StoredFile) -> Path:
        """Check the file out of the storage and return a local filesystem path

        :param stored_file: StoredFile object
        :return: Path of the checked-out file
        """
        assert isinstance(stored_file, StoredFile)
        self.available()
        return Path(self._path(stored_file.name))

    # @contextmanager: NOTE: This should be a context manager so that the file always gets closed(doesn't happen now), good luck!
    def checkout_stream(self, stored_file: StoredFile) -> BinaryIO:
        """Check the file out of the storage as a data stream

        :param stored_file: StoredFile object
        :return: File object
        """
        assert isinstance(stored_file, StoredFile)
        self.available()
        return Path(self._path(stored_file.name)).open('rb')

    def delete(self, name: PurePath, recursive=False):
        """
        :param name: The name of the file to be deleted
        :param recursive: whether to remove directories and their contents recursively, False by default.
        """
        path = Path(self._path(name))
        if recursive and os.path.isdir(path):
            self._rmdir(path)
        else:
            path.unlink(missing_ok=True)

    def _rmdir(self, directory: PurePath):
        directory = Path(directory)
        for item in directory.iterdir():
            if item.is_dir():
                self._rmdir(item)
            else:
                self.delete(item)
        directory.rmdir()

    def _process_path(self, path: PurePath) -> PurePath:
        return PurePath(os.path.relpath(path, start=self.upload_to))

    def _verbose_name(self, path: PurePath, name_hint: Optional[str] = None) -> str:
        """
        return the verbose name of a path
        :param path: The path of the file
        """
        return name_hint if name_hint != '' and name_hint is not None else path.name


class HashStorage(Storage):

    def _process_path(self, path: PurePath) -> PurePath:
        return PurePath(os.path.relpath(path, start=settings.CAMELOT_MEDIA_ROOT))

    @staticmethod
    def get_hashed_name(name: str) -> str:
        return sha1(name.encode('UTF-8')).hexdigest()

    def _create_tempfile(self, suffix: str, prefix: str) -> Tuple[int, str]:
        hashed_prefix = self.get_hashed_name(prefix)
        self.available(subdir=hashed_prefix[:2])
        return tempfile.mkstemp(suffix=suffix, prefix=hashed_prefix, dir=self.upload_to.joinpath(hashed_prefix[:2]))

    def _path(self, name: PurePath) -> PurePath:
        return PurePath(settings.CAMELOT_MEDIA_ROOT).joinpath(name)

    def list_files(self, prefix='', suffix=''):
        # TODO user exception?
        raise NotImplementedError("list_files is not implemented for HashStorage")
