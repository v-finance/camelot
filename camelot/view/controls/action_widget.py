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
Created on May 22, 2010

@author: tw55413
'''

import functools

from PyQt4 import QtGui
from PyQt4 import QtCore

from camelot.view.model_thread import post

class ActionWidget(QtGui.QPushButton):
    """A button that can be pushed to trigger an action"""

    def __init__(self, action, model, parent):
        super(ActionWidget, self).__init__(unicode(action.get_name()))
        if action.get_icon():
            self.setIcon(action.get_icon().getQIcon())
        self._action = action
        self._model = model
        self._current_index = None
        self.clicked.connect(self.triggered)

    @QtCore.pyqtSlot()
    def triggered(self):
        """This slot is triggered when the user triggers the action."""
        if self._current_index:
            self._action.run( functools.partial( self._model._get_object, self._current_index ) )

    @QtCore.pyqtSlot( int )
    def changed(self, current_index ):
        """This slot is triggered when the entity displayed has changed, which
        means the state of the widget needs to be updated"""
        self._current_index = current_index
        post( functools.update_wrapper( functools.partial( self._is_enabled, current_index ), self._is_enabled ),
              self._set_enabled )

    def _set_enabled(self, enabled):
        self.setEnabled(enabled or False)

    def _is_enabled(self, current_index ):
        obj = self._model._get_object( current_index )
        return self._action.enabled(obj)

