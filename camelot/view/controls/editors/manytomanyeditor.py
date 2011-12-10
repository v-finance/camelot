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

from one2manyeditor import One2ManyEditor
from abstractmanytooneeditor import AbstractManyToOneEditor

from camelot.view.art import Icon
from camelot.view.model_thread import model_function, post
from camelot.core.utils import ugettext as _

class ManyToManyEditor( One2ManyEditor, AbstractManyToOneEditor ):

    direction = 'manytomany'

    def removeSelectedRows( self ):
        """Remove the selected rows in this tableview, but don't delete them"""
        table = self.findChild(QtGui.QWidget, 'table')
        if table:
            self.model.remove_rows( set( map( lambda x: x.row(), table.selectedIndexes() ) ), delete=False)
            self.editingFinished.emit()
