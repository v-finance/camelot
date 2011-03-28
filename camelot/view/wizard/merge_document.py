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
'''
Wizard to merge documents with a list of objects.

This wizard is triggered thru an entry in the main menu.
'''

from PyQt4 import QtGui, QtCore

import os

from camelot.core.utils import ugettext_lazy as _
from camelot.core.utils import variant_to_pyobject
from camelot.view.art import Icon
from camelot.view.wizard.pages.progress_page import ProgressPage
from camelot.view.wizard.pages.select import SelectFilePage

class SelectTemplatePage(SelectFilePage):
    """Page to select the template to merge"""
    title = _('Merge a template document')
    sub_title = _(
        "Click 'Browse' to select a template file, then click 'Next'."
    )
    icon = Icon('tango/32x32/mimetypes/x-office-document-template.png')

class MergePage(ProgressPage):
    """Wait until merge is complete"""
    title = _('Merge in progress')
    
    def __init__(self, parent, selection_getter):
        super(MergePage, self).__init__(parent)
        self._selection_getter = selection_getter
        
    def run(self):
        from jinja2 import Environment, FileSystemLoader
        import tempfile
        import datetime
        objects = list(self._selection_getter())
        self.update_maximum_signal.emit( len(objects) + 1)
        number_of_digits = len( str( len( objects ) + 1 ) )
        destination_folder = tempfile.mkdtemp()
        template_file_name = variant_to_pyobject( self.field('datasource') )
        file_system_loader = FileSystemLoader( os.path.dirname( template_file_name ) )
        environment = Environment( loader=file_system_loader )
        template = environment.get_template( os.path.basename( template_file_name ) )
        extension = os.path.splitext( template_file_name )[1]
        self.update_progress_signal.emit( 1, 'Opened template' )
        for i, obj in enumerate(objects):
            context = {'obj':obj, 'now':datetime.datetime.now()}
            document = template.render( context )
            index = '%0*i'%(number_of_digits, i+1)
            destination_file = os.path.join( destination_folder, 
                                             'document %s'%index + extension )
            open( destination_file, 'w').write( document.encode('utf-8') )
            self.update_progress_signal.emit( i+1, unicode(obj) )
        url = QtCore.QUrl.fromLocalFile( destination_folder )
        QtGui.QDesktopServices.openUrl( url )

class MergeDocumentWizard(QtGui.QWizard):
    """This wizard lets the user select a template file, it then
merges that template will all the selected rows in a table"""
    
    window_title = _('Merge Document')

    def __init__(self, parent=None, selection_getter=None):
        """:param selection_getter: function to loop over the list of objects
        to merge"""
        super(MergeDocumentWizard, self).__init__(parent)
        self.setWindowTitle( unicode(self.window_title) )
        assert selection_getter
        self.addPage(SelectTemplatePage(parent=self))
        self.addPage(MergePage(parent=self, selection_getter=selection_getter))


