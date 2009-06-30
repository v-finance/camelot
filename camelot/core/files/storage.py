# -*- coding: utf8 -*-

import logging

logger = logging.getLogger('camelot.core.files.storage')

from camelot.view.model_thread import model_function

class StoredFile(object):
  """Helper class for the File field type.
  Stored file objects can be used within the GUI thread, as none of
  its methods should block.
  """
  
  def __init__(self, storage, name):
    """
:param storage: the storage in which the file is stored
:param name: the key by which the file is known in the storage"""
    self.storage = storage
    self.name = name
    
  @property
  def verbose_name(self):
    """The name of the file, as it is to be displayed in the GUI"""
    return self.name
  
  def __unicode__(self):
    return self.verbose_name
  
class Storage(object):
  """Helper class that opens and saves StoredFile objects
The default implementation stores files in the settings.CAMELOT_MEDIA_ROOT
directory.  The storage object should only be used within the model thread,
as all of it's methods might block.
  """

  def __init__(self, upload_to=''):
    """
:param upload_to: the sub directory in which to put files
"""
    import settings
    import os
    self.upload_to = os.path.join(settings.CAMELOT_MEDIA_ROOT, upload_to)
    try:
      if not os.path.exists(self.upload_to):
        os.makedirs(self.upload_to)
    except Exception, e:
      logger.warn('Could not access or create path %s, files will be unreachable'%self.upload_to, exc_info=e)
 
  @model_function
  def exists(self, name):
    """True if a file exists given some name"""
    import os
    os.path.exists(self.path(name))
    
  @model_function
  def path(self, name):
    """The local filesystem path where the file can be opened using Python’s standard open"""
    import os
    return os.path.join(self.upload_to, name)

  @model_function
  def checkin(self, local_path):
    """Check the file pointed to by local_path into the storage, and
    return a StoredFile"""
    import tempfile
    import shutil
    import os
    print 'checkin', local_path
    root, extension = os.path.splitext(os.path.basename(local_path))
    (handle, to_path) = tempfile.mkstemp(suffix=extension, prefix=root, dir=self.upload_to, text='b')
    os.close(handle)
    logger.debug('copy file from %s to %s', local_path, to_path)
    shutil.copy(local_path, to_path)
    return StoredFile(self, os.path.basename(to_path))
  
  @model_function
  def checkout(self, stored_file):
    """Check the file pointed to by the local_path out of the storage and return
a local filesystem path where the file can be opened"""
    import os
    return os.path.join(self.upload_to, stored_file.name)

  @model_function
  def delete(self, name):
    pass

class S3Storage(object):
  """Helper class that opens and saves StoredFile objects into Amazon S3.
  
  these attibutes need to be set in your settings for S3Storage to work :
   * AWS_ACCESS_KEY_ID = '<INSERT YOUR AWS ACCESS KEY ID HERE>'
   * AWS_SECRET_ACCESS_KEY = '<INSERT YOUR AWS SECRET ACCESS KEY HERE>'
   * AWS_BUCKET_NAME = 'camelot'
   * AWS_LOCATION = S3.Location.DEFAULT
  """

  def __init__(self, upload_to=''):
    import locale
    # try to work around bug S3 code which uses bad names of days
    # http://code.google.com/p/boto/issues/detail?id=140
    # but workaround doesn't work :(
#    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
#    print 'create S3 storage'
    import settings
    import S3
    self.upload_to=upload_to    
    conn = S3.AWSAuthConnection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    generator = S3.QueryStringAuthGenerator(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    if (conn.check_bucket_exists(settings.AWS_BUCKET_NAME).status == 200):
      pass
    else:
      print '----- creating bucket -----'
      print conn.create_located_bucket(settings.AWS_BUCKET_NAME, settings.AWS_LOCATION).message