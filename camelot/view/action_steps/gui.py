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

"""
Various ``ActionStep`` subclasses that manipulate the GUI of the application.
"""

from PyQt4 import QtGui

from camelot.admin.action.base import ActionStep

class OpenFormView( ActionStep ):
    """Open the form view for a list of objects, in a non blocking way
    :param objects: the list of objects to display in the form view
    :param admin: the admin class to use to display the form    
    """
    
    blocking = False
    
    def __init__( self, objects, admin ):
        self.objects = objects
        self.admin = admin
        
        
    def gui_run( self, gui_context ):
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.view.workspace import show_top_level

        def create_collection_getter( objects ):
            return lambda:objects
        
        model = CollectionProxy(
            self.admin,
            create_collection_getter(self.objects),
            self.admin.get_fields,
            max_number_of_rows=10
        )
        title = ''
        formview = self.admin.create_form_view(
            title, model, 0
        )
        show_top_level( formview, gui_context.workspace )    
    
class Refresh( ActionStep ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""
    
    def gui_run( self, gui_context ):
        gui_context.workspace.refresh()


class ShowChart( ActionStep ):
    """Show a full screen chart.
    
    :param chart: a :class:`camelot.core.container.FigureContainer` or
        :class:`camelot.core.container.AxesContainer`
    """
        
    def __init__( self, chart ):
        self.chart = chart
        
    def gui_run( self, gui_context ):
        from camelot.view.controls.editors import ChartEditor
        ChartEditor.show_fullscreen_chart( self._chart, 
                                           gui_context.workspace )

    
class ShowPixmap( ActionStep ):
    """Show a full screen pixmap
    
    :param pixmap: a :class:`camelot.view.art.Pixmap` object
    """
    
    def __init__( self, pixmap ):
        self.pixmap = pixmap
        
    def gui_run( self, gui_context ):
        from camelot.view.controls.liteboxview import LiteBoxView
        litebox = LiteBoxView( parent = gui_context.workspace )
        litebox.show_fullscreen_pixmap( self.pixmap.getQPixmap() )
        
class CloseView( ActionStep ):
    """
    Close the view that triggered the action, if such a view is available.
    
    :param accept: a boolean indicating if the view's widget should accept the
        close event.  This defaults to :keyword:`True`, when this is set to 
        :keyword:`False`, the view will trigger it's corresponding close action
        instead of accepting the close event.  The close action might involve
        validating if the view can be closed, or requesting confirmation from
        the user.
    """

    def __init__( self, accept = True ):
        self.accept = accept
        
    def gui_run( self, gui_context ):
        view = gui_context.view
        if view != None:
            view.close_view( self.accept )

class MessageBox( ActionStep ):
    """
    Popup a :class:`QtGui.QMessageBox` and send it result back.  The arguments
    of this action are the same as those of the :class:`QtGui.QMessageBox`
    constructor.
    
    :param icon: one of the :class:`QtGui.QMessageBox.Icon` constants
    :param title: the window title of the message box
    :param text: the text to be displayed within the message box
    :param standard_buttons: the buttons to be displayed on the message box,
        out of the :class:`QtGui.QMessageBox.StandardButton` enumeration. by 
        default only an :label:`Ok` button will be shown.
    """
    
    def __init__( self,
                  icon, 
                  title, 
                  text, 
                  standard_buttons =  QtGui.QMessageBox.Ok ):
        self.icon = icon
        self.title = unicode( title )
        self.text = unicode( text )
        self.standard_buttons = standard_buttons
        
    def gui_run( self, gui_context ):
        message_box = QtGui.QMessageBox( self.icon,
                                         self.title,
                                         self.text,
                                         self.standard_buttons )
        return message_box.exec_()
