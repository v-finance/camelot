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
Various ``ActionStep`` subclasses to create and manipulate a form view in the
context of the `Qt` model-view-delegate framework.
"""

from ...admin.action.base import ActionStep
from ...core.qt import Qt, variant_to_py
from ..workspace import show_top_level
from ..proxy.collection_proxy import ObjectRole, CollectionProxy

class OpenFormView( ActionStep ):
    """Open the form view for a list of objects, in a non blocking way.

    :param objects: the list of objects to display in the form view, if objects
        is set to `None`, the model of the item view of the gui context is
        reused
        
    :param admin: the admin class to use to display the form

    .. attribute:: row

        Which object to display when opening the form, defaults to the first
        object, so row is 0 by default

    .. attribute:: actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the side of the form, this defaults to the ones returned by the
        admin

    .. attribute:: top_toolbar_actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the top toolbar of the form, this defaults to the ones returned by the
        admin
    """

    def __init__( self, objects, admin ):
        self.objects = objects
        self.admin = admin
        self.row = 0
        self.actions = admin.get_form_actions(None)
        get_form_toolbar_actions = admin.get_form_toolbar_actions
        self.top_toolbar_actions = get_form_toolbar_actions(Qt.TopToolBarArea)
        self.title = u' '
        self._columns = admin.get_fields()
        self._form_display = admin.get_form_display()

    def get_objects( self ):
        """Use this method to get access to the objects to change in unit tests

        :return: the list of objects to display in the form view
        """
        return self.objects

    def render(self, gui_context):
        from camelot.view.controls.formview import FormView
        if self.objects is None:
            related_model = gui_context.item_view.model()
            proxy = related_model.get_value().copy()
            # Always create a new proxy
            # relating two views on the same model to each other and
            # making sure the correct row is shown in the form involves too many
            # edge cases.
            # this is the row the user clicked on
            related_row = gui_context.item_view.currentIndex().row()
            # this is the object visible in that row at the time of the click
            obj = related_model.headerData(related_row, Qt.Vertical, ObjectRole)
            # the value for the ObjectRole might be None if the update of the
            # model is still pending, in that case no form can be opened yet
            if variant_to_py(obj) is None:
                return None
            # this is the row in the new proxy for the same object, this migth
            # be the same row as the related row if there were no gui changes
            # pending
            row = proxy.index(variant_to_py(obj))
        else:
            row = self.row
            proxy = self.admin.get_proxy(self.objects)

        model = CollectionProxy(self.admin, max_number_of_rows=10)
        list(model.add_columns((fn for fn, fa in self._columns)))
        model.set_value(proxy)

        form = FormView(title=self.title, admin=self.admin, model=model,
                        columns=self._columns, form_display=self._form_display,
                        index=row)
        form.set_actions(self.actions)
        form.set_toolbar_actions(self.top_toolbar_actions)
        return form

    def gui_run( self, gui_context ):
        window = gui_context.get_window()
        formview = self.render(gui_context)
        if formview is not None:
            show_top_level(formview, window, self.admin.form_state)

class ChangeFormIndex(ActionStep):

    def gui_run( self, gui_context ):
        # a pending request might change the number of rows, and therefor
        # the new index
        # submit all pending requests to the model thread
        gui_context.widget_mapper.model().timeout_slot()
        # wait until they are handled
        super(ChangeFormIndex, self).gui_run(gui_context)

class ToFirstForm(ChangeFormIndex):
    """
    Show the first object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToFirstForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toFirst()

class ToNextForm(ChangeFormIndex):
    """
    Show the next object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToNextForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toNext()
        
class ToLastForm(ChangeFormIndex):
    """
    Show the last object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToLastForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toLast()
        
class ToPreviousForm(ChangeFormIndex):
    """
    Show the previous object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        super(ToPreviousForm, self).gui_run(gui_context)
        gui_context.widget_mapper.toPrevious()

