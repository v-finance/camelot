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
Camelot unittest helpers.  This module contains helper classes and functions
to write unittests for Camelot applications.  These are not the unittests for
Camelot itself. 
"""

import logging
import unittest
import six

from ..admin.action.application_action import ApplicationActionGuiContext
from ..admin.entity_admin import EntityAdmin
from ..core.orm import Session
from ..core.qt import QtGui, QtCore, Qt
from ..view import action_steps

has_programming_error = False
_application_ = []


LOGGER = logging.getLogger('camelot.test')

def get_application():
    """Get the singleton QApplication"""
    if not len(_application_):
        #
        # Uniform style for screenshot generation
        #
        application = QtGui.QApplication.instance()
        if not application:
            import sys
            from camelot.view import art
            QtGui.QApplication.setStyle('cleanlooks')
            application = QtGui.QApplication(sys.argv)
            application.setStyleSheet( art.read('stylesheet/office2007_blue.qss').decode('utf-8') )
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
        QtGui.QApplication.flush()
        widget.repaint()
        inner_pixmap = QtGui.QPixmap.grabWidget(widget, 0, 0, widget.width(), widget.height())
        # add a border to the image
        border = 4
        outer_image = QtGui.QImage(inner_pixmap.width()+2*border, inner_pixmap.height()+2*border, QtGui.QImage.Format_RGB888)
        outer_image.fill(Qt.gray)
        painter = QtGui.QPainter()
        painter.begin(outer_image)
        painter.drawPixmap(QtCore.QRectF(border, border, inner_pixmap.width(), inner_pixmap.height()), 
                          inner_pixmap,
                          QtCore.QRectF(0, 0, inner_pixmap.width(), inner_pixmap.height()))
        painter.end()
        outer_image.save(os.path.join(images_path, image_name), 'PNG')

    def process(self):
        """Wait until all events are processed and the queues of the model thread are empty"""
        self.mt.wait_on_work()

    def setUp(self):
        from camelot.core.conf import settings
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
        self.mt.post( settings.setup_model )
        self.process()

    def tearDown(self):
        self.process()
        #self.mt.exit(0)
        #self.mt.wait()

class ApplicationViewsTest(ModelThreadTestCase):
    """Test various application level views, like the main window, the
    sidepanel"""
    
    def setUp(self):
        super(ApplicationViewsTest, self).setUp()
        self.gui_context = ApplicationActionGuiContext()

    def get_application_admin(self):
        """Overwrite this method to make use of a custom application admin"""
        from camelot.admin.application_admin import ApplicationAdmin
        return ApplicationAdmin()
    
    def install_translators(self, app_admin):
        for translator in app_admin.get_translator():
            QtCore.QCoreApplication.installTranslator(translator)

    def test_navigation_pane(self):
        from camelot.view.controls.section_widget import NavigationPane
        app_admin = self.get_application_admin()
        self.install_translators(app_admin)
        nav_pane = NavigationPane(None, None)
        nav_pane.set_sections(app_admin.get_sections())
        self.grab_widget(nav_pane, subdir='applicationviews')
      
    def test_main_window(self):
        app_admin = self.get_application_admin()
        self.gui_context.admin = app_admin
        self.install_translators(app_admin)
        step = action_steps.MainWindow(app_admin)
        widget = step.render(self.gui_context)
        self.grab_widget(widget, subdir='applicationviews')
    
class EntityViewsTest(ModelThreadTestCase):
    """Test the views of all the Entity subclasses, subclass this class to test all views
    in your application.  This is done by calling the create_table_view and create_new_view
    on a set of admin objects.  To tell the test case which admin objects should be tested,
    overwrite the get_admins method.
    """

    def setUp(self):
        super(EntityViewsTest, self).setUp()
        global has_programming_error
        translators = self.get_application_admin().get_translator()
        for translator in translators:
            QtCore.QCoreApplication.installTranslator(translator)
        has_programming_error = False
        self.session = Session()

    def get_application_admin(self):
        """Overwrite this method to make use of a custom application admin"""
        from camelot.admin.application_admin import ApplicationAdmin
        return ApplicationAdmin()
            
    def get_admins(self):
        """Should return all admin for which a table and a form view should be displayed,
        by default, returns for all entities their default admin"""
        from sqlalchemy.orm.mapper import _mapper_registry
         
        classes = []
        for mapper in six.iterkeys(_mapper_registry):
            if hasattr(mapper, 'class_'):
                classes.append( mapper.class_ )
            else:
                raise Exception()
            
        app_admin = self.get_application_admin()
        
        for cls in classes:
            admin = app_admin.get_related_admin(cls)
            if admin is not None:
                yield admin

    def test_table_view(self):
        from camelot.admin.action.base import GuiContext
        from camelot.view.action_steps import OpenTableView
        gui_context = GuiContext()
        for admin in self.get_admins():
            if isinstance(admin, EntityAdmin):
                step = OpenTableView(admin, admin.get_query())
                widget = step.render(gui_context)
                self.grab_widget(widget, suffix=admin.entity.__name__.lower(),
                                 subdir='entityviews')
                self.assertFalse( has_programming_error )

    def test_new_view(self):
        from camelot.admin.action.base import GuiContext
        from camelot.admin.entity_admin import EntityAdmin
        from ..view.action_steps import OpenFormView
        gui_context = GuiContext()
        for admin in self.get_admins():
            verbose_name = six.text_type(admin.get_verbose_name())
            LOGGER.debug('create new view for admin {0}'.format(verbose_name))
            # create an object or take one from the db
            obj = None
            new_obj = False
            if isinstance(admin, EntityAdmin):
                obj = admin.get_query().first()
            if obj is None:
                obj = admin.entity()
                new_obj = True
            # create a form view
            form_view_step = OpenFormView([obj], admin)
            widget = form_view_step.render(gui_context)
            mapper = widget.findChild(QtGui.QDataWidgetMapper, 'widget_mapper')
            mapper.revert()
            self.process()
            if admin.form_state != None:
                # virtually maximize the widget
                widget.setMinimumSize(1200, 800)
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')
            self.assertFalse( has_programming_error )
            if new_obj:
                self.session.expunge(obj)
