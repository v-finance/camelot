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

logger = logging.getLogger( 'camelot.core.files.storage' )



from camelot.core.conf import settings
from camelot.core.exception import UserException
from camelot.core.utils import ugettext

class StoredFile( object ):
    """Helper class for the File field type.
    Stored file objects can be used within the GUI thread, as none of
    its methods should block.
    """

    def __init__( self, storage, name ):
        """
    :param storage: the storage in which the file is stored
    :param name: the key by which the file is known in the storage"""
        self.storage = storage
        self.name = name

    @property
    def verbose_name( self ):
        """The name of the file, as it is to be displayed in the GUI"""
        return self.name

    def __getstate__( self ):
        """Returns the key of the file.  To support pickling stored files
        in the database in a :class:`camelot.model.memento.Memento`
        object"""
        return dict( name = self.name )
    
    def __str__( self ):
        return self.verbose_name

class Storage( object ):
    """Helper class that opens and saves StoredFile objects
  The default implementation stores files in the settings.CAMELOT_MEDIA_ROOT
  directory.  The storage object should only be used within the model thread,
  as all of it's methods might block.

  The methods of this class don't verify if they are called on the model
  thread, because these classes can be used server side or in a non-gui
  script as well.
    """

    def __init__( self, upload_to = '', 
                  stored_file_implementation = StoredFile,
                  root = None ):
        """
    :param upload_to: the sub directory in which to put files
    :param stored_file_implementation: the subclass of StoredFile to be used when
    checking out files from the storage
    :param root: the root directory in which to put files, this may be a callable that
    takes no arguments.  if root is a callable, it will be called in the model thread
    to get the actual root of the media store.
    
    The actual files will be put in root + upload to.  If None is given as root,
    the settings.CAMELOT_MEDIA_ROOT will be taken as the root directory.
    """
        self._root = root
        self._subfolder = upload_to
        self._upload_to = None
        self.stored_file_implementation = stored_file_implementation
        #
        # don't do anything here that might reduce the startup time, like verifying the
        # availability of the storage, since the path might be on a slow network share
        #

    @property
    def upload_to(self):
        if self._upload_to == None:
            root = self._root or settings.CAMELOT_MEDIA_ROOT
            import os
            if callable( root ):
                root = root()
            self._upload_to = os.path.join( root, self._subfolder )
        return self._upload_to
        
    def available(self):
        """Verify if the storage is available

        :return: True if the storage is available, False otherwise
        """
        import os
        try:
            if not os.path.exists( self.upload_to ):
                os.makedirs( self.upload_to )
            return True
        except Exception as e:
            logger.warn( 'Could not access or create path %s, files will be unreachable' % self.upload_to, exc_info = e )

    def writeable(self):
        """Verify if the storage is available and writeable

        :return: True if the storage is writeable, False otherwise
        """
        import os
        if self.available():
            return os.access(self.upload_to, os.W_OK) 
        
    def exists( self, name ):
        """True if a file exists given some name"""
        if self.available():
            import os
            return os.path.exists( self.path( name ) )
        return False
        
    def list(self, prefix='*', suffix='*'):
        """Lists all files with a given prefix and or suffix available in this storage

        :return: a iterator of StoredFile objects
        """
        import glob
        import os
        return (StoredFile(self, os.path.basename(name) ) for name in glob.glob( os.path.join( self.upload_to, u'%s*%s'%(prefix, suffix) ) ) )

    def path( self, name ):
        """The local filesystem path where the file can be opened using Python standard open"""
        import os
        return os.path.join( self.upload_to, name )

    def _create_tempfile( self, suffix, prefix ):
        import tempfile
        # @todo suffix and prefix should be cleaned, because the user might be
        #       able to get directory separators in here or something related
        try:
            return tempfile.mkstemp( suffix = suffix, prefix = prefix, dir = self.upload_to, text = 'b' )
        except EnvironmentError as e:
            if not self.available():
                raise UserException( text = ugettext('The directory %s does not exist')%(self.upload_to),
                                     resolution = ugettext( 'Contact your system administrator' ) )
            if not self.writeable():
                raise UserException( text = ugettext('You have no write permissions for %s')%(self.upload_to),
                                     resolution = ugettext( 'Contact your system administrator' ) )
            
            raise UserException( text = ugettext('Unable to write file to %s')%(self.upload_to),
                                 resolution = ugettext( 'Contact your system administrator' ),
                                 detail = ugettext('OS Error number : %s \nError : %s \nPrefix : %s \nSuffix : %s')%( e.errno,
                                                                                                                      e.strerror,
                                                                                                                      prefix,
                                                                                                                      suffix ) )
        
    def checkin( self, local_path, filename=None ):
        """Check the file pointed to by local_path into the storage, and
        return a StoredFile
        
        :param local_path: the path to the local file that needs to be checked in
        :param filename: a hint for the filename to be given to the checked in file, if None
        is given, the filename from the local path will be taken.

        The stored file is not guaranteed to have the filename asked, since the
        storage might not support this filename, or another file might be named
        like that.  In each case the storage will choose the filename.
        """
        self.available()
        import shutil
        import os
        if filename is None and len(os.path.basename( local_path )) > 100:
            raise UserException( text = ugettext('The filename of the selected file is too long'),
                                     resolution = ugettext( 'Please rename the file' ) )
        root, extension = os.path.splitext( filename or os.path.basename( local_path ) )
        ( handle, to_path ) = self._create_tempfile( extension, root )
        os.close( handle )
        logger.debug( u'copy file from %s to %s', local_path, to_path )
        shutil.copy( local_path, to_path )
        return self.stored_file_implementation( self, os.path.basename( to_path ) )

    def checkin_stream( self, prefix, suffix, stream ):
        """Check the datastream in as a file into the storage

        :param prefix: the prefix to use for generating a file name
        :param suffix: the suffix to use for generating a filen name, eg '.png'
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
        import os
        ( handle, to_path ) = self._create_tempfile( suffix, prefix )
        logger.debug(u'checkin stream to %s'%to_path)
        file = os.fdopen( handle, 'wb' )
        logger.debug('opened file')
        file.write( stream.read() )
        logger.debug('written contents to file')
        file.flush()
        logger.debug('flushed file')
        file.close()
        logger.debug('closed file')
        return self.stored_file_implementation( self, os.path.basename( to_path ) )

    def checkout( self, stored_file ):
        """Check the file pointed to by the local_path out of the storage and return
    a local filesystem path where the file can be opened"""
        self.available()
        import os
        return os.path.join( self.upload_to, stored_file.name )

    def checkout_stream( self, stored_file ):
        """Check the file stored_file out of the storage as a datastream

        :return: a file object
        """
        self.available()
        import os
        return open( os.path.join( self.upload_to, stored_file.name ), 'rb' )

    def delete( self, name ):
        pass


