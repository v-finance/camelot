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

from ...core.qt import QtGui, QtCore, variant_to_py, py_to_variant

import six

from camelot.admin.action import ActionStep
from camelot.view.action_runner import hide_progress_dialog
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _

class SelectFile( ActionStep ):
    """Select one or more files to open
    
    :param file_name_filter: Filter on the names of the files that can
        be selected, such as 'All files (*)'.  
        See :class:`QtGui.QFileDialog` for more documentation.
    
    .. attribute:: single
    
        defaults to :const:`True`, set to :const:`False` if selection
        of multiple files is allowed
         
    .. attribute:: caption

        The text to display to the user
        
    The :keyword:`yield` statement of :class:`SelectFile` returns a list
    of selected file names.  This list has only one element when single is
    set to :const:`True`.  Raises a 
    :class:`camelot.core.exception.CancelRequest` when no file was selected.
    
    This action step stores its last location into the :class:`QtCore.QSettings` 
    and uses it as the initial location the next time it is invoked.
    """
    
    def __init__( self, file_name_filter = ''):
        self.file_name_filter = six.text_type(file_name_filter)
        self.single = True
        self.caption = _('Open')

    def gui_run(self, gui_context):
        settings = QtCore.QSettings()
        directory = six.text_type(variant_to_py(settings.value('datasource')))
        directory = os.path.dirname(directory)
        if self.single:
            get_filename = QtGui.QFileDialog.getOpenFileName
        else:
            get_filename = QtGui.QFileDialog.getOpenFileNames
        with hide_progress_dialog( gui_context ):
            selected = get_filename(parent=gui_context.workspace,
                                    caption=six.text_type(self.caption),
                                    directory=directory,
                                    filter=self.file_name_filter)
            if selected:
                if self.single:
                    settings.setValue( 'datasource', py_to_variant(selected))
                    return [six.text_type(selected)]
                else:
                    settings.setValue( 'datasource', py_to_variant(selected[0]))
                    return [six.text_type(fn) for fn in selected]
            else:
                raise CancelRequest()

class SaveFile( ActionStep ):
    """Select a file for saving
    
    :param file_name_filter: Filter on the names of the files that can
        be selected, such as 'All files (*)'.  
        See :class:`QtGui.QFileDialog` for more documentation.

    :param file_name: `None` or the default filename to use

    .. attribute:: caption

        The text to display to the user

    The :keyword:`yield` statement of :class:`SaveFile` returns a file name.
    Raises a :class:`camelot.core.exception.CancelRequest` when no file was
    selected.
    
    This action step stores its last location into the :class:`QtCore.QSettings` 
    and uses it as the initial location the next time it is invoked.
    """

    def __init__(self, file_name_filter='', file_name=None):
        self.file_name_filter = six.text_type(file_name_filter)
        self.file_name = file_name
        self.caption = _('Save')
        
    def gui_run(self, gui_context):
        settings = QtCore.QSettings()
        directory = six.text_type(variant_to_py(settings.value('datasource')))
        directory = os.path.dirname(directory)
        if self.file_name is not None:
            directory = os.path.join(directory, self.file_name)
        get_filename = QtGui.QFileDialog.getSaveFileName
        with hide_progress_dialog( gui_context ):
            selected = get_filename(parent=gui_context.workspace,
                                    caption=six.text_type(self.caption),
                                    directory=directory,
                                    filter=self.file_name_filter)
            if selected:
                settings.setValue('datasource', py_to_variant(selected))
                return six.text_type(selected)
            else:
                raise CancelRequest()

class SelectDirectory(ActionStep):
    """Select a single directory

    .. attribute:: caption
    
        The text to display to the user

    .. attribute:: options
    
        options to pass to :meth:`QtGui.QFileDialog.getExistingDirectory`,
        defaults to :const:`QtGui.QFileDialog.ShowDirsOnly`

    """
    
    def __init__(self):
        self.caption = _('Select directory')
        self.options = QtGui.QFileDialog.ShowDirsOnly
        
    def gui_run(self, gui_context):
        settings = QtCore.QSettings()
        directory = six.text_type(variant_to_py(settings.value('datasource')))
        get_directory = QtGui.QFileDialog.getExistingDirectory
        with hide_progress_dialog( gui_context ):
            selected = get_directory(parent=gui_context.workspace,
                                     caption=six.text_type(self.caption),
                                     directory=directory,
                                     options=self.options)
            if selected:
                settings.setValue('datasource', py_to_variant(selected))
            return six.text_type(selected)