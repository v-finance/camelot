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

import itertools
import logging
import os

logger = logging.getLogger('camelot.admin.application_admin')

from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui

from camelot.admin.action import application_action, form_action, list_action
from camelot.core.utils import ugettext_lazy as _
from camelot.view import art
from camelot.view import database_selection
from camelot.view.model_thread import model_function

_application_admin_ = []

#
# The translations data needs to be kept alive during the
# running of the application
#
_translations_data_ = []

def get_application_admin():
    if not len(_application_admin_):
        raise Exception('No application admin class has been constructed yet')
    return _application_admin_[0]

class ApplicationAdmin(QtCore.QObject):
    """The ApplicationAdmin class defines how the application should look
like, it also ties Python classes to their associated 
:class:`camelot.admin.object_admin.ObjectAdmin` class or subclass.  It's
behaviour can be steered by overwriting its static attributes or it's
methods :

.. attribute:: name

    The name of the application, as it will appear in the title of the main
    window.

.. attribute:: application_url

    The url of the web site where the user can find more information on
    the application.

.. attribute:: help_url

    Points to either a local html file or a web site that contains the
    documentation of the application.

.. attribute:: author

    The name of the author of the application
    
.. attribute:: domain

    The domain name of the author of the application, eg 'mydomain.com', this
    domain will be used to store settings of the application.
    
.. attribute:: version
    
    A string with the version of the application
    
.. attribute:: database_profile_wizard
    
    The wizard that should be used to create new database profiles. Defaults
    to :class:`camelot.view.database_selection.ProfileWizard`
    
.. attribute:: database_selection

    if this is set to True, present the user with a database selection
    wizard prior to starting the application.  Defaults to :keyword:`False`.
    
When the same action is returned in the :meth:`get_toolbar_actions` and 
:meth:`get_main_menu` method, it should be exactly the same object, to avoid
shortcut confusion and reduce the number of status updates.
    """

    database_profile_wizard = database_selection.ProfileWizard

    name = 'Camelot'
    application_url = None
    help_url = 'http://www.python-camelot.com/docs.html'
    author = 'Conceptive Engineering'
    domain = 'python-camelot.com'

    version = '1.0'
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

    #
    # actions that will be shared between the toolbar and the main menu
    #
    change_row_actions = [ list_action.ToFirstRow(),
                           list_action.ToPreviousRow(),
                           list_action.ToNextRow(),
                           list_action.ToLastRow(), ]
    edit_actions = [ list_action.OpenNewView(),
                     list_action.DeleteSelection(),
                     list_action.DuplicateSelection(),]
    help_actions = [ application_action.ShowHelp(), ]
    export_actions = [ list_action.PrintPreview(),
                       list_action.ExportSpreadsheet() ]
    form_toolbar_actions = [ form_action.CloseForm(),
                             form_action.ToFirstForm(),
                             form_action.ToPreviousForm(),
                             form_action.ToNextForm(),
                             form_action.ToLastForm(),
                             application_action.Refresh() ]
    
    def __init__(self):
        """Construct an ApplicationAdmin object and register it as the 
        prefered ApplicationAdmin to use througout the application"""
        QtCore.QObject.__init__(self)
        _application_admin_.append(self)
        #
        # Cache created ObjectAdmin objects
        #
        self._object_admin_cache = {}

    def register(self, entity, admin_class):
        """Associate a certain ObjectAdmin class with another class.  This
        ObjectAdmin will be used as default to render object the specified
        type.
        
        :param entity: :class:`class`
        :param admin_class: a subclass of 
            :class:`camelot.admin.object_admin.ObjectAdmin` or
            :class:`camelot.admin.entity_admin.EntityAdmin`
        """
        self.admins[entity] = admin_class

    @model_function
    def get_sections( self ):
        """A list of :class:`camelot.admin.section.Section` objects,
        these are the sections to be displayed in the left panel.
        
        .. image:: /_static/picture2.png
        """
        from camelot.admin.section import Section
        
        return [ Section( _('Relations'), self ),
                 Section( _('Configuration'), self ),
                 ]
    
    def get_settings( self ):
        """A :class:`QtCore.QSettings` object in which Camelot related settings
        can be stored.  This object is inteded for Camelot internal use.  If an
        application specific settings object is needed, simply construct one.
        
        :return: a :class:`QtCore.QSettings` object
        """
        settings = QtCore.QSettings()
        settings.beginGroup( 'Camelot' )
        return settings
        
    def get_application_admin( self ):
        """Get the :class:`ApplicationAdmin` class of this application, this
        method is here for compatibility with the :class:`ObjectAdmin`
        
        :return: this object itself
        """
        return self
    
    def get_related_admin(self, cls):
        """Get the default :class:`camelot.admin.object_admin.ObjectAdmin` class
        for a specific class, return None, if not known.  The ObjectAdmin
        should either be registered through the :meth:`register` method or be
        defined as an inner class with name :keyword:`Admin` of the entity.

        :param entity: a :class:`class`
        
        """
        return self.get_entity_admin( cls )
    
    def get_entity_admin(self, entity):
        """Get the default :class:`camelot.admin.object_admin.ObjectAdmin` class
        for a specific entity, return None, if not known.  The ObjectAdmin
        should either be registered through the :meth:`register` method or be
        defined as an inner class with name :keyword:`Admin` of the entity.

        :param entity: a :class:`class`
        
        deprecated : use get_related_admin instead
        """

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

    def create_main_window(self):
        """Create the main window that will be shown when the application
        starts up.  By default, returns an instance of 
         :class:`camelot.view.mainwindow.MainWindow`
         
        :return: a :class:`PyQt4.QtGui.QWidget`
        """
        from camelot.admin.action.application_action import ApplicationActionGuiContext
        from camelot.view.mainwindow import MainWindow
        gui_context = ApplicationActionGuiContext()
        gui_context.admin = self
        mainwindow = MainWindow( gui_context )
        shortcut_versions = QtGui.QShortcut(
            QtGui.QKeySequence( QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_V ),
            mainwindow
        )
        shortcut_versions.activated.connect( self.show_versions )
        shortcut_dump_state = QtGui.QShortcut(
            QtGui.QKeySequence( QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_D ),
            mainwindow
        )
        shortcut_dump_state.activated.connect( self.dump_state )
        shortcut_read_null = QtGui.QShortcut(
            QtGui.QKeySequence( QtCore.Qt.CTRL+QtCore.Qt.ALT+QtCore.Qt.Key_0 ),
            mainwindow
        )
        shortcut_read_null.activated.connect( self.read_null )
        return mainwindow

    @QtCore.pyqtSlot()
    def show_versions(self):
        """Pops up a messagebox showing the version of certain
        libraries used.  This is for debugging purposes."""
        logger.debug('showing about message box with versions')
        abtmsg = self.get_versions()
        QtGui.QMessageBox.about(None, 'Versions', abtmsg)
        logger.debug('about message with versions closed')

    def get_actions(self):
        """
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the desktop of the user.
        """
        return []
    
    def get_related_toolbar_actions( self, toolbar_area, direction ):
        """Specify the toolbar actions that should appear by default on every
        OneToMany editor in the application.
        
        :param toolbar_area: the position of the toolbar
        :param direction: the direction of the relation : 'onetomany' or 
            'manytomany'
        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        if toolbar_area == Qt.RightToolBarArea and direction == 'onetomany':
            return [ list_action.AddNewObject(),
                     list_action.DeleteSelection(),
                     list_action.DuplicateSelection(),
                     list_action.ExportSpreadsheet(), ]
        if toolbar_area == Qt.RightToolBarArea and direction == 'manytomany':
            return [ list_action.AddExistingObject(),
                     list_action.RemoveSelection(),
                     list_action.ExportSpreadsheet(), ]
        
    def get_form_actions( self ):
        """Specify the action buttons that should appear on each form in the
        application.  
        The :meth:`camelot.admin.object_admin.ObjectAdmin.get_form_actions`
        method will call this method and prepend the result to the actions
        of that specific form.
        
        :return: a list of :class:`camelot.admin.action.base.Action` objects
        """
        return []
    
    def get_form_toolbar_actions( self, toolbar_area ):
        """
        :param toolbar_area: an instance of :class:`Qt.ToolBarArea` indicating
            where the toolbar actions will be positioned
            
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of a form view.  return
            None if no toolbar should be created.
        """
        if toolbar_area == Qt.TopToolBarArea:
            return self.form_toolbar_actions
        
    def get_main_menu( self ):
        """
        :return: a list of :class:`camelot.admin.menu.Menu` objects, or None if 
            there should be no main menu
        """
        from camelot.admin.menu import Menu

        return [ Menu( _('&File'),
                       [ application_action.Backup(),
                         application_action.Restore(),
                         None,
                         Menu( _('Export To'),
                               self.export_actions ),
                         Menu( _('Import From'),
                               [list_action.ImportFromFile()] ),
                         None,
                         application_action.Exit(),
                         ] ),
                 Menu( _('&Edit'),
                       self.edit_actions + [
                        None,
                        list_action.SelectAll(),
                        None,
                        list_action.ReplaceFieldContents(),   
                        ]),
                 Menu( _('View'),
                       [ application_action.Refresh(),
                         Menu( _('Go To'), self.change_row_actions) ] ),
                 Menu( _('&Help'),
                       self.help_actions + [
                         application_action.ShowAbout() ] )
                 ]
    
    def get_toolbar_actions( self, toolbar_area ):
        """
        :param toolbar_area: an instance of :class:`Qt.ToolBarArea` indicating
            where the toolbar actions will be positioned
            
        :return: a list of :class:`camelot.admin.action.base.Action` objects
            that should be displayed on the toolbar of the application.  return
            None if no toolbar should be created.
        """
        if toolbar_area == Qt.TopToolBarArea:
            return self.edit_actions + self.change_row_actions + \
                   self.export_actions + self.help_actions
    
    def get_name(self):
        """
        :return: the name of the application, by default this is the class
            attribute name"""
        return unicode( self.name )

    def get_version(self):
        """:return: string representing version of the application, by default this
                    is the class attribute verion"""
        return self.version

    def get_icon(self):
        """:return: the :class:`camelot.view.art.Icon` that should be used for the application"""
        from camelot.view.art import Icon
        return Icon('tango/32x32/apps/system-users.png').getQIcon()

    def get_splashscreen(self):
        """:return: a :class:`PyQt4.QtGui.QPixmap` to be used as splash screen"""
        from camelot.view.art import Pixmap
        qpm = Pixmap('splashscreen.png').getQPixmap()
        img = qpm.toImage()
        # support transparency
        if not qpm.mask(): 
            if img.hasAlphaBuffer(): bm = img.createAlphaMask() 
            else: bm = img.createHeuristicMask() 
            qpm.setMask(bm) 
        return qpm

    def get_organization_name(self):
        """
        :return: a string with the name of the organization that wrote the
            application. By default returns the :attr:`ApplicationAdmin.author`
            attribute.
        """
        return self.author

    def get_organization_domain(self):
        """
        :return: a string with the domain name of the organization that wrote the
            application. By default returns the :attr:`ApplicationAdmin.domain`
            attribute.
        """
        return self.domain

    def get_help_url(self):
        """:return: a :class:`PyQt4.QtCore.QUrl` pointing to the index page for help"""
        from PyQt4.QtCore import QUrl
        if self.help_url:
            return QUrl( self.help_url )

    def get_stylesheet(self):
        """
        :return: a string with the content of a qt stylesheet to be used for 
        this application as a string or None if no stylesheet needed.

        Camelot comes with a couple of default stylesheets :

         * stylesheet/office2007_blue.qss
         * stylesheet/office2007_black.qss
         * stylesheet/office2007_silver.qss

        Have a look at the default implementation to use another stylesheet.
        """
        #
        # Try to load a custom QStyle, if that fails use a stylesheet from
        # a file
        #
        try:
            from PyTitan import QtnOfficeStyle
            QtnOfficeStyle.setApplicationStyle( QtnOfficeStyle.Windows7Scenic )
        except:
            pass
        return art.read('stylesheet/office2007_blue.qss')

    def _load_translator_from_file( self, 
                                    module_name, 
                                    file_name, 
                                    directory = '', 
                                    search_delimiters = '_', 
                                    suffix = '.qm' ):
        """
        Tries to create a translator based on a file stored within a module.
        The file is loaded through the pkg_resources, to enable loading it from
        within a Python egg.  This method tries to mimic the behavior of
        :meth:`QtCore.QTranslator.load` while looking for an appropriate
        translation file.
        
        :param module_name: the name of the module in which to look for
            the translation file with pkg_resources.
        :param file_name: the filename of the the tranlations file, without 
            suffix
        :param directory: the directory, relative to the module in which
            to look for translation files
        :param suffix: the suffix of the filename
        :param search_delimiters: list of characters by which to split the file
            name to search for variations of the file name
        :return: :keyword:None if unable to load the file, otherwise a
            :obj:`QtCore.QTranslator` object.
            
        This method tries to load all file names with or without suffix, and
        with or without the part after the search delimiter.
        """
        from camelot.core.resources import resource_string

        #
        # split the directory names and file name
        #
        file_name_parts = [ file_name ]
        head, tail = os.path.split( file_name_parts[0] )
        while tail:
            file_name_parts[0] = tail
            file_name_parts = [ head ] + file_name_parts
            head, tail = os.path.split( file_name_parts[0] )
        #
        # for each directory and file name, generate all possibilities
        #
        file_name_parts_possibilities = []
        for file_name_part in file_name_parts:
            part_possibilities = []
            for search_delimiter in search_delimiters:
                delimited_parts = file_name_part.split( search_delimiter )
                for i in range( len( delimited_parts ) ):
                    part_possibility = search_delimiter.join( delimited_parts[:len(delimited_parts)-i] )
                    part_possibilities.append( part_possibility )
            file_name_parts_possibilities.append( part_possibilities )
        #
        # make the combination of all those possibilities
        #
        file_names = []
        for parts_possibility in itertools.product( *file_name_parts_possibilities ):
            file_name = os.path.join( *parts_possibility )
            file_names.append( file_name )
            file_names.append( file_name + suffix )
        #
        # now try all file names
        #
        translations = None
        for file_name in file_names:
            try:
                logger.debug( u'try %s'%file_name )
                translations = resource_string( module_name, os.path.join(directory,file_name) )
                break
            except IOError:
                pass
        if translations:
            _translations_data_.append( translations ) # keep the data alive
            translator = QtCore.QTranslator()
            # PySide workaround for missing loadFromData method
            if not hasattr( translator, 'loadFromData' ):
                return
            if translator.loadFromData( translations ):
                logger.info("add translation %s" % (directory + file_name))
                return translator
        
    def get_translator(self):
        """Reimplement this method to add application specific translations
        to your application.  The default method returns a list with the
        default Qt and the default Camelot translator for the current system
        locale.  Call :meth:`QLocale.setDefault` before this method is called
        if you want to load different translations then the system default.

        :return: a list of :obj:`QtCore.QTranslator` objects that should be 
            used to translate the application
        """
        translators = []
        qt_translator = QtCore.QTranslator()
        locale_name = QtCore.QLocale().name()
        logger.info( u'using locale %s'%locale_name )
        if qt_translator.load( "qt_" + locale_name,
                               QtCore.QLibraryInfo.location( QtCore.QLibraryInfo.TranslationsPath ) ):
            translators.append( qt_translator )
        camelot_translator = self._load_translator_from_file( 'camelot', 
                                                              os.path.join( '%s/LC_MESSAGES/'%locale_name, 'camelot' ),
                                                              'art/translations/' )
        if camelot_translator:
            translators.append( camelot_translator )
        else:
            logger.debug( 'no camelot translations found for %s'%locale_name )
        return translators

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
        import chardet
        import jinja2
        import xlrd
        import xlwt
                
        return """<em>Python:</em> <b>%s</b><br>
                  <em>Qt:</em> <b>%s</b><br>
                  <em>PyQt:</em> <b>%s</b><br>
                  <em>SQLAlchemy:</em> <b>%s</b><br>
                  <em>Chardet:</em> <b>%s</b><br>
                  <em>Jinja:</em> <b>%s</b><br>
                  <em>xlrd:</em> <b>%s</b><br>
                  <em>xlwt:</em> <b>%s</b><br><br>
                  <em>path:<br></em> %s""" % ('.'.join([str(el) for el in sys.version_info]),
                                              float('.'.join(str(QtCore.QT_VERSION_STR).split('.')[0:2])),
                                              QtCore.PYQT_VERSION_STR,
                                              sqlalchemy.__version__,
                                              chardet.__version__,
                                              jinja2.__version__,
                                              xlrd.__VERSION__,
                                              xlwt.__VERSION__,
                                              unicode(sys.path))
    
    def read_null(self):
        """Create a segmentation fault by reading null, this is to test
        the faulthandling functions.  this method is triggered by pressing
        :kbd:`Ctrl-Alt-0` in the GUI"""
        ok = QtGui.QMessageBox.critical( None, 
                                         'Experimental segfault',
                                         'Are you sure you want to segfault the application',
                                         buttons = QtGui.QMessageBox.No | QtGui.QMessageBox.Yes )
        if ok == QtGui.QMessageBox.Yes:
            import faulthandler
            faulthandler._read_null()
    
    def dump_state(self):
        """Dump the state of the application to the output, this method is
        triggered by pressing :kbd:`Ctrl-Alt-D` in the GUI"""
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

