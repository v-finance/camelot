==========================
Debugging Camelot and PyQt
==========================

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

  python2.6 build.py prepare

Configure the debugging symbols::

  python2.6 configure.py -b /home/tw55413/temp/riverbank/sip_install/ -d /home/tw55413/temp/riverbank/sip_install/ -e /home/tw55413/temp/riverbank/sip_install/ -v  /home/tw55413/temp/riverbank/sip_install/ --debug

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