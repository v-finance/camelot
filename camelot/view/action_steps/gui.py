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
Various ``ActionStep`` subclasses that manipulate the GUI of the application.
"""

from PyQt4 import QtGui, QtCore

from camelot.admin.action.base import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext_lazy as _
from camelot.view.controls import editors
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage

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
        if gui_context.workspace:
            gui_context.workspace.refresh()

class ItemSelectionDialog(StandaloneWizardPage):

    def __init__( self, 
                  window_title=None,
                  autoaccept=False,
                  parent=None):
        """
        :param autoaccept: if True, the value of the ComboBox is immediately
        accepted after selecting it.
        """
        super(ItemSelectionDialog, self).__init__( window_title = window_title, 
                                                   parent = parent ) 
        self.autoaccept = autoaccept
        self.set_default_buttons()
        layout = QtGui.QVBoxLayout()
        combobox = editors.ChoicesEditor()
        combobox.setObjectName( 'combobox' )
        combobox.activated.connect( self._combobox_activated )
        layout.addWidget( combobox )
        self.main_widget().setLayout(layout)

    @QtCore.pyqtSlot(int)
    def _combobox_activated(self, index):
        if self.autoaccept:
            self.accept()

    def set_choices(self, choices):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            combobox.set_choices(choices)
            
    def get_value(self):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.get_value()            

    def set_value(self, value):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.set_value(value)
    
class SelectItem( ActionStep ):
    """This action step pops up a single combobox dialog in which the user can
    select one item from a list of items.
    
    :param items: a list of tuples with values and the visible name of the items
       from which the user can select, such as `[(1, 'first'), (2,'second')]
    :param value: the value that should be selected when the dialog pops up
    :param autoaccept: if `True` the dialog closes immediately after the user
       selected an option.  When this is `False`, the user should press
       :guilabel:`OK` first.
    """
    
    def __init__( self, items, value=None ):
        self.items = items
        self.value = value
        self.autoaccept = True
        self.title =  _('Please select')
        self.subtitle = _('Make a selection and press the OK button')
        
    def render(self):
        dialog = ItemSelectionDialog( autoaccept = self.autoaccept )
        dialog.set_choices(self.items)
        dialog.set_value(self.value)
        dialog.setWindowTitle( unicode( self.title ) )
        dialog.set_banner_subtitle( unicode( self.subtitle ) )
        return dialog
    
    def gui_run(self, gui_context):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return dialog.get_value()
    
class ShowChart( ActionStep ):
    """Show a full screen chart.
    
    :param chart: a :class:`camelot.container.chartcontainer.FigureContainer` or
        :class:`camelot.container.chartcontainer.AxesContainer`
    """
        
    def __init__( self, chart ):
        self.chart = chart
        
    def gui_run( self, gui_context ):
        from camelot.view.controls.editors import ChartEditor
        ChartEditor.show_fullscreen_chart( self.chart, 
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
        close event.  This defaults to :const:`True`, when this is set to 
        :const:`False`, the view will trigger it's corresponding close action
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
    
    :param text: the text to be displayed within the message box
    :param icon: one of the :class:`QtGui.QMessageBox.Icon` constants
    :param title: the window title of the message box
    :param standard_buttons: the buttons to be displayed on the message box,
        out of the :class:`QtGui.QMessageBox.StandardButton` enumeration. by 
        default an :guilabel:`Ok` and a button :guilabel:`Cancel` will be shown.
        
    When the :guilabel:`Cancel` button is pressed, this action step will raise
    a `CancelException`
        
    .. image:: /_static/listactions/import_from_file_confirmation.png
    
    """
    
    default_buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel
    
    def __init__( self,
                  text, 
                  icon = QtGui.QMessageBox.Information, 
                  title = _('Message'), 
                  standard_buttons = default_buttons ):
        self.icon = icon
        self.title = unicode( title )
        self.text = unicode( text )
        self.standard_buttons = standard_buttons
        
    def render( self ):
        """create the message box. this method is used to unit test
        the action step."""
        return QtGui.QMessageBox( self.icon,
                                  self.title,
                                  self.text,
                                  self.standard_buttons )
        
    def gui_run( self, gui_context ):
        message_box = self.render()
        result = message_box.exec_()
        if result == QtGui.QMessageBox.Cancel:
            raise CancelRequest()
        return result

