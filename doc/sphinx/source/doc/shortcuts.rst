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

.. note:: 

   On Mac OS X, the Ctrl value corresponds to the key Command on the
   Macintosh keyboard.

Main window shortcuts
=====================

   +----------------------+------------------------------------------+
   | :kbd:`Alt-Spacebar`  | Display control menu for the main window |
   +----------------------+------------------------------------------+
   | :kbd:`Ctrl-p`        |                                    Print |
   +----------------------+------------------------------------------+
   | :kbd:`Alt-f v`       |                           Preview (todo) |
   +----------------------+------------------------------------------+

Menus shortcuts
---------------


   +---------------------------------------------------+------------------------------------------------+
   | :kbd:`F10`, :kbd:`Alt`                            |                            Select the menu bar |
   +---------------------------------------------------+------------------------------------------------+
   | :kbd:`Up`, :kbd:`Down`, :kbd:`Left`, :kbd:`Right` |                          Navigate the menu bar |
   +---------------------------------------------------+------------------------------------------------+
   | :kbd:`Tab`                                        |     When menu bar is selected, go to next menu |
   +---------------------------------------------------+------------------------------------------------+
   | :kbd:`Shift-Tab`                                  | When menu bar is selected, go to previous menu |
   +---------------------------------------------------+------------------------------------------------+
   | :kbd:`ENTER`                                      |       Perform the action or open selected menu |
   +---------------------------------------------------+------------------------------------------------+

Navigation pane shortcuts
-------------------------

   +------------------------+-----------------------------+
   | :kbd:`Up`, :kbd:`Down` |  Navigate the entities tree |
   +------------------------+-----------------------------+
   | :kbd:`ENTER`           | Open selected entity (todo) |
   +------------------------+-----------------------------+


Child windows shortcuts
=======================

   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-W`, :kbd:`Ctrl+F4` |        Close the selected child window (todo) |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-F5`                | Restore window size of selected window (todo) |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-Tab`               |               Switch next child window (todo) |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-Shift-Tab`         |        Switch to previous child window (todo) |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`F9`                     |                               Session refresh |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-F9`                |                  Minimize child window (todo) |
   +-------------------------------+-----------------------------------------------+
   | :kbd:`Ctrl-F10`               |                  Maximize child window (todo) |
   +-------------------------------+-----------------------------------------------+

Table view shortcuts
--------------------

   +------------------------+-------------------------+
   | :kbd:`Up`, :kbd:`Down` |           Navigate rows |
   +------------------------+-------------------------+
   | :kbd:`Tab`             |               Next cell |
   +------------------------+-------------------------+
   | :kbd:`Shift-Tab`       |           Previous cell |
   +------------------------+-------------------------+
   | :kbd:`Ctrl-Home`       | First row in the column |
   +------------------------+-------------------------+
   | :kbd:`Ctrl-End`        |  Last row in the column |
   +------------------------+-------------------------+
   | :kbd:`Alt-Home`        |   First cell in the row |
   +------------------------+-------------------------+
   | :kbd:`Alt-End`         |    Last cell in the row |
   +------------------------+-------------------------+
   | :kbd:`Ctrl-Alt-Home`   | First cell of first row |
   +------------------------+-------------------------+
   | :kbd:`Ctrl-Alt-End`    |   Last cell of last row |
   +------------------------+-------------------------+

Form view shortcuts
-------------------

   +---------------+---------------+
   | :kbd:`Ctrl-z` |          Undo |
   +---------------+---------------+
   | :kbd:`Ctrl-c` |          Copy |
   +---------------+---------------+
   | :kbd:`Ctrl-x` |           Cut |
   +---------------+---------------+
   | :kbd:`Ctrl-v` |         Paste |
   +---------------+---------------+
   | :kbd:`Delete` |        Delete |
   +---------------+---------------+
   | :kbd:`Ctrl-b` |   Format bold |
   +---------------+---------------+
   | :kbd:`Ctrl-i` | Format italic |
   +---------------+---------------+
