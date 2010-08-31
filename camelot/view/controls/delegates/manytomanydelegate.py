#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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

#from PyQt4 import QtCore

from camelot.view.controls import editors
from one2manydelegate import One2ManyDelegate


class ManyToManyDelegate(One2ManyDelegate):
    """
  .. image:: ../_static/manytomany.png
  """

    def createEditor(self, parent, option, index):
        editor = editors.ManyToManyEditor(parent=parent, **self.kwargs)
        self.setEditorData(editor, index)
        self.connect(editor, editors.editingFinished, self.commitAndCloseEditor)
        return editor

    def commitAndCloseEditor(self):
        editor = self.sender()
        #self.emit(QtCore.SIGNAL('commitData(QWidget*)'), editor)
        self.commitData.emit(editor)

    def setModelData(self, editor, model, index):
        if editor.getModel():
            model.setData(index, editor.getModel().collection_getter)
