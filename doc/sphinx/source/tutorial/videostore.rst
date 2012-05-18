.. _tutorial-videostore:

########################################
 Creating a Movie Database Application
########################################

In this tutorial we will create a fully functional movie database application
with Camelot. We assume Camelot is properly :ref:`installed <doc-install>`.
An all in one installer for Windows is available as an SDK to develop Camelot
applications `(Python SDK) <http://www.conceptive.be/python-sdk.html>`_.

Starting a New Project
======================

We begin with the creation of a new project. Open your favourite command prompt
(or shell) and go to the directory in which the new project should be created.
Typing the following command::

  python -m camelot.bin.camelot_admin

A dialog appears where the basic information of the application can be
filled in.

.. image:: /_static/actionsteps/change_object.png

Press `OK` to generate the source code of the project.

The folder :file:`videostore` should appear in your the directory you are 
working in. We will be working the Python modules created and put inside this 
directory.

Main Window and Views
=====================

:option:`camelot_admin` created some modules for us. Let's focus on the
one called :file:`main.py` which contains the entry point of your Camelot
application. If you launch it::

  set PYTHONPATH=.
  python main.py

your `PyQt <http://www.riverbankcomputing.co.uk/software/pyqt/intro>`_
:abbr:`Graphical User Interface <GUI>` should look like the one we show in the
picture below:

.. image:: ../_static/picture1.png

The application has menus, a toolbar, a left navigation pane, and a central
area, where default the `Home` tab is opened, on which nothing is currently displayed.

The navigation pane has its first `section` expanded. 

.. image:: ../_static/picture2.png

.. note::

   Camelot uses `sections` to group `models`.  Each button in the navigation
   pane represents a `section`, and each entry of the navigation tree is part
   of this section.

Select any other section-button by clicking on it, and see this section expand, 
minimizing the previous section.
The links in a section are `entities`, and we will talk about them later.  (Generally speaking,
an `entity` represents a single table in a database.)

Notice that the application disables most of the menus and the toolbar
buttons. When we click on an entity, more options become available.
So let's click on the entity ``Persons`` of the section ``Relations``.
The table view of the entity appears in a tab next to the `Home` tab.
Entities are opened in the active tab, unless
they are opened by selecting `Open in New Tab` from the context menu (right click) 
of the entity link, which will obviously open a new tab to right.
Tabs can be closed by clicking the `X` in the tab itself.

.. image:: ../_static/picture3.png

Each row is a record with some fields that we can edit (others might not be
editable). Let's now add a new row by clicking on the new icon (icon farthest the 
the left in the toolbar above the navigation pane).

.. image:: ../_static/picture4.png

We now see a new window, containing a form view with additional fields. 
Forms label **required** fields in bold.

.. image:: ../_static/picture5.png

Fill in a first and last name, and close the form. Camelot will automatically
validate and echo the changes to the database. We can reopen the form by
clicking on the blue folder icon in the first column of each row of the table. Notice
also that there is now an entry in our table.

.. image:: ../_static/picture6.png

That's it for basic usages of the interface. Next we will write code for our
database model.


Creating the Movie Model
========================

Let's first take a look at the :file:`settings.py` in our project directory.
There is a function, ``ENGINE``, which returns a call to the `create_engine 
<http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine>`_ 
SQLAlchemy function, containing a :abbr:`Uniform Resource Identifier URI`. 
That's the database your Camelot application will be connecting too. 
Camelot provides a default ``sqlite`` URI scheme. But you can set your own.

If you set a database file that does not exist it will be created in the
directory from which the application is *launched*. Keep this in mind
if you plan to deploy your application by means of an installer on
Microsoft Windows Vista or newer, because the Program Files folder is not
writable. Choose a location that is writable to the application, such
as the user's AppData folder, or a shared folder in case of multiple users
needing to access the same data.

Now we can look at :file:`model.py`. Camelot has already imported some classes
for us. They are used to create our entities. Let's say we want a movie entity
with a ``title``, a short ``description``, a ``release date``, and a
``genre``.

The aforementioned specifications translate into the following Python code,
that we add to our model.py module::

  from sqlalchemy import Unicode, Date
  from sqlalchemy.schema import Column
  from camelot.core.orm import Entity
  from camelot.admin.entity_admin import EntityAdmin
  
  class Movie( Entity ):
    
      __tablename__ = 'movie'
    
      title = Column( Unicode(60), nullable = False )
      short_description = Column( Unicode(512) )
      release_date = Column( Date() )
      genre = Column( Unicode(15) )

.. note::

   The complete source code of this tutorial can be found in the
   :file:`camelot_example` folder of the Camelot source code.
   
``Movie`` inherits ``Entity``.  ``Entity`` is the base class for all objects
that should be stored in the database.  We use the ``__tablename__`` attribute to
to name the table ourselves in which the data will be stored, otherwise a 
default tablename would have been used.

Our entity holds four fields that are stored in columns in the table.

::

  title = Column( Unicode(60), nullable = False )

``title`` holds up to 60 unicode characters, and cannot be left empty:

::

  short_description = Column( Unicode(512) )

``short_description`` can hold up to 512 characters:

::

  release_date = Column( Date() )
  genre = Column( Unicode(15) )

``release_date`` holds a date, and ``genre`` up to 15 unicode characters:

For more information about defining models, refer to the
`SQLAlchemy Declarative extension <http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html>`_. 

The different `SQLAlchemy <http://www.sqlalchemy.org>`_ column types used 
are described `here <http://docs.sqlalchemy.org/en/rel_0_7/core/types.html>`_.
Finally, custom Camelot fields are documented in the API.

Let's now create an ``EntityAdmin`` subclass


The EntityAdmin Subclass
========================

We have to tell Camelot about our entities, so they show up in the 
:abbr:`GUI (Graphical User Interface)`.
This is one of the purposes of :class:`camelot.admin.entity_admin.EntityAdmin` 
subclasses. After adding the ``EntityAdmin`` subclass, our ``Movie`` class now 
looks like this::

  class Movie( Entity ):
    
      __tablename__ = 'movie'
    
      title = Column( Unicode(60), nullable = False )
      short_description = Column( Unicode(512) )
      release_date = Column( Date() )
      genre = Column( Unicode(15) )

      def __unicode__( self ):
          return self.title or 'Untitled movie'

      class Admin( EntityAdmin ):
          verbose_name = 'Movie'
          list_display = ['title', 'short_description', 'release_date', 'genre']


We made ``Admin`` an inner class to strengthen the link between it and the
``Entity`` subclass. Camelot does not force us. Assign your ``EntityAdmin``
class to the ``Admin`` ``Entity`` member to put it somewhere else. 

``verbose_name`` will be the label used in navigation trees.

The last attribute is interesting; it holds a list containing the fields we
have defined above. As the name suggests, ``list_display`` tells Camelot to
only show the fields specified in the list. ``list_display`` fields are also
taken as the default fields to show on a form.

In our case we want to display four fields: ``title``, ``short_description``,
``release_date``, and ``genre`` (that is, all of them.)

The fields displayed on the form can optionally be specified too in the ``form_display``
attribute.

We also add a ``__unicode__()`` method that will return either the title of the
movie entity or ``'Untitled movie'`` if title is empty.  The ``__unicode__()``
method will be called in case Camelot needs a textual representation of an 
object, such as in a window title.

Let's move onto the last piece of the puzzle.

Configuring the Application
===========================

We are now working with :file:`application_admin.py`.  One of
the tasks of :file:`application_admin.py` is to specify the sections in
the left pane of the main window.

Camelot defined a class, ``MyApplicationAdmin``, for us. This class is a
subclass of class:`camelot.admin.application_admin.ApplicationAdmin`, which is 
used to control the overall look and feel of every Camelot application.

To change sections in the left pane of the main window, simply overwrite the
``get_sections`` method, to return a list of the desired sections.  By default
this method contains::

  def get_sections(self):
    from camelot.model.memento import Memento
    from camelot.model.party import Person, Organization
    from camelot.model.i18n import Translation
    return [Section('Relation',
		    self,
                    Icon('tango/22x22/apps/system-users.png'),
                    items = [Person, Organization]),
            Section('Configuration',
		    self,
                    Icon('tango/22x22/categories/preferences-system.png'),
                    items = [Memento, Translation])
            ]
            
which will display two buttons in the navigation pane, labelled ``'Relations'``
and ``'Configurations'``, with the specified icon next to each label. And yes,
the order matters.

We need to add a new section for our ``Movie`` entity, this is done by
extending the list of sections returned by the ``get_sections`` method with a
Movie section::

	Section('Movies',
		self,
                Icon('tango/22x22/mimetypes/x-office-presentation.png'),
                items = [Movie])

The constructor of a section object takes the name of the section, a reference
to the application admin object, the icon to be used and the items in the 
section.  The items is a list of the entities for which a table view should 
shown. 

Camelot comes with the `Tango <http://tango.freedesktop.org/Tango_Icon_Library>`_
icon collection; we use a suitable icon for our movie section.

The resulting method now becomes::

  def get_sections(self):
    from camelot.model.memento import Memento
    from camelot.model.authentication import Person, Organization
    from camelot.model.i18n import Translation    
    from model import Movie
    return [Section('Movies', 
		    self,
                    Icon('tango/22x22/mimetypes/x-office-presentation.png'),
                    items = [Movie]),
            Section('Relation',
		    self,
                    Icon('tango/22x22/apps/system-users.png'),
                    items = [Person, Organization]),
            Section('Configuration',
		    self,
                    Icon('tango/22x22/categories/preferences-system.png'),
                    items = [Memento, Translation])
            ]
    
We can now try our application.

We see a new button the navigation pane labelled `'Movies'`. Clicking on it
fills the navigation tree with the only entity in the movies's section.
Clicking on this tree entry opens the table view. And if we click on the blue
folder of each record, a form view appears as shown below.

.. image:: ../_static/picture7.png

That's it for the basics of defining an entity and setting it for display in
Camelot. Next we look at relationships between entities.

Relationships
=============

We will be using SQLAlchemy's :class:`sqlalchemy.orm.relationship` API.  We'll
relate a director to each movie.  So first we need a ``Director`` entity. We 
define it as follows::
                   
    class Director( Entity ):
    
        __tablename__ = 'director'
  
        name = Column( Unicode( 60 ) )

Even if we define only the ``name`` column, Camelot adds an ``id`` column
containing the primary key of the ``Director`` Entity.  It does so because we
did not define a primary key ourselves.  This primary key is an integer number,
unique for each row in the ``director`` table, and as such unique for each 
``Director`` object.

Next, we add a reference to this primary key in the movie table, this is called
the foreign key.  This foreign key column, called ``director_id`` will be an 
integer number as well, with the added constraint that it can only contain
values that are present in the ``director`` table its ``id`` column.

Because the ``director_id`` column is only an integer, we need to add the
``director`` attribute of type ``relationship``.  This will allow us to use
the ``director`` property as a ``Director`` object related to a ``Movie``
object.  The ``relationship`` attribute will find out about the ``director_id``
column and use it to attach a ``Director`` object to a ``Movie`` object ::

    from sqlalchemy.schema import ForeignKey
    from sqlalchemy.orm import relationship
  
    class Movie( Entity ):
	
	__tablename__ = 'movie'
	
	title = Column( Unicode( 60 ), required=True )
	short_description = Column( Unicode( 512 ) )
	release_date = Column( Date() )
	genre = Column( Unicode( 15 ) )
	
	director_id = Column( Integer, ForeignKey('director.id') )
	director = relationship( 'Director' )
      
	class Admin( EntityAdmin ):
	    verbose_name =  'Movie'
	    list_display = [ 'title',
			     'short_description',
			     'release_date',
			     'genre',
			     'director' ]
      
	def __unicode__( self ):
	    return self.title or 'untitled movie'

We also inserted ``'director'`` in ``list_display``.

To be able to have the movies accessible from a director, a ``relationship`` is
defined on the ``Director`` entity as well.  This will result in a ``movies``
attribute for each director, containing a list of movie objects.

Our ``Director`` entity needs an administration class as well. We will also 
add ``__unicode__()`` method as suggested above. The entity now looks as 
follows::

    class Director( Entity ):
	__tablename__ = 'director'
    
	name = Column( Unicode(60) )
	movies = relationship( 'Movie' )
    
	class Admin( EntityAdmin ):
	    verbose_name = 'Director'
	    list_display = [ 'name' ]
    
	def __unicode__(self):
	    return self.name or 'unknown director'

For completeness the two entities are once again listed below::

    class Movie( Entity ):
	
	__tablename__ = 'movie'
	
	title = Column( Unicode( 60 ), required=True )
	short_description = Column( Unicode( 512 ) )
	release_date = Column( Date() )
	genre = Column( Unicode( 15 ) )
	
	director_id = Column( Integer, ForeignKey('director.id') )
	director = relationship( 'Director' )
      
	class Admin( EntityAdmin ):
	    verbose_name =  'Movie'
	    list_display = [ 'title',
			     'short_description',
			     'release_date',
			     'genre',
			     'director' ]
      
	def __unicode__( self ):
	    return self.title or 'untitled movie'

    class Director( Entity ):
	__tablename__ = 'director'
    
	name = Column( Unicode(60) )
	movies = relationship( 'Movie' )
    
	class Admin( EntityAdmin ):
	    verbose_name = 'Director'
	    list_display = [ 'name' ]
    
	def __unicode__(self):
	    return self.name or 'unknown director'

The last step is to fix :file:`application_admin.py` by adding the following
lines to the Director entity to the Movie section::

	Section( 'Movies', 
		 self,
                 Icon( 'tango/22x22/mimetypes/x-office-presentation.png' ),
                 items = [ Movie, Director ])

This takes care of the relationship between our two entities. Below is the new
look of our video store application.

.. image:: ../_static/picture8.png

We have just learned the basics of Camelot, and have a nice movie database
application we can play with. In another tutorial, we will learn more advanced
features of Camelot.
