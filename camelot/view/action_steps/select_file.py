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

from PyQt4 import QtGui
  
from camelot.admin.action import ActionStep
from camelot.core.exception import CancelRequest

class SelectOpenFile( ActionStep ):
    
    def __init__( self, file_name_filter = '' ):
        """Select one or more files to open or to process.
        
        :param file_name_filter: Filter on the names of the files that can
            be selected, such as 'All files (*)'.  
            See :class:`QtGui.QFileDialog` for more documentation.
        
        .. attribute:: single
            defaults to :keyword:`True`, set to :keyword:`False` if selection
            of multiple files is allowed
            
        The :keyword:`yield` statement of :class:`SelectOpenFile` returns a list
        of selected file names.  This list has only one element when single is
        set to :keyword:`True`.  Raises a 
        :class:`camelot.core.exception.CancelRequest` when no file was selected.
        """
        self.file_name_filter = file_name_filter
        self.single = True
    
    def gui_run( self, gui_context ):
        if self.single == False:
            file_names = [unicode(fn) for fn in QtGui.QFileDialog.getOpenFileNames( filter = self.file_name_filter )]
            if not file_names:
                raise CancelRequest()
        else:
            file_name = unicode( QtGui.QFileDialog.getOpenFileName( filter = self.file_name_filter ) )
            if not file_name:
                raise CancelRequest()
            file_names = [file_name]
        return file_names
