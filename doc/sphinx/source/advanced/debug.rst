.. _doc-debug:

==========================
Debugging Camelot and PyQt
==========================

Log the SQL Queries
===================

Configure SQLAlchemy to log all queries::

    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

Buiding Qt
==========

Configure::

    ./configure -prefix /home/tw55413/temp/nokia/qt_install/ -debug -opensource
  
Standard make::

    make
    make install

Building SIP
============

Prepare the build::

     python build.py prepare

Configure the debugging symbols::

     python configure.py -b /home/tw55413/temp/riverbank/sip_install/ -d /home/tw55413/temp/riverbank/sip_install/ -e /home/tw55413/temp/riverbank/sip_install/ -v  /home/tw55413/temp/riverbank/sip_install/ --debug

Standard make::

     make
     make install

Building PyQt
=============

Configure::

  export PYTHONPATH=../sip_install/
  python configure.py --debug --trace -b /home/tw55413/temp/riverbank/pyqt_install/ -d /home/tw55413/temp/riverbank/pyqt_install/ -p /home/tw55413/temp/riverbank/pyqt_install -q /home/tw55413/temp/nokia/qt_install/bin/qmake --confirm-license 
  make
  make install

Using the libraries
===================

set the environment variables::

  export LD_LIBRARY_PATH=/home/tw55413/temp/nokia/qt_install/lib/
  export PYTHONPATH=.:/home/tw55413/temp/riverbank/sip_install/:/home/tw55413/temp/riverbank/pyqt_install/
  
launch the python application::

  python main.py

Then start Qt Creator, choose debug, and attach to the running process

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
 
