#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
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
        self.update_maximum_signal.emit( len(collection) )
        for i, entity in enumerate(collection):
            message = self.update_entity(entity)
            Session.object_session( entity ).flush( [entity] )
            signal_handler.sendEntityUpdate( self, entity )
            self.update_progress_signal.emit( i, message or '')


