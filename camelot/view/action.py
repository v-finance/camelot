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

"""The action module contains various QAction classes, representing commands
that can be invoked via menus, toolbar buttons, and keyboard shortcuts."""

from PyQt4 import QtGui

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

class ActionFactory(object):
    """Utility class to generate some default actions we need
    in several places.
    
    Each method of this class, returns a certain action with
    a default text, icon and shortcut.
    """

    icon_copy = Icon('tango/16x16/actions/edit-copy.png')
        
    @classmethod
    def create_action(*a, **kw):
        """creates and returns a QAction object"""
        # collect params
        parent = kw['parent']
        text = kw['text']
        slot = kw.get('slot', None)
        shortcut = kw.get('shortcut', '')
        actionicon = kw.get('actionicon', '')
        tip = kw.get('tip', '')
        checkable = kw.get('checkable', False)
        #signal = kw.get('signal', 'triggered()')
        widgetaction = kw.get('widgetaction', False)
        if widgetaction:
            action = QtGui.QWidgetAction(parent)
        else:
            action = QtGui.QAction(parent)
        action.setText(text)
        if actionicon:
            action.setIcon(actionicon.getQIcon())
        if shortcut:
            action.setShortcut(shortcut)
        if tip:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect( slot )
        if checkable:
            action.setCheckable(True)
        return action

    @classmethod
    def copy(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Copy'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.Copy,
            actionicon=Icon('tango/16x16/actions/edit-copy.png'),
            tip=_('Duplicate')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def paste(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Paste'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.Paste,
            actionicon=Icon('tango/16x16/actions/edit-paste.png'),
            tip=_('Paste content from clipboard')
        )
        default.update(kwargs)
        return cls.create_action(**default)
