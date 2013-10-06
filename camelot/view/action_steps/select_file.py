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

import os

import six

from ...core.qt import QtGui, QtCore, py_to_variant
  
from camelot.admin.action import ActionStep
from camelot.view.action_runner import hide_progress_dialog
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _

class SelectFile( ActionStep ):
    """Select one or more files to open or to process.
    
    :param file_name_filter: Filter on the names of the files that can
        be selected, such as 'All files (*)'.  
        See :class:`QtGui.QFileDialog` for more documentation.
    
    .. attribute:: single
    
        defaults to :const:`True`, set to :const:`False` if selection
        of multiple files is allowed

    .. attribute:: existing
    
        defaults to :const:`True`, set to :const:`False` if non existing
        files are allowed (to save something)
        
    .. attribute:: proposal
    
         proposed file name
         
    .. attribute:: button_text
    
         the text in the button to confirm the selection
        
    The :keyword:`yield` statement of :class:`SelectFile` returns a list
    of selected file names.  This list has only one element when single is
    set to :const:`True`.  Raises a 
    :class:`camelot.core.exception.CancelRequest` when no file was selected.
    
    .. image:: /_static/actionsteps/select_file.png
    
    This action step stores its last location into the :class:`QtCore.QSettings` 
    and uses it as the initial location the next time it is invoked.
    """
    
    def __init__( self, file_name_filter = ''):
        self.file_name_filter = unicode(file_name_filter)
        self.single = True
        self.existing = True
        self.proposal = None
        self.button_text = _('Open')
    
    def render( self, directory = None ):
        """create the file dialog widget. this method is used to unit test
        the action step.

        :param directory: the directory in which to open the dialog, None to
            use the default
        """
        directory = os.path.dirname(directory or '')
        if self.proposal is not None:
            directory = os.path.join(directory, self.proposal)
        dialog = QtGui.QFileDialog( filter = self.file_name_filter,
                                    directory = directory )
        if self.existing == False:
            file_mode = QtGui.QFileDialog.AnyFile
        else:
            if self.single == True:
                file_mode = QtGui.QFileDialog.ExistingFile
            else:
                file_mode = QtGui.QFileDialog.ExistingFiles
        dialog.setFileMode( file_mode )
        return dialog
    
    def gui_run( self, gui_context ):
        settings = QtCore.QSettings()
        directory = unicode(settings.value( 'datasource' ).toString())
        dialog = self.render( directory )
        with hide_progress_dialog( gui_context ):
            if dialog.exec_() == QtGui.QDialog.Rejected:
                raise CancelRequest()
            file_names = [six.text_type(fn) for fn in dialog.selectedFiles()]
            if file_names:
                settings.setValue( 'datasource', py_to_variant( file_names[0] ) )
            return file_names


