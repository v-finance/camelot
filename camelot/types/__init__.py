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

"""
Camelot extends the SQLAlchemy column types with a number of its own column
types. Those field types are automatically mapped to a specific delegate taking
care of the visualisation.

Those fields are stored in the :mod:`camelot.types` module.
"""

import logging
logger = logging.getLogger('camelot.types')

import sqlalchemy
from sqlalchemy import types

SQLALCHEMY_MAJOR_VERSION = int(sqlalchemy.__version__.split('.')[1])

from camelot.core.files.storage import StoredFile, StoredImage, Storage

class VirtualAddress(types.TypeDecorator):
    """A single field that can be used to enter phone numbers, fax numbers, email
    addresses, im addresses.  The editor provides soft validation of the data
    entered.  The address or number is stored as a string in the database.
      
    This column type accepts and returns tuples of strings, the first string is
    the :attr:`virtual_address_type`, and the second the address itself.
  
    eg: ``('email','project-camelot@conceptive.be')`` is stored as
    ``email://project-camelot@conceptive.be``
  
    .. image:: /_static/virtualaddress_editor.png
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
    
    def result_processor(self, dialect, coltype=None):
      
        if SQLALCHEMY_MAJOR_VERSION >= 6:
            impl_processor = self.impl.result_processor(dialect, coltype)
        else:
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
    
    .. image:: /_static/editors/CodeEditor_editable.png
    
    :param parts: a list of input masks specifying the mask for each part,
    eg ``['99', 'AA']``. For valid input masks, see
    `QLineEdit <http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qlineedit.html>`_    
    """
    
    impl = types.Unicode
          
    def __init__(self, parts, separator=u'.', **kwargs):
        import string
        translator = string.maketrans('', '')
        self.parts = parts
        self.separator = separator
        max_length = sum(len(part.translate(translator, '<>!')) for part in parts) + len(parts)*len(self.separator)
        types.TypeDecorator.__init__(self, length=max_length, **kwargs)
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                value = self.separator.join(value)
            return impl_processor(value)
          
        return processor
    
    def result_processor(self, dialect, coltype=None):
      
        if SQLALCHEMY_MAJOR_VERSION >= 6:
            impl_processor = self.impl.result_processor(dialect, coltype)
        else:
            impl_processor = self.impl.result_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
      
        def processor(value):
    
            if value:
                return value.split(self.separator)
            return ['' for _p in self.parts]
            
        return processor
    
class IPAddress(Code):
    def __init__(self, **kwargs):
        super(IPAddress, self).__init__(parts=['900','900','900','900'])
    
class Rating(types.TypeDecorator):
    """The rating field is an integer field that is visualized as a number of stars that
  can be selected::
  
    class Movie( Entity ):
      title = Column( Unicode(60), nullable = False )
      rating = Column( camelot.types.Rating() )
      
  .. image:: /_static/editors/StarEditor_editable.png
"""
    
    impl = types.Integer
       
class RichText(types.TypeDecorator):
    """RichText fields are unlimited text fields which contain html. The html will be
  rendered in a rich text editor.  
  
    .. image:: /_static/editors/RichTextEditor_editable.png
"""
    
    impl = types.UnicodeText
     
class Language(types.TypeDecorator):
    """The languages are stored as a string in the database of 
the form *language*(_*country*), where :

 * *language* is a lowercase, two-letter, ISO 639 language code,
 * *territory* is an uppercase, two-letter, ISO 3166 country code
 
This used to be implemented using babel, but this was too slow and
used too much memory, so now it's implemented using QT.
    """
    
    impl = types.Unicode
    
    def __init__(self):
        types.TypeDecorator.__init__(self, length=20)
        
class Color(types.TypeDecorator):
    """The Color field returns and accepts tuples of the form (r,g,b,a) where
r,g,b,a are integers between 0 and 255. The color is stored as an hexadecimal
string of the form AARRGGBB into the database, where AA is the transparency, 
RR is red, GG is green BB is blue::
  
    class MovieType( Entity ):
        color = Column( camelot.types.Color() )

.. image:: /_static/editors/ColorEditor_editable.png  
  
The colors are stored in the database as strings.
  
Use::
    
    QColor(*color) 
    
to convert a color tuple to a QColor.
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
      
    def result_processor(self, dialect, coltype=None):
      
        if SQLALCHEMY_MAJOR_VERSION >= 6:
            impl_processor = self.impl.result_processor(dialect, coltype)
        else:
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
      title = Column( Unicode(60), nullable = False )
      state = Column( camelot.types.Enumeration([(1,'planned'), (2,'recording'), (3,'finished'), (4,'canceled')]), 
                      index = True, nullable = False, default = 'planning' )
  
  .. image:: /_static/editors/ChoicesEditor_editable.png  
  
  If None should be a possible value of the enumeration, add (None, None) to the list of
  possible enumerations.  None will be presented as empty in the GUI.
  
  :param choices: is a list of tuples.  each tuple contains an integer and its
  associated string.  such as :: 
  
      choices = [(1,'draft'), (2,'approved')]
  """
    
    impl = types.Integer
    
    def __init__(self, choices=[], **kwargs):
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
                    raise
            else:
                impl_processor(value)
                        
        return processor
    
    def result_processor(self, dialect, coltype=None):
      
        if SQLALCHEMY_MAJOR_VERSION >= 6:
            impl_processor = self.impl.result_processor(dialect, coltype)
        else:
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
                    raise
                
        return processor
    
class File(types.TypeDecorator):
    """Sqlalchemy column type to store files.  Only the location of the file is stored
    
  This column type accepts and returns a StoredFile. The name of the file is 
  stored as a string in the database.  A subdirectory upload_to can be specified::
  
    class Movie( Entity ):
      script = Column( camelot.types.File( upload_to = 'script' ) )
      
  .. image:: /_static/editors/FileEditor_editable.png
  
  Retrieving the actual storage from a File field can be a little cumbersome.
  The easy way is taking it from the field attributes, in which it will be
  put by default.  If no field attributes are available at the location where
  the storage is needed, eg in some function doing document processing, one 
  needs to go through SQLAlchemy to retrieve it.
  
  For an 'task' object  with a File field named 'document', the
  storage can be retrieved::
  
      from sqlalchemy import orm
      
      task_mapper = orm.object_mapper( task )
      document_property = task_mapper.get_property('document')
      storage = document_property.columns[0].type.storage

  :param max_length: the maximum length of the name of the file that will
  be saved in the database.

  :param upload_to: a subdirectory in the Storage, in which the the file
  should be stored.

  :param storage: an alternative storage to use for this field.

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
    
    def result_processor(self, dialect, coltype=None):
      
        if SQLALCHEMY_MAJOR_VERSION >= 6:
            impl_processor = self.impl.result_processor(dialect, coltype)
        else:
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
  specified by settings.CAMELOT_MEDIA_ROOT.  The name of the file is stored as a string in
  the database.
  
  The Image field type provides the same functionallity as the File field type, but
  the files stored should be images.
  
  .. image:: /_static/editors/ImageEditor_editable.png
    """
  
    stored_file_implementation = StoredImage
