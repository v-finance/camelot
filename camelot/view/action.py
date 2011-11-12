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

"""The action module contains various QAction classes, representing commands
that can be invoked via menus, toolbar buttons, and keyboard shortcuts."""

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from camelot.view.art import Icon
from camelot.core.utils import ugettext as _

class ActionFactory(object):
    """Utility class to generate some default actions we need
    in several places.
    
    Each method of this class, returns a certain action with
    a default text, icon and shortcut.
    """

    icon_backup = Icon('tango/16x16/actions/document-save.png')
    icon_restore = Icon('tango/16x16/devices/drive-harddisk.png')
    icon_pgsetup = Icon('tango/16x16/actions/document-properties.png')
    icon_print = Icon('tango/16x16/actions/document-print.png')
    icon_preview = Icon('tango/16x16/actions/document-print-preview.png')
    icon_copy = Icon('tango/16x16/actions/edit-copy.png')
    icon_new = Icon('tango/16x16/actions/document-new.png')
    icon_delete = Icon('tango/16x16/places/user-trash.png')
    icon_excel = Icon('tango/16x16/mimetypes/x-office-spreadsheet.png')
    icon_word = Icon('tango/16x16/mimetypes/x-office-document.png')
    icon_mail = Icon('tango/16x16/actions/mail-message-new.png')
    icon_import = Icon('tango/16x16/mimetypes/text-x-generic.png')
    icon_help = Icon('tango/16x16/apps/help-browser.png')
        
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
        return cls.create_action(**default)

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
        return cls.create_action(**default)

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
        return cls.create_action(**default)

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
        return cls.create_action(**default)
    
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
        return cls.create_action(**default)
    
    @classmethod
    def backup(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('&Backup'),
            slot=slot,
            actionicon=cls.icon_backup,
            tip=_('Backup the database')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def restore(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('&Restore'),
            slot=slot,
            actionicon=cls.icon_restore,
            tip=_('Restore the database from a backup')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def page_setup(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Page Setup...'),
            slot=slot,
            actionicon=cls.icon_pgsetup,
            tip=_('Page Setup...')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def print_(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Print...'),
            slot=slot,
            shortcut=QtGui.QKeySequence.Print,
            actionicon=cls.icon_print,
            tip=_('Print...')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def print_preview(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Print Preview'),
            slot=slot,
            actionicon=cls.icon_preview,
            tip=_('Print Preview')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def exit(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('E&xit'),
            slot=slot,
            shortcut=QtGui.QKeySequence.Quit,
            actionicon=Icon('tango/16x16/actions/system-shutdown.png'),
            tip=_('Exit the application')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def duplicate(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('&Copy'),
            slot=slot,
            shortcut=QtGui.QKeySequence.Copy,
            actionicon=cls.icon_copy,
            tip=_("Duplicate the selected rows")
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def select_all(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Select &All'),
            slot=slot,
            shortcut=QtGui.QKeySequence.SelectAll,
            tip=_('Select all rows in the table'),
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def about(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('&About'),
            slot=slot,
            actionicon=Icon('tango/16x16/mimetypes/application-certificate.png'),
            tip=_("Show the application's About box")
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def whats_new(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('&What\'s new'),
            slot=slot,
            actionicon=Icon('tango/16x16/status/software-update-available.png'),
            tip=_("Show the What's New box")
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def affiliated_website(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Affiliated website'),
            slot=slot,
            actionicon=Icon('tango/16x16/apps/internet-web-browser.png'),
            tip=_('Go to the affiliated website')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def remote_support(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Remote support'),
            slot=slot,
            actionicon=Icon('tango/16x16/devices/video-display.png'),
            tip=_('Let the support agent take over your desktop')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def help(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Help'),
            slot=slot,
            shortcut=QtGui.QKeySequence.HelpContents,
            actionicon=cls.icon_help,
            tip=_('Help content')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def new(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('New'),
            slot=slot,
            shortcut=QtGui.QKeySequence.New,
            actionicon=cls.icon_new,
            tip=_('New')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def delete(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Delete'),
            slot=slot,
            shortcut=QtGui.QKeySequence.Delete,
            actionicon=cls.icon_delete,
            tip=_('Delete')
        )
        default.update(kwargs)
        return cls.create_action(**default)
 
    @classmethod
    def update_values(cls, parent, slot, **kwargs):
        default = dict(
            parent = parent,
            text = _('Replace field contents'),
            slot = slot,
            tip = _('Replace the content of a field for all rows in a selection')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def merge_document(cls, parent, slot, **kwargs):
        default = dict(
            parent = parent,
            text = _('Merge document'),
            slot = slot,
            tip = _('Merge a template document with all rows in a selection')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def export_excel(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Export to MS Excel'),
            slot=slot,
            actionicon=cls.icon_excel,
            tip=_('Export to MS Excel')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def export_word(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Export to MS Word'),
            slot=slot,
            actionicon=cls.icon_word,
            tip=_('Export to MS Word')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def export_mail(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Send by e-mail'),
            slot=slot,
            actionicon=cls.icon_mail,
            tip=_('Send by e-mail')
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def import_file(cls, parent, slot, **kwargs):
        default = dict(
            parent=parent,
            text=_('Import from file'),
            slot=slot,
            actionicon=cls.icon_import,
            tip=_('Import from file')
        )
        default.update(kwargs)
        return cls.create_action(**default)
        
    @classmethod
    def refresh(cls, parent, slot, **kwargs):
        default = dict(
            parent = parent,
            text = _('Refresh'),
            slot = slot,
            shortcut = QtGui.QKeySequence( Qt.Key_F9 ),
            icond = Icon('tango/16x16/actions/view-refresh.png'),
        )
        default.update(kwargs)
        return cls.create_action(**default)

    @classmethod
    def new_tab(cls, parent, slot, **kwargs):
        default = dict(
            parent = parent,
            text = _('Open in New Tab'),
            slot = slot
        )
        default.update(kwargs)
        return cls.create_action(**default)
