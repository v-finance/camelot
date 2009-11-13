from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from camelot.view.controls import editors
from camelot.core.utils import variant_to_pyobject

import logging
logger = logging.getLogger( 'camelot.view.controls.delegates.one2manydelegate' )

class One2ManyDelegate( QtGui.QItemDelegate ):
    """Custom delegate for many 2 one relations
  
  .. image:: ../_static/onetomany.png  
  """

    def __init__( self, parent = None, **kwargs ):
        logger.debug( 'create one2manycolumn delegate' )
        assert 'delegate' in kwargs
        QtGui.QItemDelegate.__init__( self, parent )
        self.kwargs = kwargs

    def createEditor( self, parent, option, index ):
        logger.debug( 'create a one2many editor' )
        editor = editors.One2ManyEditor( parent = parent, **self.kwargs )
        self.setEditorData( editor, index )
        return editor

    def setEditorData( self, editor, index ):
        logger.debug( 'set one2many editor data' )
        model = variant_to_pyobject( index.data( Qt.EditRole ) )
        editor.set_value( model )

    def setModelData( self, editor, model, index ):
        pass
