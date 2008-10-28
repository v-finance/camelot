import settings
import logging
import os

from sqlalchemy import types

logger = logging.getLogger('cantate.types')
logger.setLevel(logging.DEBUG)

from sqlalchemy import types

class VirtualAddress(types.TypeDecorator):
  """
  Sqlalchemy type to store virtual addresses : eg, phone number, e-mail address, ...
  
  This column type accepts and returns tuples of strings, the first string is
  the virtual_address_type, and the second the address itself:
  
  eg: ('mail','project-camelot@conceptive.be') is stored as mail://project-camelot@conceptive.be
  """
  
  impl = types.Unicode
  virtual_address_types = ['phone', 'fax', 'mobile', 'email', 'im', 'pager',]

  def bind_processor(self, dialect):

    impl_processor = self.impl.bind_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x
    
    def processor(value):
      if value is not None:
        value = '://'.join(value)
      return impl_processor(value)
    
    return processor

  def result_processor(self, dialect):
    
    impl_processor = self.impl.result_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x

    def processor(value):

      if value:
        return value.split('://')
      return ('phone','')
      
    return processor  
    
class Code(types.TypeDecorator):
  """
  Sqlalchemy column type to store codes
  
  This column type accepts and returns a list of strings and stores them as a
  string joined with points.
  
  eg: ['08', 'AB'] is stored as 08.AB
  
  @param parts: a list of input masks specifying the mask for each part, eg ['99', 'AA'], for
  valid input masks, see the docs of qlineedit
  """
  
  impl = types.Unicode
        
  def __init__(self, parts, **kwargs):
    import string
    translator = string.maketrans('', '')
    self.parts = parts
    max_length = sum(len(part.translate(translator, '<>!')) for part in parts) + len(parts)
    types.TypeDecorator.__init__(self, length=max_length, **kwargs)
    
  def bind_processor(self, dialect):

    impl_processor = self.impl.bind_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x
    
    def processor(value):
      if value is not None:
        value = '.'.join(value)
      return impl_processor(value)
    
    return processor

  def result_processor(self, dialect):
    
    impl_processor = self.impl.result_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x

    def processor(value):

      if value:
        return value.split('.')
      return ['' for p in self.parts]
      
    return processor
  
class IPAddress(Code):
  
  def __init__(self, **kwargs):
    super(IPAddress, self).__init__(parts=['900','900','900','900'])
    
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

      if value:
        value = os.path.join(self.upload_to, impl_processor(value))
        if os.path.exists(value):
          return PILImage.open( value )
        else:
          logger.warn('Image at %s does not exist'%value)
      
    return processor
