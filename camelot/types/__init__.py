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

"""
Camelot extends the SQLAlchemy column types with a number of its own column
types. Those field types are automatically mapped to a specific delegate taking
care of the visualisation.

Those fields are stored in the :mod:`camelot.types` module.
"""
import collections
import logging

logger = logging.getLogger('camelot.types')



from sqlalchemy import types

from camelot.core.files.storage import StoredFile, Storage

"""
The `__repr__` method of the types is implemented to be able to use Alembic.
"""

class PrimaryKey(types.TypeDecorator):
    """Special type that can be used as the column type for a primary key.  This
    type defererring the definition of the actual type of primary key to
    compilation time.  This allows the changing of the primary key type through
    the whole model by changing the `options.DEFAULT_AUTO_PRIMARYKEY_TYPE`
    """
    
    impl = types.TypeEngine
    _type_affinity = types.Integer
    
    def load_dialect_impl(self, dialect):
        from camelot.core.orm import options
        return options.DEFAULT_AUTO_PRIMARYKEY_TYPE()
    
    @property
    def python_type(self):
        from camelot.core.orm import options
        return options.DEFAULT_AUTO_PRIMARYKEY_TYPE().python_type

    def __repr__(self):
        return 'PrimaryKey()'

virtual_address = collections.namedtuple('virtual_address',
                                        ['type', 'address'])

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
  
    @property
    def python_type(self):
        return virtual_address
    
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
      
        impl_processor = self.impl.result_processor(dialect, coltype)
        if not impl_processor:
            impl_processor = lambda x:x
      
        def processor(value):
    
            if value:
                split = value.split('://')
                if len(split)>1:
                    return virtual_address(*split)
            return virtual_address(u'phone',u'')
            
        return processor

    def __repr__(self):
        return 'VirtualAddress()'

    
class RichText(types.TypeDecorator):
    """RichText fields are unlimited text fields which contain html. The html will be
  rendered in a rich text editor.  
  
    .. image:: /_static/editors/RichTextEditor_editable.png
"""
    
    impl = types.UnicodeText
    
    @property
    def python_type(self):
        return self.impl.python_type

    def __repr__(self):
        return 'RichText()'

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
        
    @property
    def python_type(self):
        return self.impl.python_type

    def __repr__(self):
        return 'Language()'

class Color(types.TypeDecorator):
    """
    Colors are stored as hexidecimal color codes in the database.
    """

    impl = types.Unicode

    def __init__(self):
        types.TypeDecorator.__init__(self, length=7)

    @property
    def python_type(self):
        return self.impl.python_type

    def __repr__(self):
        return 'Color()'

class Enumeration(types.TypeDecorator):
    """The enumeration field stores integers in the database, but represents them as
  strings.  This allows efficient storage and querying while preserving readable code.
  
  Typical use of this field would be a status field.
  
  Enumeration fields are visualized as a combo box, where the labels in the combo
  box are the capitalized strings::
  
    class Movie(Entity):
      title = Column( Unicode(60), nullable = False )
      state = Column( camelot.types.Enumeration([(1,'planned'), (2,'recording'), (3,'finished'), (4,'canceled')]), 
                      index = True, nullable = False, default = 'planned' )
  
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
        self._string_to_int = dict((str_value,int_key) for (int_key,str_value) in choices)
        self.choices = [value for (_key,value) in choices]
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                try:
                    value = self._string_to_int[value]
                    return impl_processor(value)
                except KeyError as e:
                    logger.error('could not process enumeration value %s, possible values are %s'%(value, u', '.join(list(self._string_to_int.keys()))), exc_info=e)
                    raise
            else:
                impl_processor(value)
                        
        return processor
    
    def result_processor(self, dialect, coltype=None):
      
        impl_processor = self.impl.result_processor(dialect, coltype)
        if not impl_processor:
            impl_processor = lambda x:x
            
        def processor(value):
            if value is not None:
                value = impl_processor(value)
                try:
                    return self._int_to_string[value]
                except KeyError as e:
                    logger.error('could not process %s'%value, exc_info=e)
                    raise
                
        return processor
    
    @property
    def python_type(self):
        return str

    def __repr__(self):
        return 'Enumeration()'

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

    def __init__(self, storage=None, *, max_length=100, **kwargs):
        self.max_length = max_length
        self.storage = storage or Storage()
        types.TypeDecorator.__init__(self, length=max_length, **kwargs)
        
    def bind_processor(self, dialect):
  
        impl_processor = self.impl.bind_processor(dialect)
        if not impl_processor:
            impl_processor = lambda x:x
          
        def processor(value):
            if value is not None:
                assert isinstance(value, StoredFile)
                return impl_processor(value.name)
            return impl_processor(value)
          
        return processor
    
    def result_processor(self, dialect, coltype=None):
      
        impl_processor = self.impl.result_processor(dialect, coltype)
        if not impl_processor:
            impl_processor = lambda x:x
            
        def processor(value):
    
            if value:
                value = impl_processor(value)
                return StoredFile(self.storage, value)
              
        return processor
      
    @property
    def python_type(self):
        return self.impl.python_type

    def __repr__(self):
        return 'File()'

class Months(types.TypeDecorator):
    """
    Months fields are integer fields that represent a number of months.
    It will be rendered in the corresponding months editor.
    """

    impl = types.Integer

    @property
    def python_type(self):
        return self.impl.python_type

    def __repr__(self):
        return 'Months()'
