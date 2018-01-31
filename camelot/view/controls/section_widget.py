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

"""left navigation pane"""

import logging
logger = logging.getLogger('camelot.view.controls.section_widget')

import six

from ...core.qt import variant_to_py, QtCore, QtWidgets, Qt, qt_api
from camelot.admin.action.application_action import ApplicationActionGuiContext
from camelot.admin.section import Section, SectionItem
from camelot.view.model_thread import post
from camelot.view.controls.modeltree import ModelItem
from camelot.view.controls.modeltree import ModelTree

class PaneSection(QtWidgets.QWidget):

    def __init__(self, parent, section, workspace):
        super(PaneSection, self).__init__(parent)
        self._items = []
        self._workspace = workspace
        self._section = section
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        section_tree = ModelTree(parent=self)
        # i hate the sunken frame style
        section_tree.setFrameShape(QtWidgets.QFrame.NoFrame)
        section_tree.setFrameShadow(QtWidgets.QFrame.Plain)
        section_tree.contextmenu = QtWidgets.QMenu(self)
        section_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        section_tree.customContextMenuRequested.connect(self.create_context_menu)
        section_tree.setObjectName( 'SectionTree' )
        section_tree.itemClicked.connect( self._item_clicked )
        section_tree.setWordWrap( False )
        layout.addWidget( section_tree )
        self.setLayout(layout)
        post( section.get_items, self.set_items )

    @QtCore.qt_slot(object)
    def set_items(self, items, parent = None):
        logger.debug('setting items for current navpane section')
        section_tree = self.findChild(QtWidgets.QWidget, 'SectionTree')
        if section_tree:
            if parent == None:
                # take a copy, so the copy can be extended
                self._items = list(i for i in items)
                section_tree.clear()
                section_tree.clear_model_items()
                parent = section_tree
    
            if not items: return
    
            for item in items:
                label = item.get_verbose_name()
                icon = item.get_icon()
                model_item = ModelItem( parent, 
                                        [six.text_type(label)],
                                        item )
                if icon:
                    model_item.set_icon(icon.getQIcon())
                section_tree.modelitems.append( model_item )
                if isinstance( item, Section ):
                    child_items = item.get_items()
                    self.set_items( child_items, parent = model_item )
                    self._items.extend( child_items )
                    
            section_tree.resizeColumnToContents( 0 )

    def create_context_menu(self, point):
        logger.debug('creating context menu')
        section_tree = self.findChild(QtWidgets.QWidget, 'SectionTree')
        if section_tree:
            item = section_tree.itemAt(point)
            if item:
                section_tree.contextmenu.clear()
                for mode in item.section_item.get_modes():
                    action = mode.render( self )
                    action.triggered.connect( self._action_triggered )
                    section_tree.contextmenu.addAction( action )
                section_tree.setCurrentItem(item)
                section_tree.contextmenu.popup(section_tree.mapToGlobal(point))

    @QtCore.qt_slot(bool)
    def _action_triggered( self, _checked ):
        action = self.sender()
        mode_name = variant_to_py( action.data() )
        self._run_current_action( mode_name )
        
    @QtCore.qt_slot(QtWidgets.QTreeWidgetItem, int)
    def _item_clicked(self, _item, _column):
        self._run_current_action()

    def _run_current_action( self, mode_name=None ):
        section_tree = self.findChild(QtWidgets.QWidget, 'SectionTree')
        if section_tree:
            item = section_tree.currentItem()
            index = section_tree.indexFromItem(item)
            parent = index.parent()
            if parent.row() >= 0:
                section = self._items[parent.row()]
                section_item = section.items[index.row()]
            else:
                section_item = self._items[index.row()]
            if not isinstance( section_item, SectionItem ):
                return
            gui_context = ApplicationActionGuiContext()
            gui_context.mode_name = mode_name
            gui_context.workspace = self._workspace
            gui_context.admin = self._section.admin
            section_item.get_action().gui_run( gui_context )
                        
class NavigationPane(QtWidgets.QDockWidget):

    def __init__(self, workspace, parent):
        super(NavigationPane, self).__init__(parent)
        self._workspace = workspace
        tb = QtWidgets.QToolBox()
        tb.setMinimumWidth(220)
        tb.setFrameShape(QtWidgets.QFrame.NoFrame)
        tb.layout().setContentsMargins(0,0,0,0)
        tb.layout().setSpacing(1)
        tb.setObjectName('toolbox')
        tb.setMouseTracking(True)
        
        # hack for removing the dock title bar
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWidget(tb)
        self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)

    def wheelEvent(self, wheel_event):
        if qt_api=='PyQt5':
            steps = -1 * wheel_event.angleDelta().y() / (8 * 15)
        else:
            steps = -1 * wheel_event.delta() / (8 * 15)
        toolbox = self.findChild(QtWidgets.QWidget, 'toolbox')
        if steps and toolbox:
            current_index = toolbox.currentIndex()
            toolbox.setCurrentIndex( max( 0, min( current_index + steps, toolbox.count() ) ) )

    @QtCore.qt_slot(object)
    def set_sections(self, sections):
        logger.debug('setting navpane sections')
        if not sections:
            self.setMaximumWidth(0)
            return
        toolbox = self.findChild(QtWidgets.QWidget, 'toolbox')

        # performs QToolBox clean up
        # QToolbox won't delete items we have to do it explicitly
        count = toolbox.count()
        while count:
            item = toolbox.widget(count-1)
            toolbox.removeItem(count-1)
            item.deleteLater()
            count -= 1
            
        for section in sections:
            # TODO: old navpane used translation here
            name = six.text_type( section.get_verbose_name() )
            icon = section.get_icon().getQIcon()
            pwdg = PaneSection(toolbox, section, self._workspace)
            toolbox.addItem(pwdg, icon, name)

        toolbox.setCurrentIndex(0)
        # WARNING: hardcoded width
        #self._toolbox.setMinimumWidth(220)




