#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

import logging
logger = logging.getLogger('camelot.view.controls.editors.embeddedmany2oneeditor')

from customeditor import CustomEditor, QtCore, QtGui
from wideeditor import WideEditor
from camelot.view.model_thread import post
from camelot.view.proxy import ValueLoading
from camelot.core.utils import CollectionGetterFromObjectGetter


class EmbeddedMany2OneEditor( CustomEditor, WideEditor ):
    """Widget for editing a many 2 one relation a a form embedded in another
  form.
  """

    def __init__( self, admin = None, parent = None, **kwargs ):
        assert admin != None
        CustomEditor.__init__( self, parent )
        self.admin = admin
        #
        # The admin class of the current entity can be different from
        # self.admin, since the current entity can be a subclass of
        # the entity for which self.admin was made
        #
        self.current_entity_admin = None
        self.layout = QtGui.QHBoxLayout()
        self.entity_instance_getter = None
        self.form = None
        self.model = None
        self.setLayout( self.layout )
        self.setEntity( lambda:ValueLoading, propagate = False )

    def set_value( self, value ):
        value = CustomEditor.set_value( self, value )
        if value:
            self.setEntity( value, propagate = False )

    def set_field_attributes(self, **kwargs):
        pass

    def setEntity( self, entity_instance_getter, propagate = True ):

        def create_instance_getter( entity_instance ):
            return lambda:entity_instance

        def set_entity_instance():
            entity = entity_instance_getter()
            current_entity_admin = None
            if entity:
                if entity!=ValueLoading:
                    self.entity_instance_getter = create_instance_getter( entity )
                    current_entity_admin = self.admin.get_related_entity_admin( entity.__class__ )
                else:
                    return False, False, current_entity_admin
            else:
                try:
                    new_entity = self.admin.entity()
                except Exception, e:
                    logger.error('ProgrammingError : could not create a new entity of type %s'%(self.admin.entity.__name__), exc_info=e)
                self.entity_instance_getter = create_instance_getter( new_entity )
                current_entity_admin = self.admin
            return True, propagate, current_entity_admin

        post( set_entity_instance, self.update_form )

    def update_form(self, update_form_and_propagate ):
        from camelot.view.proxy.collection_proxy import CollectionProxy

        update_form, propagate, current_entity_admin = update_form_and_propagate

        if update_form:

            if self.model==None or self.model.get_admin()!=current_entity_admin:
                # We cannot reuse the current model and form
                if self.form:
                    self.form.deleteLater()
                    self.layout.removeWidget( self.form )

                self.model = CollectionProxy( current_entity_admin,
                                              CollectionGetterFromObjectGetter( self.entity_instance_getter ),
                                              current_entity_admin.get_fields )
                self.form = current_entity_admin.create_form_view( '', self.model, 0, self )
                self.layout.addWidget( self.form )
            else:
                # We can reuse the form, just update the content of the collection
                self.model.set_collection_getter(CollectionGetterFromObjectGetter( self.entity_instance_getter ))

        if propagate:
            self.emit( QtCore.SIGNAL( 'editingFinished()' ) )
