.. _doc-development:

#######################
  Development Guidlines
#######################

:Date: |today|

Python, PyQt and Qt objects
===========================

Python and Qt both have their own way of tracking objects
and deleting them when they are no longer needed :

  * Python does reference counting supported
    by a garbage collector.
    
  * Qt has parent child relations between objects.  When a
    parent object is deleted, all its child objects are
    deleted as well.
    
PyQt merges these two concepts by introducing **ownership**
of objects :

  * Pure python objects are owned by Python, Python takes
    care of their deletion.
    
  * Qt objects wrapped by Python are either:
  
    * owned by Qt when they have a parent object, Qt will
      delete them, when their parent object is deleted
      
    * owned by Python when they have no parent, Python will
      delete them, and trigger the deletion of all their children
      by Qt
      
  * Qt objects that are not wrapped by Python, those are in
    one way or another children of a Qt object that is wrapped
    by Python, they will get deleted by Qt.

The difficult case in this scheme is the case where Qt objects
are wrapped by Python but have a parent object.  This can happen
in two ways :

  * A Qt object is created in python, but with a parent ::
  
		from PyQt4 import QtCore
		
		parent = QtCore.QObject()
		child = QtCore.QObject(parent=parent)
    
    In this case PyQt is able to track when the object is 
    deleted by Qt and raises exceptions accordingly when a
    method of underlying Qt object is called after the deletion ::

		parent = QtCore.QObject()
		child = QtCore.QObject(parent=parent)
		del parent
		print child.objectName()
    
    will raise a RuntimeError: underlying C/C++ object has been deleted.

  * A Qt object is returned from a Qt function that created the object
    without Python being aware of it.  When the object is passed as a 
    return value PyQt will wrap it as a Python object, but is unable
    to track when Qt deletes it ::
    
		from PyQt4 import QtGui
		app = QtGui.QApplication([])
		window = QtGui.QMainWindow()
		statusbar = window.statusBar()
		del window
		statusbar.objectName()

    Will result in a segmentation fault.
    
A segmentation fault will happen in several cases :

  * Python tries to delete a Qt object already deleted by Qt
  * PyQt calls a function of a Qt object already deleted
  * Qt calls a function of a Qt object already deleted by Python
  
In principle, PyQt is able to handle all cases where the object
has been created by Python.  However, when this ownership tracking 
is combined with threading and signal slot connections, a lot 
of corner cases arise in both Qt and PyQt.

To play on safe, these guidelines are used when developing Camelot :

  * Never keep a reference to objects created by Qt having a parent, 
    so only use::
  
		window.statusBar().objectName()
		
  * Keep references to Qt child objects as short as possible, and
    never beyond the scope of a method call.  This is possible because
    qt allows objects to have a name.
    
    so instead of doing ::
    
    	from PyQt4 import QtGui
    	
    	class Parent( QtGui.QWidget ):
    	
    		def __init__( self ):
    			super(Parent, self).__init__()
    			self._child = QtGui.QLabel( parent=self )
    			
    		def do_something( self ):
    			print self._child.objectName()
    			
    this is done ::

    	from PyQt4 import QtGui
    	
    	class Parent( QtGui.QWidget ):
    	
    		def __init__( self ):
    			super(Parent, self).__init__()
    			child = QtGui.QLabel( parent=self )
    			child.setObjectName( 'label' )
    			
    		def do_something( self ):
    		    child = self.findChild( QtGui.QWidget, 'label' )
    		    if child != None:
    				print child.objectName()
    
    should the child object have been deleted by Qt, the findChild method
    will return None, and a segmentation fault is prevented.  An explicit
    check for None is needed, since even if the widget exists, it might
    evaluate to 0 or an empty string.
