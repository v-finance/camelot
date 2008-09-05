import settings
import logging
import os

from sqlalchemy import types

logger = logging.getLogger('cantate.types')
logger.setLevel(logging.DEBUG)

from sqlalchemy import types

# Try to import PIL in various ways
try:
  from PIL import Image as PILImage
except:
  import Image as PILImage
        
class Image(types.TypeDecorator):
  """
  Sqlalchemy column type to store images
  
  This column type accepts and returns PIL images, and stores them in the directory
  specified by settings.MEDIA_ROOT.  The name of the file is stored as a string in
  the database.
  """
  
  impl = types.Unicode
  
  def __init__(self, max_length=100, upload_to='', prefix='image-', format='png', **kwargs):
    self.upload_to = os.path.join(settings.CAMELOT_MEDIA_ROOT, upload_to)
    self.prefix = prefix
    self.format = format
    self.max_length = max_length
    if not os.path.exists(self.upload_to):
      os.makedirs(self.upload_to)
    types.TypeDecorator.__init__(self, length=max_length, **kwargs)
    
  def bind_processor(self, dialect):

    impl_processor = self.impl.bind_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x
    
    def processor(value):
      if value is not None:
        import tempfile
        import os
        (handle, name) = tempfile.mkstemp(suffix='.%s'%self.format, prefix=self.prefix, dir=os.path.join(self.upload_to))
        value.save(os.fdopen(handle, 'wb'), 'png')
        value = os.path.basename(name)
      return impl_processor(value)
    
    return processor

  def result_processor(self, dialect):
    
    impl_processor = self.impl.result_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x
      
    def processor(value):

      import os
      if value:
        value = os.path.join(self.upload_to, impl_processor(value))
        if os.path.exists(value):
          return PILImage.open( value )
        else:
          logger.warn('Image at %s does not exist'%value)
      
    return processor
