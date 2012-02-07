.. _doc-threads:

##################
  The Two Threads
##################

Most users of Camelot won't need the information in this Chapter
and can simply enjoy building applications that don't freeze.  However,
if you start customizing your application beyond developing custom
delegates, this information might be crucial to you.

Introduction
------------

A very important aspect of any GUI application is the speed
with which it responds to the user's request.  While it is
acceptable that some actions take some time to complete, an
application freezing for even half a second makes the user
feel uncomfortable.

From an application developer's point of view, potential
freezes are everywhere (open a file, access a database, do
some calculations), so we need a structural approach to
get rid of them.

Two different approaches are possible.  The first approach
is split all possibly blocking operations into small parts and hook 
everything together with events.  This is the approach taken
in some of the QT classes (eg.: the network classes) or in
the Twisted framework.  The second approach is to use multiple
threads of execution and make sure the blocking operations
run in another thread than the GUI.

Events :
 * No multi-threaded programming needed : no deadlocks etc.
 * Every single library you use must support this approach
 
Multiple threads :
 * Scary : potential race conditions and deadlocks
 * Can be used with existing libraries
 
The Camelot framework was developed using the multi-threaded
approach.  This allows to build on top of a large number of
existing libraries (sqlalchemy, PIL, numpy,...) that don't support
the event based approach.

Two Threads
-----------

To keep the problems associated with multi-threaded programming
under control, Camelot runs only two threads for its basic 
operations.  Those threads don't share any data with each other
and exchange information using a message queue (the way 
Erlang advocates).  This ensures there are no deadlocks or 
race conditions.

The first thread, called the GUI Thread contains the QT widgets
and runs the QT event loop.  No blocking operations should take
place in this thread.  The second thread contains all the data,
like objects mapped to the database by sqlalchemy, and is called
the Model Thread.

This approach keeps the problem of application freezes under
control, it won't speed up your application when certain actions
take a long time, but it will ensure the gui remains responsive
during those actions.

The Model Thread
----------------

Since every single operation on a data model is potentially
blocking (eg : getting an attribute of a class mapped to the
database by sqlalchemy might trigger a query to the database
which might be overloaded at that time), the whole data model
lives in a separate thread and every operation on the data model
should take place within this thread.

To keep things simple and avoid the use of locks and data
synchronization between threads, there is only one such thread,
called the Model Thread.

Other threads that want to interact with the model can post
operations to the model thread using its queue ::

	from camelot.view.model_thread import get_model_thread
	
	mt = get_model_thread()
	mt.post(my_operation)
	
where 'my_operation' is a function that will then be executed
within the model thread.	

The GUI Thread
--------------

Now that all potentially blocking operations have been move to the
model thread, we have a GUI Thread that never blocks.  But the GUI
thread will need some data from the model to present to the user.

The GUI thread gets its data by posting an operation to the Model
Thread that strips some data from the model, this data will then be
posted by the Model thread to the GUI thread.

Suppose we want to display the name of the first person in the
database in a QLabel ::

	from camelot.view.model_thread import get_model_thread
	from PyQt4 import QtGui

	class PersonLabel(QtGui.QLabel):
     
	  def __init__(self):
        QtGui.QLabel.__init__(self)   
        mt = get_model_thread()
        mt.post(self.strip_data_from_model, self.put_data_on_label) 
   
	  def strip_data_from_model(self):
        from camelot.model.authentication import Person
        return Person.query.first().name
     
	  def put_data_on_label(self, name):
	    self.setText(name)

When the strip_data_from_model method is posted to the Model Thread, it
will be executed within the Model Thread and its result (the name of the
person) will be posted back to the GUI thread.  Upon arrival of the name
in the GUI thread the function put_data_on_label will be executed within
the GUI thread with as its first argument the name.

In reality, the stripping of data from the model and presenting this data
to the gui is taken care off by the proxy classes in camelot.view.proxy.

Actions
-------

Proxy classes
-------------

  .. image:: ../_static/collection_proxy.png
  
Application speedup
-------------------

