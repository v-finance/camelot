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

"""ModelContext, GuiContext and Actions that are used in the context of
editing a document.
"""

from .base import Action
from .application_action import ( ApplicationActionGuiContext, 
                                  ApplicationActionModelContext )
from ...core.utils import ugettext_lazy as _
from ...view.art import FontIcon

class DocumentActionModelContext( ApplicationActionModelContext ):
    
    def __init__( self ):
        super( DocumentActionModelContext, self ).__init__()
        self.document = None
    
class DocumentActionGuiContext( ApplicationActionGuiContext ):
    """The GUI context for an :class:`camelot.admin.action.ApplicationActionGuiContext`.
    On top of  the attributes of the 
    :class:`camelot.admin.action.base.ApplicationActionGuiContext`, this context 
    contains :
    
    .. attribute:: document
    
        the :class:`QtGui.QTextDocument` upon which this action is acting

    .. attribute:: view
    
        the view that displays the document
        
    """
    
    model_context = DocumentActionModelContext
    
    def __init__( self ):
        super( DocumentActionGuiContext, self ).__init__()
        self.document = None
        self.view = None
        
    def copy( self, base_class=None ):
        new_context = super( DocumentActionGuiContext, self ).copy( base_class )
        new_context.document = self.document
        new_context.view = self.view
        return new_context
    
    def create_model_context( self ):
        context = super( DocumentActionGuiContext, self ).create_model_context()
        context.document = self.document
        return context
    
class EditDocument( Action ):
    
    verbose_name = _('Edit')
    icon = FontIcon('edit') # 'tango/16x16/apps/accessories-text-editor.png'
    tooltip = _('Edit this document')
    
    def model_run( self, model_context ):
        from ...view import action_steps
        edit = action_steps.EditTextDocument(model_context.document)
        yield edit
        yield action_steps.UpdatePrintPreview()

