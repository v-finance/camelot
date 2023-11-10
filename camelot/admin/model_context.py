from ..core.cache import ValueCache
from .action.application_action import ApplicationActionModelContext


class ObjectsModelContext(ApplicationActionModelContext):
    """On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`, 
    this context contains :
        
    .. attribute:: selection_count
    
        the number of selected rows.
        
    .. attribute:: collection_count
    
        the number of rows in the list.
        
    .. attribute:: selected_rows
    
        an ordered list with tuples of selected row ranges.  the range is
        inclusive.
        
    .. attribute:: current_row
    
        the current row in the list if a cell is active
    
    .. attribute:: current_column
    
        the current column in the table if a cell is active
    
    .. attribute:: current_field_name
    
        the name of the field displayed in the current column
        
    .. attribute:: session
    
        The session to which the objects in the list belong.

    .. attribute:: proxy

        A :class:`camelot.core.item_model.AbstractModelProxy` object that gives
        access to the objects in the list

    .. attribute:: field_attributes
    
        The field attributes of the field to which the list relates, for example
        the attributes of Person.addresses if the list is the list of addresses
        of the Person.
       
    The :attr:`collection_count` and :attr:`selection_count` attributes allow the 
    :meth:`model_run` to quickly evaluate the size of the collection or the
    selection without calling the potentially time consuming methods
    :meth:`get_collection` and :meth:`get_selection`.
    """
    
    def __init__(self, admin, proxy, locale):
        super().__init__(admin)
        self.proxy = proxy
        self.locale = locale
        self.edit_cache = ValueCache(100)
        self.attributes_cache = ValueCache(100)
        self.static_field_attributes = []
        self.current_row = None
        self.current_column = None
        self.current_field_name = None
        self.selection_count = 0
        self.collection_count = 0
        self.selected_rows = []
        self.field_attributes = dict()
        # self.obj = None
        # todo : remove the concept of a validator (taken from CollectionProxy)
        self.validator = admin.get_validator()

    def get_selection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects selected
        """
        # during deletion or duplication, the collection might
        # change, while the selection remains the same, so we should
        # be careful when using the collection to generate selection data
        for (first_row, last_row) in self.selected_rows:
            for obj in self.proxy[first_row:last_row + 1]:
                yield obj

    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self.proxy[0:self.collection_count]:
            yield obj
            
    def get_object( self, row = None ):
        """
        :param row: The row for the object to get.
        :return: The object for the specified row. If the specified row is None, the object
            displayed in the current row or None is returned.
        """
        if row is None:
            row = self.current_row
        if row != None:
            for obj in self.proxy[row:row+1]:
                return obj