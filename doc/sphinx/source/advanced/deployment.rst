.. _doc-deployment:

#############
  Deployment
#############

:Release: |version|
:Date: |today|

After developing a Camelot application comes the need to deploy the
application, eather at a central location or in a distributed setup.

Building .egg files
===================

Whatever the deployment setup is, it is almost always a good idea to
distribute your application as a single .egg file, containing as much
as possible the dependencies that are likely to change often during
the lifetime of the application.  Resource files (like icons or templates
can be included in this .egg file as well).

Building .egg files is a relatively straightforward process using 
setuptools_ 

A setup.py file for building an .egg of your application could look
like this::

	from setuptools import setup, find_packages

	setup(
	  name = 'movie store',
	  version = '01.01',
	  description = 'Movie Store',
	  author = 'Conceptive Engineering',
	  author_email = 'project-camelot@conceptive.be',
	  url = 'www.conceptive.be',
	  include_package_data = True,
	  packages = find_packages(),
	  py_modules =  ['settings'] )

Which is then build using this command::
	  
	python -O setup.py bdist_egg --exclude-source-files
	
The setup.py script above includes settings.py in the .egg file.  This
is prefered if the settings.py file is going to be the same for all 
deployments.  (Eg.: the database is on a central server accessible
for all)  In some occasions it might be better not to include the settings.py
file into the .egg file, and only put it in your PYTHONPATH at deployment
time. 

.. note::

	The advantage of using .egg files comes when updating the application, simply
	replacing a single .egg file at a central location is enough to migrate all
	your users to the new version.
	
Linux deployment
================

The application can be launched by putting the .egg in the PYTHONPATH
and starting python with the -m option::

	export PYTHONPATH = /mnt/r/movie_store-01.01-py2.5.egg
	python.exe -m movie_store.main
	
Windows deployment
==================

Using .egg files
----------------

First of all python needs to be available on the machines that are going
to run the application.  Notice that for python to be available, it not
necessarily needs to be installed on every machine that runs the application.
Installing python on a shared disk of a central server might just be enough.

Don't forget to install the needed binary libraries as well, like PyQt, PIL.

Also put the .egg file on a shared drive.

Then, the easiest way to proceed is to put a little .vbs bootstrap script on
the shared drive and put shortcuts to it on the desktops of the users.  The
.vbs script can look like this::

	Set WshShell = WScript.CreateObject("WScript.Shell")
	WshShell.Environment("Process").item("PYTHONPATH") = "R:\movie_store-01.01-py2.5.egg;"
	WshShell.Run """R:\Python2.5\pythonw.exe"" -m movie_store.main"

Creating installers
-------------------

When the application needs to be installed at a variety of sites and circumstances,
or it needs to be downloadable as a package, it might be needed to build a real 
windows installer.  This can be done using a combination of py2exe_ and InnoSetup_.

The commercial release of Camelot includes a script that builds an installer from
a Camelot application.

.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _py2exe: http://www.py2exe.org/
.. _InnoSetup: http://www.innosetup.com
