
from customeditor import CustomEditor, QtCore, QtGui
from wideeditor import WideEditor
from camelot.view.model_thread import post
from camelot.view.proxy import ValueLoading

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
                self.entity_instance_getter = create_instance_getter( self.admin.entity() )
                current_entity_admin = self.admin
            return True, propagate, current_entity_admin
      
        post( set_entity_instance, self.update_form )
    
    def update_form(self, update_form_and_propagate ):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        
        update_form, propagate, current_entity_admin = update_form_and_propagate

        if update_form:
            
            def create_collection_getter( instance_getter ):
                return lambda:[instance_getter()]
                        
            if self.model==None or self.model.get_admin()!=current_entity_admin:
                # We cannot reuse the current model and form
                if self.form:
                    self.form.deleteLater()
                    self.layout.removeWidget( self.form )

                self.model = CollectionProxy( current_entity_admin,
                                              create_collection_getter( self.entity_instance_getter ),
                                              current_entity_admin.get_fields )
                self.form = current_entity_admin.create_form_view( '', self.model, 0, self )
                self.layout.addWidget( self.form )
            else:
                # We can reuse the form, just update the content of the collection
                self.model.set_collection_getter(create_collection_getter( self.entity_instance_getter ))
            
        if propagate:
            self.emit( QtCore.SIGNAL( 'editingFinished()' ) )
