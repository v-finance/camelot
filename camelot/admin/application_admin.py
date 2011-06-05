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

import logging
logger = logging.getLogger('camelot.admin.application_admin')

from PyQt4 import QtCore, QtGui

from camelot.view.model_thread import model_function
from camelot.core.backup import BackupMechanism
from camelot.view import art
from camelot.view import database_selection

_application_admin_ = []

def get_application_admin():
    if not len(_application_admin_):
        raise Exception('No application admin class has been constructed yet')
    return _application_admin_[0]


class ApplicationAdmin(QtCore.QObject):
    """The Application Admin class defines how the application should look
    like, it also ties python classes to their associated admin classes.  It's
    behaviour can be steered by overwriting its static attributes or it's
    methods :

    .. attribute:: name

    The name of the application, as it will appear in the title of the main
    window.
    
    .. attribute:: version
    
    A string with the version of the application

    .. attribute:: backup_mechanism

    A subclass of camelot.core.backup.BackupMechanism that enables the application
    to perform backups an restores.
    
    .. attribute:: database_profile_wizard
    
    The wizard that should can be used to create new database profiles
    """

    backup_mechanism = BackupMechanism
    database_profile_wizard = database_selection.ProfileWizard
    name = 'Camelot'
    version = '1.0'
    sections = ['Relations', 'Configuration']
    admins = {}

    # This signal is emitted whenever the sections are changed, and the views
    # should be updated
    sections_changed_signal = QtCore.pyqtSignal()
    # This signal is emitted whenever the tile of the main window needs to
    # be changed.
    title_changed_signal = QtCore.pyqtSignal(str)
    # Emitted whenever the application actions need to be changed
    actions_changed_signal = QtCore.pyqtSignal()

    database_selection = False

    def __init__(self):
        QtCore.QObject.__init__(self)
        _application_admin_.append(self)
        #
        # Cache created ObjectAdmin objects
        #
        self._object_admin_cache = {}

    def register(self, entity, admin_class):
        self.admins[entity] = admin_class

    @model_function
    def get_sections(self):
        """A list of sections, to be displayed in the left panel.
        
            .. image:: ../_static/picture2.png
        """
        from camelot.admin.section import structure_to_sections
        return structure_to_sections(self.sections)

    def get_entity_admin(self, entity):
        """Get the default entity admin for this entity, return None, if not
        existant"""

        admin_class = None
        try:
            admin_class = self.admins[entity]
        except KeyError:
            pass
        if not admin_class and hasattr(entity, 'Admin'):
            admin_class = entity.Admin
        if admin_class:
            try:
                return self._object_admin_cache[admin_class]
            except KeyError:
                admin = admin_class(self, entity)
                self._object_admin_cache[admin_class] = admin
                return admin

    def get_entity_query(self, entity):
        """Get the root query for an entity"""
        return entity.query

    def create_main_window(self):
        """create_main_window"""
        from camelot.view.mainwindow import MainWindow
        mainwindow = MainWindow(self)
        shortcut_versions = QtGui.QShortcut(
            QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_V,
            mainwindow
        )
        shortcut_versions.activated.connect( self.show_versions )
        shortcut_dump_state = QtGui.QShortcut(
            QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_D,
            mainwindow
        )
        shortcut_dump_state.activated.connect( self.dump_state )

        return mainwindow

    @QtCore.pyqtSlot()
    def show_versions(self):
        logger.debug('showing about message box with versions')
        abtmsg = self.get_versions()
        QtGui.QMessageBox.about(None, 'Versions', abtmsg)
        logger.debug('about message with versions closed')

    def get_entities_and_queries_in_section(self, section):
        """:return: a list of tuples of (admin, query) instances related to
        the entities in this section.
        """
        result = [(self.get_entity_admin(e), self.get_entity_query(e))
                  for e, a in self.admins.items()
                  if hasattr(a, 'section')
                  and a.section == section]
        result.sort(cmp = lambda x, y: cmp(x[0].get_verbose_name_plural(),
                                           y[0].get_verbose_name_plural()))
        return result

    def get_actions(self):
        """:return: a list of camelot.admin.application_action.ApplicationAction objects
        that should be added to the menu and the icon bar for this application
        """
        return []

    def get_name(self):
        """:return: the name of the application, by default this is the class
                    attribute name"""
        return self.name

    def get_version(self):
        """:return: string representing version of the application, by default this
                    is the class attribute verion"""
        return self.version

    def get_icon(self):
        """:return: the QIcon that should be used for the application"""
        from camelot.view.art import Icon
        return Icon('tango/32x32/apps/system-users.png').getQIcon()

    def get_splashscreen(self):
        """:return: a QtGui.QPixmap to be used as splash screen"""
        from camelot.view.art import Pixmap
        return Pixmap('splashscreen.png').getQPixmap()

    def get_organization_name(self):
        return 'Conceptive Engineering'

    def get_organization_domain(self):
        return 'conceptive.be'

    def get_help_url(self):
        """:return: a QUrl pointing to the index page for help"""
        from PyQt4.QtCore import QUrl
        return QUrl('http://www.python-camelot.com/docs.html')

    def get_whats_new(self):
        """:return: a widget that has a show() method """
        return None

    def get_affiliated_url(self):
        """:return: a QUrl pointing to an affiliated webpage

        When this method returns a QUrl, an additional item will be available
        in the 'Help' menu, when clicked the system browser will be opened
        an pointing to this url.

        This can be used to connect the user to a website that is used a lot
        in the organization, but hard to remember.
        """
        return None

    def get_remote_support_url(self):
        """:return: a QUrl pointing to a page to get remote support

        When this method returns a QUrl, an additional item will be available
        in the 'Help' menu, when clicked the system browser will be opened
        an pointing to this url.

        This can be used to connect the user to services like logmein.com, an
        online ticketing system or others.
        """
        return None

    def get_stylesheet(self):
        """
        :return: a string with the qt stylesheet to be used for this application as a string
        or None if no stylesheet needed.

        Camelot comes with a couple of default stylesheets :

         * stylesheet/office2007_blue.qss
         * stylesheet/office2007_black.qss
         * stylesheet/office2007_silver.qss

        Have a look at the default implementation to use another stylesheet.
        """
        return art.read('stylesheet/office2007_blue.qss')

    def get_translator(self):
        """Reimplement this method to add application specific translations
        to your application.

        :return: a QTranslator that should be used to translate the application or a 
                 list of QTranslors if multiple translators should be used
        """
        return QtCore.QTranslator()

    def get_about(self):
        """:return: the content of the About dialog, a string with html
                    syntax"""
        import datetime
        from camelot.core import license
        today = datetime.date.today()
        return """<b>Camelot</b><br/>
                  Building desktop applications at warp speed
                  <p>
                  Copyright &copy; 2007-%s Conceptive Engineering.
                  All rights reserved.
                  </p>
                  <p>
                  %s
                  </p>
                  <p>
                  http://www.python-camelot.com<br/>
                  http://www.conceptive.be
                  </p>
                  """%(today.year, license.license_type)

    def get_versions(self):
        """
        :return: html which displays the versions of used libs for development
        """
        import sys
        import sqlalchemy
        import elixir
        import cloudlaunch2
        import chardet
        import jinja2
        import pdfminer
        import xlrd
        import xlwt
                
        return """<em>Python version:</em> <b>%s</b><br>
                  <em>Qt:</em> <b>%s</b><br>
                  <em>PyQt:</em> <b>%s</b><br>
                  <em>SQLAlchemy:</em> <b>%s</b><br>
                  <em>Elixir:</em> <b>%s</b><br>
                  <em>Cloudlaunch:</em> <b>%s</b><br>
                  <em>Chardet:</em> <b>%s</b><br>
                  <em>Jinja:</em> <b>%s</b><br>
                  <em>PDFMiner:</em> <b>%s</b><br>
                  <em>xlrd:</em> <b>%s</b><br>
                  <em>xlwt:</em> <b>%s</b><br>""" % ('.'.join([str(el) for el in sys.version_info]),
                                                     float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2])),
                                                     QtCore.PYQT_VERSION_STR,
                                                     sqlalchemy.__version__,
                                                     elixir.__version__,
                                                     cloudlaunch2.__version__,
                                                     chardet.__version__,
                                                     jinja2.__version__,
                                                     pdfminer.__version__,
                                                     xlrd.__VERSION__,
                                                     xlwt.__VERSION__)
    
    def dump_state(self):
        """Dump the state of the application to the output, this method is
        triggered by pressing Ctrl-Alt-D in the GUI"""
        from camelot.view.model_thread import post
        from camelot.view.register import dump_register
        from camelot.view.proxy.collection_proxy import CollectionProxy

        import gc
        gc.collect()

            
        dump_register()
        
        def dump_session_state():
            import collections
            
            from camelot.model.authentication import Person

            print '======= begin session =============='
            type_counter = collections.defaultdict(int)
            for o in Person.query.session:
                type_counter[type(o).__name__] += 1
            for k,v in type_counter.items():
                print k,v
            print '====== end session =============='

        post( dump_session_state )

        for o in gc.get_objects():
            if isinstance(o, CollectionProxy):
                print o
                for r in gc.get_referrers(o):
                    print ' ', type(r).__name__
                    for rr in gc.get_referrers(r):
                        print  '  ', type(rr).__name__
                
    def get_default_field_attributes(self, type_, field):
        """Returns the default field attributes"""
        from camelot.core.view.field_attributes import \
            _sqlalchemy_to_python_type_
        return _sqlalchemy_to_python_type_[type_](field)

    def backup(self, main_window):
        from camelot.view.wizard.backup import BackupWizard
        wizard = BackupWizard(self.backup_mechanism, main_window)
        wizard.exec_()

    def restore(self, main_window):
        from camelot.view.wizard.backup import RestoreWizard
        wizard = RestoreWizard(self.backup_mechanism, main_window)
        wizard.exec_()



