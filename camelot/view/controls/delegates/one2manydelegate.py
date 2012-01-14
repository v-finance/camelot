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
from PyQt4.QtCore import Qt

from camelot.view.controls import editors
from customdelegate import CustomDelegate, DocumentationMetaclass
from camelot.core.utils import variant_to_pyobject

import logging
logger = logging.getLogger( 'camelot.view.controls.delegates.one2manydelegate' )

class One2ManyDelegate( CustomDelegate ):
    """Custom delegate for many 2 one relations
  
  .. image:: /_static/onetomany.png
  """

    __metaclass__ = DocumentationMetaclass

    def __init__( self, parent = None, **kwargs ):
        super( One2ManyDelegate, self ).__init__( parent=parent, **kwargs )
        logger.debug( 'create one2manycolumn delegate' )
        self.kwargs = kwargs

    def createEditor( self, parent, option, index ):
        logger.debug( 'create a one2many editor' )
        editor = editors.One2ManyEditor( parent = parent, **self.kwargs )
        self.setEditorData( editor, index )
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def setEditorData( self, editor, index ):
        logger.debug( 'set one2many editor data' )
        model = variant_to_pyobject( index.data( Qt.EditRole ) )
        editor.set_value( model )
        field_attributes = variant_to_pyobject(index.data(Qt.UserRole))
        editor.set_field_attributes(**field_attributes)

    def setModelData( self, editor, model, index ):
        pass

