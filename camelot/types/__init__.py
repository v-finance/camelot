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

"""
Camelot extends the SQLAlchemy field types with a number of its own field
types. Those field types are automatically mapped to a specific delegate taking
care of the visualisation.

Those fields are stored in the :mod:`camelot.types` module.
"""

import logging
logger = logging.getLogger('camelot.types')

from sqlalchemy import types

from camelot.core.files.storage import StoredFile, StoredImage, Storage

class VirtualAddress(types.TypeDecorator):
    """A single field that can be used to enter phone numbers, fax numbers, email
    addresses, im addresses.  The editor provides soft validation of the data
    entered.  The address or number is stored as a string in the database.
      
    This column type accepts and returns tuples of strings, the first string is
    the :attr:`virtual_address_type`, and the second the address itself.
  
    eg: ``('email','project-camelot@conceptive.be')`` is stored as
    ``mail://project-camelot@conceptive.be``
  
    .. image:: ../_static/virtualaddress_editor.png
    """
    
    impl = types.Unicode
    virtual_address_types = ['phone', 'fax', 'mobile', 'email', 'im', 'pager',]
  
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                if value[1]:
                    value = u'://'.join(value)
                else:
                    value = None
            return impl_processor(value)
          
        return processor
    
    def result_processor(self, dialect):
      
        impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
      
        def processor(value):
    
            if value:
                split = value.split('://')
                if len(split)>1:
                    return tuple(split)
            return (u'phone',u'')
            
        return processor  
        
    
class Code(types.TypeDecorator):
    """SQLAlchemy column type to store codes.  Where a code is a list of strings
    on which a regular expression can be enforced.
  
    This column type accepts and returns a list of strings and stores them as a
    string joined with points.
  
    eg: ``['08', 'AB']`` is stored as ``08.AB``
    """
    
    impl = types.Unicode
          
    def __init__(self, parts, **kwargs):
        """
        :param parts: a list of input masks specifying the mask for each part,
        eg ``['99', 'AA']``. For valid input masks, see
        `QLineEdit <http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qlineedit.html>`_
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
                value = u'.'.join(value)
            return impl_processor(value)
          
        return processor
    
    def result_processor(self, dialect):
      
        impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
      
        def processor(value):
    
            if value:
                return value.split('.')
            return ['' for _p in self.parts]
            
        return processor
    
class IPAddress(Code):
    def __init__(self, **kwargs):
        super(IPAddress, self).__init__(parts=['900','900','900','900'])
    
class Rating(types.TypeDecorator):
    """The rating field is an integer field that is visualized as a number of stars that
  can be selected::
  
    class Movie(Entity):
      title = Field(Unicode(60), required=True)
      rating = Field(camelot.types.Rating())
      
  .. image:: ../_static/rating.png"""
    
    impl = types.Integer
       
class RichText(types.TypeDecorator):
    """RichText fields are unlimited text fields which contain html.  The html will be
  rendered in a rich text editor.  
  
  .. image:: ../_static/richtext.png"""
    
    impl = types.UnicodeText
     
class Language(types.TypeDecorator):
    """The languages are stored as ISO codes in the database
    """
    
    import babel
    
    impl = types.Unicode
    choices = []
    for code in babel.localedata.list():
        locale = babel.Locale(code)
        display_name = locale.get_display_name()
        if display_name:
            choices.append((code, u'%s (%s)'%(code, display_name)))
        else:
            choices.append((code, code))
    
    def __init__(self):
        types.TypeDecorator.__init__(self, length=20)
        
class Color(types.TypeDecorator):
    """The Color field returns and accepts tuples of the form (r,g,b,a) where
  r,g,b,a are integers between 0 and 255. The color is stored as an hexadecimal
  string of the form AARRGGBB into the database, where AA is the transparency, 
  RR is red, GG is green BB is blue::
  
    class MovieType(Entity):
      color = Field(camelot.types.Color())
  
  .. image:: ../_static/color.png
  
  
  The colors are stored in the database as strings 
    """
    
    impl = types.Unicode
    
    def __init__(self):
        types.TypeDecorator.__init__(self, length=8)
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                assert len(value) == 4
                for i in range(4):
                    assert value[i] >= 0
                    assert value[i] <= 255
                return '%02X%02X%02X%02X'%(value[3], value[0], value[1], value[2])
            return impl_processor(value)
          
        return processor
      
    def result_processor(self, dialect):
      
        impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
            
        def processor(value):
    
            if value:
                return (int(value[2:4],16), int(value[4:6],16), int(value[6:8],16), int(value[0:2],16))
              
        return processor
      
class Enumeration(types.TypeDecorator):
    """The enumeration field stores integers in the database, but represents them as
  strings.  This allows efficient storage and querying while preserving readable code.
  
  Typical use of this field would be a status field.
  
  Enumeration fields are visualized as a combo box, where the labels in the combo
  box are the capitalized strings::
  
    class Movie(Entity):
      title = Field(Unicode(60), required=True)
      state = Field(camelot.types.Enumeration([(1,'planned'), (2,'recording'), (3,'finished'), (4,'canceled')]), 
                                              index=True, required=True, default='planning')
  
  .. image:: ../_static/enumeration.png  
  """
    
    impl = types.Integer
    
    def __init__(self, choices=[], **kwargs):
        """
        @param param: choices is a list of tuples.  each tuple contains an integer and its
        associated string.  eg. : choices = [(1,'draft'), (2,'approved')]
        """
        types.TypeDecorator.__init__(self, **kwargs)
        self._int_to_string = dict(choices)
        self._string_to_int = dict((v,k) for (k,v) in choices)
        self.choices = [v for (k,v) in choices]
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                try:
                    value = self._string_to_int[value]
                    return impl_processor(value)
                except KeyError, e:
                    logger.error('could not process enumeration value %s, possible values are %s'%(value, u', '.join(list(self._string_to_int.keys()))), exc_info=e)
                        
        return processor
    
    def result_processor(self, dialect):
      
        impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
            
        def processor(value):
            if value is not None:
                value = impl_processor(value)
                try:
                    return self._int_to_string[value]
                except KeyError, e:
                    logger.error('could not process %s'%value, exc_info=e)
                
        return processor
    
class File(types.TypeDecorator):
    """Sqlalchemy column type to store files.  Only the location of the file is stored
    
  This column type accepts and returns a StoredFile, and stores them in the directory
  specified by settings.MEDIA_ROOT.  The name of the file is stored as a string in
  the database.  A subdirectory upload_to can be specified::
  
    class Movie(Entity):
      script = Field(camelot.types.File(upload_to='script'))
      
  .. image:: ../_static/file_delegate.png
    """
    
    impl = types.Unicode
    stored_file_implementation = StoredFile
    
    def __init__(self, max_length=100, upload_to='', storage=Storage, **kwargs):
        self.max_length = max_length
        self.storage = storage(upload_to, self.stored_file_implementation)
        types.TypeDecorator.__init__(self, length=max_length, **kwargs)
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                assert isinstance(value, (self.stored_file_implementation))
                return impl_processor(value.name)
            return impl_processor(value)
          
        return processor
    
    def result_processor(self, dialect):
      
        impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
            
        def processor(value):
    
            if value:
                value = impl_processor(value)
                return self.stored_file_implementation(self.storage, value)
              
        return processor
      
class Image(File):
    """Sqlalchemy column type to store images
    
  This column type accepts and returns a StoredImage, and stores them in the directory
  specified by settings.MEDIA_ROOT.  The name of the file is stored as a string in
  the database.
  
  The Image field type provides the same functionallity as the File field type, but
  the files stored should be images.
  
  .. image:: ../_static/image.png  
    """
  
    stored_file_implementation = StoredImage
