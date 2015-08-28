#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
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

        objects = self.objects
        if objects is None:
            related_model = gui_context.item_view.model()
            # Always create a simple collection proxy, even if the original model
            # was a query proxy, since relating two models to each other and
            # making sure the correct row is shown in the form involves too many
            # edge cases.
            related_row = gui_context.item_view.currentIndex().row()
            obj = related_model.headerData(related_row, Qt.Vertical, ObjectRole)
            objects = [variant_to_py(obj)]
            row = 0
        else:
            row = self.row

        model = CollectionProxy(self.admin, max_number_of_rows=10)
        model.set_columns(self._columns)
        model.set_value(objects)

        form = FormView(title=self.title, admin=self.admin, model=model,
                        columns=self._columns, form_display=self._form_display,
                        index=row)
        form.set_actions(self.actions)
        form.set_toolbar_actions(self.top_toolbar_actions)
        self.admin._apply_form_state( form )
        return form

    def gui_run( self, gui_context ):
        window = gui_context.get_window()
        formview = self.render(gui_context)
        show_top_level(formview, window)

class ToFirstForm( ActionStep ):
    """
    Show the first object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toFirst()

class ToNextForm( ActionStep ):
    """
    Show the next object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toNext()
        
class ToLastForm( ActionStep ):
    """
    Show the last object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toLast()
        
class ToPreviousForm( ActionStep ):
    """
    Show the previous object in the collection in the current form
    """

    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toPrevious()
