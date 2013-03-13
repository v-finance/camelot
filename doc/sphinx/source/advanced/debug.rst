.. _doc-debug:

==========================
Debugging Camelot and PyQt
==========================

Log the SQL Queries
===================

Configure SQLAlchemy to log all queries::

    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

Enable core dumps
=================

Linux
-----

For older gdb versions (pre 7),
copy the gdbinit file from the python Misc folder::

  cp gdbinit ~/.gdbinit
  
use::

  ulimit -c unlimited
  
load core file in gdb::

  gdb /usr/bin/python -c core


In newer gdb versions, Python can run inside gdb:

http://bugs.python.org/issue8032

To give gdb python super powers::

    (gdb) python
    >import sys
    >sys.path.append('Python-2.7.1/Tools/gdb/libpython.py')
    >import libpython
    >reload(libpython)
    >
    >end

https://fedoraproject.org/wiki/Features/EasierPythonDebugging


Windows
-------

 * Install *Debugging tools for Windows* from MSDN

Install 'Debug Diagnostic Tool'

http://stackoverflow.com/questions/27742/finding-the-crash-dump-files-for-a-c-app

http://blogs.msdn.com/b/tess/

Setup Qt Creator 

http://doc.qt.nokia.com/qtcreator-snapshot/creator-debugger-engines.html

 * Install Windows Sysinternals process utilities from MSDN

http://technet.microsoft.com/en-us/sysinternals/bb795533
 
