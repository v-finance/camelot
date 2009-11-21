#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================


from camelot.view.model_thread import model_function


_application_admin_ = []


def get_application_admin():
    if not len(_application_admin_):
        raise Exception('No application admin class has been constructed yet')
    return _application_admin_[0]


class ApplicationAdmin(object):
    """The Application Admin class defines how the application should look
    like, it also ties python classes to their associated admin classes.  It's
    behaviour can be steered by overwriting its static attributes or it's
    methods :

    .. attribute:: name

    The name of the application, as it will appear in the title of the main
    window.

    .. attribute:: sections

    A list containing the various sections that should appear in the left panel
    of the mainwindow.

    .. image:: ../_static/picture2.png

    """

    name = 'Camelot'
    sections = ['Relations', 'Configuration']
    admins = {}

    def __init__(self):
        _application_admin_.append(self)

    def register(self, entity, admin_class):
        self.admins[entity] = admin_class

    @model_function
    def get_sections(self):
        from camelot.admin.section import structure_to_sections
        return structure_to_sections(self.sections)

    def get_entity_admin(self, entity):
        """Get the default entity admin for this entity, return None, if not
        existant"""
        try:
            return self.admins[entity](self, entity)
        except KeyError:
            pass
        if hasattr(entity, 'Admin'):
            return entity.Admin(self, entity)

    def get_entity_query(self, entity):
        """Get the root query for an entity"""
        return entity.query

    def create_main_window(self):
        """create_main_window"""
        from camelot.view.mainwindow import MainWindow
        mainwindow = MainWindow(self)
        return mainwindow

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
        """:return: a list of actions that should be added to the menu and the
        icon bar for this application, each action is a tuple of
        (name, icon, callable), where callable is a function taking no
        arguments that will be called when the action is executed.  Callable
        will be called in the model thread.
        """
        return []

    def get_name(self):
        """:return: the name of the application"""
        return self.name

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
        return QUrl('http://www.conceptive.be/projects/camelot/')

    def get_stylesheet(self):
        """
        :return: the qt stylesheet to be used for this application as a string
        or None if no stylesheet needed
        """
        return None

    def get_about(self):
        """:return: the content of the About dialog, a string with html
        syntax"""
        return """<b>Camelot Project</b>
                  <p>
                  Copyright &copy; 2008-2009 Conceptive Engineering.
                  All rights reserved.
                  </p>
                  <p>
                  http://www.conceptive.be/projects/camelot
                  </p>
                  """

    def get_default_field_attributes(self, type_, field):
        """Returns the default field attributes"""
        from camelot.core.view.field_attributes import \
            _sqlalchemy_to_python_type_
        return _sqlalchemy_to_python_type_[type_](field)
