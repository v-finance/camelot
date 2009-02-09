#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Custom Camelot field types that extend the SQLAlchemy field types.
"""

import os

import logging
logger = logging.getLogger('camelot.types')
logger.setLevel(logging.DEBUG)

from sqlalchemy import types


class VirtualAddress(types.TypeDecorator):
  """Sqlalchemy type to store virtual addresses : eg, phone number, e-mail
  address, ...
  
  This column type accepts and returns tuples of strings, the first string is
  the virtual_address_type, and the second the address itself:
  
  eg: ('mail','project-camelot@conceptive.be') is stored as 
  mail://project-camelot@conceptive.be
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
  """Sqlalchemy column type to store codes.  Where a code is a list of strings
  on which a regular expression can be enforced.
  
  This column type accepts and returns a list of strings and stores them as a
  string joined with points.
  
  eg: ['08', 'AB'] is stored as 08.AB
  

  """
  
  impl = types.Unicode
        
  def __init__(self, parts, **kwargs):
    """
    @param parts: a list of input masks specifying the mask for each part, eg ['99', 'AA'], for
    valid input masks, see the docs of qlineedit    
    """
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
    
class RichText(types.TypeDecorator):
  """Sqlalchemy column type to store rich text
  
  by default, fields of this type will be displayed within a rich
  text editor"""
  
  impl = types.UnicodeText
  
# Try to import PIL in various ways
try:
  from PIL import Image as PILImage
except:
  import Image as PILImage
        

class StoredImage(object):
  """Class linking a PIL image and the location and filename where the image is stored"""
  
  def __init__(self, image, location=None, filename=None):
    self.image = image
    self.location = location
    self.filename = filename
  
  @property
  def full_path(self):
    import os
    return os.path.join(self.location, self.filename)
    
    
class Image(types.TypeDecorator):
  """Sqlalchemy column type to store images
  
  This column type accepts and returns a StoredImage, and stores them in the directory
  specified by settings.MEDIA_ROOT.  The name of the file is stored as a string in
  the database.
  """
  
  impl = types.Unicode
  
  def __init__(self, max_length=100, upload_to='', prefix='image-', format='png', **kwargs):
    import settings
    self.upload_to = os.path.join(settings.CAMELOT_MEDIA_ROOT, upload_to)
    self.prefix = prefix
    self.format = format
    self.max_length = max_length
    try:
      if not os.path.exists(self.upload_to):
        os.makedirs(self.upload_to)
    except Exception, e:
      logger.warn('Could not access or create image path %s, images will be unreachable'%self.upload_to, exc_info=e)
    types.TypeDecorator.__init__(self, length=max_length, **kwargs)
    
  def bind_processor(self, dialect):

    impl_processor = self.impl.bind_processor(dialect)
    if not impl_processor:
      impl_processor = lambda x:x
    
    def processor(value):
      if value is not None:
        import tempfile
        (handle, name) = tempfile.mkstemp(suffix='.%s'%self.format, prefix=self.prefix, dir=os.path.join(self.upload_to))
        value.image.save(os.fdopen(handle, 'wb'), 'png')
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
          try:
            return StoredImage(PILImage.open( open(value, 'rb') ), self.upload_to, value)
          except Exception, e:
            logger.warn('Cannot open image at %s'%value, exc_info=e)
            return None
        else:
          logger.warn('Image at %s does not exist'%value)
      
    return processor
