#  ============================================================================
#
#  Copyright (C) 2007-2010 Conceptive Engineering bvba. All rights reserved.
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
from utils import createAction
from camelot.core.utils import ugettext as _

class ActionFactory(object):
    """Utility class to generate some default actions we need
    in several places.
    
    Each method of this class, returns a certain action with
    a default text, icon and shortcut.
    """

    @classmethod
    def copy(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Copy'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.Copy,
            actionicon=Icon('tango/16x16/actions/edit-copy.png'),
            tip=_('Copy to clipboard')
        )
        default.update(kwargs)
        return createAction(**default)

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
        return createAction(**default)
            
    @classmethod
    def view_first(cls, parent, slot, **kwargs):
        default = dict(
            text=_('First'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.MoveToStartOfDocument,
            actionicon=Icon('tango/16x16/actions/go-first.png'),
            tip=_('First')
        )
        default.update(kwargs)
        return createAction(**default)

    @classmethod
    def view_last(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Last'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.MoveToEndOfDocument,
            actionicon=Icon('tango/16x16/actions/go-last.png'),
            tip=_('Last')
        )
        default.update(kwargs)
        return createAction(**default)

    @classmethod
    def view_next(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Next'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.MoveToNextPage,
            actionicon=Icon('tango/16x16/actions/go-next.png'),
            tip=_('Next')
        )
        default.update(kwargs)
        return createAction(**default)

    @classmethod
    def view_previous(cls, parent, slot, **kwargs):
        default = dict(
            text=_('Previous'),
            slot=slot,
            parent=parent,
            shortcut=QtGui.QKeySequence.MoveToPreviousPage,
            actionicon=Icon('tango/16x16/actions/go-previous.png'),
            tip=_('Previous')
        )
        default.update(kwargs)
        return createAction(**default)
    
    @classmethod
    def export_ooxml(cls, parent, slot, **kwargs):
        default = dict(
            text=_('To Word Processor'),
            slot=slot,
            parent=parent,
            actionicon=Icon('tango/16x16/mimetypes/x-office-document.png'),
            tip=_('Open using MS Word or Open Office')
        )
        default.update(kwargs)
        return createAction(**default)
    
    @classmethod
    def refresh(cls, parent, slot=None, **kwargs):
        from refresh import SessionRefresh
        return SessionRefresh(parent)
