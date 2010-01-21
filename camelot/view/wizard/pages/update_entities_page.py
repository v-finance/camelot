'''
Created on Jan 18, 2010

@author: tw55413
'''

from progress_page import ProgressPage

class UpdateEntitiesPage(ProgressPage):
    """A progress page that updates each entity in a collection,
    then flushes the entity, and informs all views that the entity
    has been updated.  Subclass this page and implement update_entity
    to make this page do something.
    """
    
    def __init__(self, collection_getter, parent):
        super(UpdateEntitiesPage, self).__init__( parent )
        self._wizard = parent
        self._collection_getter = collection_getter
    
    def update_entity(self, entity):
        """Implement this method to update the entities in the 
        collection.
        
        :param entity: the entity that should be updated
        :return: None or a string that will be displayed in the progress
        screen.
        """
        pass
    
    def run(self):
        from sqlalchemy.orm.session import Session
        from camelot.view.remote_signals import get_signal_handler
        signal_handler = get_signal_handler()
        collection = list(self._collection_getter())
        self.emit(self.update_maximum_signal, len(collection))
        for i, entity in enumerate(collection):
            message = self.update_entity(entity)
            Session.object_session( entity ).flush( [entity] )
            signal_handler.sendEntityUpdate( self, entity )
            self.emit(self.update_progress_signal, i, message)