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

import logging

logger = logging.getLogger( 'camelot.core.files.storage' )

from camelot.core.conf import settings
from camelot.core.exception import UserException
from camelot.core.utils import ugettext
from camelot.view.model_thread import model_function

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
    
    def __unicode__( self ):
        return self.verbose_name

class StoredImage( StoredFile ):
    """Helper class for the Image field type Class linking an image and the
    location and filename where the image is stored"""

    def __init__( self, storage, name ):
        super(StoredImage, self).__init__( storage, name )
        self._thumbnails = dict()
        
    @model_function
    def checkout_image( self ):
        """Checkout the image from the storage, this function is only to be
        used in the model thread.
        
        :return: a QImage
        """
        from PyQt4.QtGui import QImage
        p = self.storage.checkout( self )
        image = QImage(p)
        
        if image.isNull():
            return QImage(':/image_not_found.png')
        else:
            return image

    @model_function
    def checkout_thumbnail( self, width, height ):
        """Checkout a thumbnail for this image from the storage, this function
        is only to be used in the model thread
        :param width: the requested width of the thumbnail

        
        :return: a QImage
        """
        key = (width, height)
        try:
            thumbnail_image = self._thumbnails[key]
            return thumbnail_image
        except KeyError:
            pass
        from PyQt4.QtCore import Qt
        original_image = self.checkout_image()
        thumbnail_image = original_image.scaled( width, height, Qt.KeepAspectRatio )
        self._thumbnails[key] = thumbnail_image
        return thumbnail_image

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
        self._root = (root or settings.CAMELOT_MEDIA_ROOT)
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
            import os
            if callable( self._root ):
                root = self._root()
            else:
                root = self._root
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
        except Exception, e:
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
        except EnvironmentError, e:
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
        to_path = os.path.join( self.upload_to, filename or os.path.basename( local_path ) )
        if os.path.exists(to_path):
            # only if the default to_path exists, we'll give it a new name
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
        file.write( stream.read() )
        file.flush()
        file.close()
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

class S3Storage( object ):
    """Helper class that opens and saves StoredFile objects into Amazon S3.

    these attibutes need to be set in your settings for S3Storage to work :
     * AWS_ACCESS_KEY_ID = '<INSERT YOUR AWS ACCESS KEY ID HERE>'
     * AWS_SECRET_ACCESS_KEY = '<INSERT YOUR AWS SECRET ACCESS KEY HERE>'
     * AWS_BUCKET_NAME = 'camelot'
     * AWS_LOCATION = S3.Location.DEFAULT
     
    Using this Storage requires the availability of S3.py on your PYTHONPATH.
    S3.py can be found on the amazon.com website
    """

    def __init__( self, upload_to = '', stored_file_implementation = StoredFile ):
        # try to work around bug S3 code which uses bad names of days
        # http://code.google.com/p/boto/issues/detail?id=140
        # but workaround doesn't work :(
        #import locale
#    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
#    print 'create S3 storage'
        import S3
        self.upload_to = upload_to
        conn = S3.AWSAuthConnection( settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY )
#        _generator = S3.QueryStringAuthGenerator( settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY )
        if ( conn.check_bucket_exists( settings.AWS_BUCKET_NAME ).status == 200 ):
            pass
        else:
            conn.create_located_bucket( settings.AWS_BUCKET_NAME, settings.AWS_LOCATION ).message



