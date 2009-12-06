"""
Camelot unittest framework
"""

import unittest

_application_ = []

def get_application():
    """Get the singleton QApplication"""
    from PyQt4.QtGui import QApplication
    if not len(_application_):
        import sys
        _application_.append(QApplication(sys.argv))
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
        from PyQt4.QtGui import QPixmap
        if not subdir:
            images_path = os.path.join(self.images_path, self.__class__.__name__.lower()[:-len('Test')])
        else:
            images_path = os.path.join(self.images_path, subdir)
        if not os.path.exists(images_path):
            os.makedirs(images_path)
        test_case_name = sys._getframe(1).f_code.co_name[5:]
        image_name = '%s.png'%test_case_name
        if suffix:
            image_name = '%s_%s.png'%(test_case_name, suffix)
        widget.adjustSize()
        self.process()
        pixmap = QPixmap.grabWidget(widget)
        pixmap = QPixmap.grabWidget(widget)
        pixmap.save(os.path.join(images_path, image_name), 'PNG')

    def process(self):
        """Wait until all events are processed and the queues of the model thread are empty"""
        self.mt.wait_on_work()

    def setUp(self):
        self.app = get_application()
        from camelot.view.model_thread import get_model_thread, construct_model_thread, has_model_thread
        from camelot.view.remote_signals import construct_signal_handler
        if not has_model_thread():
            construct_model_thread()
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

class SchemaTest(ModelThreadTestCase):
    """Test the database schema"""

    def test_schema_display(self):
      
        def schema_display_task():
            import os
            from camelot.bin.camelot_manage import schema_display
            schema_display(os.path.join(self.images_path, 'schema.png'))
            
        from camelot.view.model_thread import get_model_thread, post
        post( schema_display_task )
        get_model_thread().wait_on_work()

class EntityViewsTest(ModelThreadTestCase):
    """Test the views of all the Entity subclasses, subclass this class to test all views
    in your application.  This is done by calling the create_table_view and create_new_view
    on a set of admin objects.  To tell the test case which admin objects should be tested,
    overwrite the get_admins method ::

    class MyEntityViewsTest(EntityViewsTest):

        def get_admins(self):
          from elixir import entities
          application_admin import MyApplicationAdmin
          self.app_admin = MyApplicationAdmin()
          return [self.app_admin.get_entity_admin(e) for e in entities if self.app_admin.get_entity_admin(e)]

    """

    def setUp(self):
        super(EntityViewsTest, self).setUp()

    def get_admins(self):
        from elixir import entities
        from camelot.admin.application_admin import ApplicationAdmin
        self.app_admin = ApplicationAdmin()
        return [self.app_admin.get_entity_admin(e) for e in entities if self.app_admin.get_entity_admin(e)]

    def test_table_view(self):
        for admin in self.get_admins():
            widget = admin.create_table_view()
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')

    def test_new_view(self):
        for admin in self.get_admins():
            widget = admin.create_new_view()
            self.grab_widget(widget, suffix=admin.entity.__name__.lower(), subdir='entityviews')
