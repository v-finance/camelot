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
"""
Camelot unittest framework.  This module contains helper classes and functions
to write unittests for Camelot applications.  These are not the unittests for
Camelot itself.  Those can be found in the /test folder, at the same position 
as /camelot.
"""

import unittest

has_programming_error = False

_application_ = []

def get_application():
    """Get the singleton QApplication"""
    from PyQt4.QtGui import QApplication
    if not len(_application_):
        #
        # Uniform style for screenshot generation
        #
        application = QApplication.instance()
        if not application:
            import sys
            from camelot.view import art
            QApplication.setStyle('cleanlooks')
            application = QApplication(sys.argv)
            application.setStyleSheet( art.read('stylesheet/office2007_blue.qss') )
            from PyQt4 import QtCore
            QtCore.QLocale.setDefault( QtCore.QLocale('nl_BE') )
            #try:
            #    from PyTitan import QtnOfficeStyle
            #    QtnOfficeStyle.setApplicationStyle( QtnOfficeStyle.Windows7Scenic )
            #except:
            #    pass 
        _application_.append( application )
    return _application_[0]

class ModelThreadTestCase(unittest.TestCase):
    """Base class for implementing test cases that need a running model_thread.
    """

    images_path = ''

    def grab_widget(self, widget, suffix=None, subdir=None):
        """Save a widget as a png file :
    :param widget: the widget to take a screenshot of
    :param suffix: string to add to the default filename of the image
    :param subdir: subdirectory of images_path in which to put the image file, defaults to
    the name of the test class
    - the name of the png file is the name of the test case, without 'test_'
    - it is stored in the directory with the same name as the class, without 'test'
        """
        import sys
        import os
        from PyQt4 import QtGui
        from PyQt4.QtGui import QPixmap
        if not subdir:
            images_path = os.path.join(self.images_path, self.__class__.__name__.lower()[:-len('Test')])
        else:
            images_path = os.path.join(self.images_path, subdir)
        if not os.path.exists(images_path):
            os.makedirs(images_path)
        
        # try to move up in the stack until we find a test method
        for i in range(1, 10):
            if sys._getframe(i).f_code.co_name.startswith('test'):
                break
            
        test_case_name = sys._getframe(i).f_code.co_name[5:]
        image_name = '%s.png'%test_case_name
        if suffix:
            image_name = '%s_%s.png'%(test_case_name, suffix)
        widget.adjustSize()
        widget.repaint()
        self.process()
        QtGui.QApplication.flush()
        inner_pixmap = QPixmap.grabWidget(widget)        
        #
        # we'll create a label that contains a screenshot of our widget and
        # take a screenshot of that label, for the sole purpose of adding a border
        #
        parent_widget = QtGui.QLabel()
        parent_widget.setPixmap(inner_pixmap)
        parent_widget.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        parent_widget.setObjectName('grab_widget_parent')
        parent_widget.setLineWidth(2)
        parent_widget.setStyleSheet("""
        #grab_widget_parent {
        border: 2px solid gray;
        }""")
        parent_widget.adjustSize()
        outer_pixmap = QPixmap.grabWidget(parent_widget)
        outer_pixmap.save(os.path.join(images_path, image_name), 'PNG')

    def process(self):
        """Wait until all events are processed and the queues of the model thread are empty"""
        self.mt.wait_on_work()

    def setUp(self):
        self.app = get_application()
        from camelot.view import model_thread
        from camelot.view.model_thread.no_thread_model_thread import NoThreadModelThread
        from camelot.view.model_thread import get_model_thread, has_model_thread
        from camelot.view.remote_signals import construct_signal_handler, has_signal_handler
        if not has_model_thread():
            #
            # Run the tests without real threading, to avoid timing problems with screenshots etc.
            #
            model_thread._model_thread_.insert( 0, NoThreadModelThread() )
        if not has_signal_handler():
            construct_signal_handler()
        self.mt = get_model_thread()
        if not self.mt.isRunning():
            self.mt.start()
        # make sure the startup sequence has passed
        self.process()

    def tearDown(self):
        self.process()
        #self.mt.exit(0)
        #self.mt.wait()

class ApplicationViewsTest(ModelThreadTestCase):
    """Test various application level views, like the main window, the
    sidepanel"""
        
    def get_application_admin(self):
        """Overwrite this method to make use of a custom application admin"""
        from camelot.admin.application_admin import ApplicationAdmin
        return ApplicationAdmin()
        
    def test_navigation_pane(self):
        from camelot.view.controls import navpane2
        from PyQt4 import QtCore
        translator = self.get_application_admin().get_translator()
        QtCore.QCoreApplication.installTranslator(translator)         
        app_admin = self.get_application_admin()
        nav_pane = navpane2.NavigationPane(app_admin, None, None)
        self.grab_widget(nav_pane, subdir='applicationviews')
        for i, section in enumerate(nav_pane.get_sections()):
            nav_pane.change_current((i, unicode(section.get_verbose_name())))
            self.grab_widget(nav_pane, suffix=section.get_name(), subdir='applicationviews')
      
    def test_main_window(self):
        from camelot.view.mainwindow import MainWindow
        from PyQt4 import QtCore
        translator = self.get_application_admin().get_translator()
        QtCore.QCoreApplication.installTranslator(translator)          
        app_admin = self.get_application_admin()        
        widget = MainWindow(app_admin)
        self.grab_widget(widget, subdir='applicationviews')
        
    def test_tool_bar(self):
        from camelot.view.mainwindow import MainWindow
        from PyQt4 import QtCore
        translator = self.get_application_admin().get_translator()
        QtCore.QCoreApplication.installTranslator(translator)        
        app_admin = self.get_application_admin()        
        main_window = MainWindow(app_admin)
        self.grab_widget(main_window.get_tool_bar(), subdir='applicationviews')
    
class EntityViewsTest(ModelThreadTestCase):
    """Test the views of all the Entity subclasses, subclass this class to test all views
    in your application.  This is done by calling the create_table_view and create_new_view
    on a set of admin objects.  To tell the test case which admin objects should be tested,
    overwrite the get_admins method.
    """

    def setUp(self):
        super(EntityViewsTest, self).setUp()
        from PyQt4 import QtCore
        global has_programming_error
        translators = self.get_application_admin().get_translator()
        for translator in translators:
            QtCore.QCoreApplication.installTranslator(translator)
        has_programming_error = False

    def get_application_admin(self):
        """Overwrite this method to make use of a custom application admin"""
        from camelot.admin.application_admin import ApplicationAdmin
        return ApplicationAdmin()
            
    def get_admins(self):
        """Should return all admin for which a table and a form view should be displayed,
        by default, returns for all entities their default admin"""
        from sqlalchemy.orm.mapper import _mapper_registry
         
        classes = []
        for mapper in _mapper_registry.keys():
            if hasattr(mapper, 'class_'):
                classes.append( mapper.class_ )
            else:
                raise Exception()
            
        app_admin = self.get_application_admin()
        return [app_admin.get_entity_admin(c) for c in classes if app_admin.get_entity_admin(c)]

    def test_select_view(self):
        for admin in self.get_admins():
            widget = admin.create_select_view()
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')
            self.assertFalse( has_programming_error )
            
    def test_table_view(self):
        from camelot.admin.action.base import GuiContext
        gui_context = GuiContext()
        for admin in self.get_admins():
            widget = admin.create_table_view( gui_context )
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')
            self.assertFalse( has_programming_error )

    def test_new_view(self):
        for admin in self.get_admins():
            widget = admin.create_new_view()
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')
            self.assertFalse( has_programming_error )

