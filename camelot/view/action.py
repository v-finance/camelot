#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================

"""The action module contains various QAction classes, representing commands
that can be invoked via menus, toolbar buttons, and keyboard shortcuts."""

from ..core.qt import QtGui, QtWidgets
from camelot.admin.icon import Icon
from camelot.view.art import from_admin_icon, FontIcon
from camelot.core.utils import ugettext as _

class ActionFactory(object):
    """Utility class to generate some default actions we need
    in several places.
    
    Each method of this class, returns a certain action with
    a default text, icon and shortcut.
    """

    icon_copy = FontIcon('copy') # 'tango/16x16/actions/edit-copy.png'
        
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
            action = QtWidgets.QWidgetAction(parent)
        else:
            action = QtGui.QAction(parent)
        action.setText(text)
        if actionicon:
            action.setIcon(from_admin_icon(actionicon).getQIcon())
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
            shortcut=QtGui.QKeySequence.StandardKey.Copy,
            actionicon=Icon('copy'), # 'tango/16x16/actions/edit-copy.png'
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
            shortcut=QtGui.QKeySequence.StandardKey.Paste,
            actionicon=Icon('paste'), # 'tango/16x16/actions/edit-paste.png'
            tip=_('Paste content from clipboard')
        )
        default.update(kwargs)
        return cls.create_action(**default)


