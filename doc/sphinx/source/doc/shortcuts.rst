.. _doc-shortcuts:

####################
  Camelot Shortcuts 
####################

:Release: |version|
:Date: |today|

This page contains the various shortcuts available in Camelot and their
meanings. Camelot graphical user interface (GUI) is based on PyQt4 widgets,
which are themselve based on Qt4. Qt4 defines what is called actions, which are
basically common commands that can be invoked via menus, toolbar buttons, and
keyboard shortcuts.

Qt4 (and thus PyQt4) comes with a set of standard shortcuts (through the
convenience enumeration [QKeySequence.StandardKey] [1]) for various widgets.
It is possible then that a keyboard shortcut not mentioned here performs a
desirable action by default.

[1]: http://doc.trolltech.com/4.4/qkeysequence.html#StandardKey-enum

Following are the shortcuts available in Camelot.

Note that on Mac OS X, the Ctrl value corresponds to the key Command on the
Macintosh keyboard.

Main window shortcuts
=====================

    ALT+SPACEBAR.....Display control menu for the main window
    CTRL+P..............................................Print
    ALT+F then V...............................Preview (todo)

Menus shortcuts
---------------

    F10 or ALT...........................................Select the menu bar
    UP, DOWN, LEFT, RIGHT..............................Navigate the menu bar
    TAB...........................When menu bar is selected, go to next menu
    SHIFT+TAB.................When menu bar is selected, go to previous menu
    ENTER...........................Perform the action or open selected menu

Navigation pane shortcuts
-------------------------

    UP, DOWN......Navigate the entities tree
    ENTER........Open selected entity (todo)


Child windows shortcuts
=======================

    CTRL+W or CTRL+F4............Close the selected child window (todo)
    CTRL+F5...............Restore window size of selected window (todo)
    CTRL+TAB............................Switch next child window (todo)
    CTRL+SHIFT+TAB...............Switch to previous child window (todo)
    F9..................................................Session refresh
    CTRL+F9................................Minimize child window (todo)
    CTRL+F10...............................Maximize child window (todo)

table view shortcuts
--------------------

    UP, DOWN....................Navigate rows
    TAB.............................Next cell
    SHIFT+TAB...................Previous cell
    CTRL+HOME.........First row in the column
    CTRL+END...........Last row in the column
    ALT+HOME............First cell in the row
    ALT+END..............Last cell in the row
    CTRL+ALT+HOME.....First cell of first row
    CTRL+ALT+END........Last cell of last row

Form view shortcuts
-------------------

    CTRL+Z..............Undo
    CTRL+C..............Copy
    CTRL+X...............Cut
    CTRL+V.............Paste
    DELETE............Delete
    CTRL+B.......Format bold
    CTRL+I.....Format italic
