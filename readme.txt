##########
 Camelot
##########

A python GUI framework on top of  Sqlalchemy  and PyQt, inspired by the Django admin interface. 
Start building desktop applications at warp speed, simply by adding some additional information to you 
model definition::

  class Movie(Entity):
    title = Field(Unicode(60), required=True)
    short_description = Field(Unicode(512))
    release_date = Field(Date)
    genre = Field(Unicode(15))

    class Admin(EntityAdmin):
      verbose_name = 'Movie'
      list_display = ['title', 'short_description', 'release_date', 'genre']
      
This piece of code is enough to define your database schema and to create a user friendly 
desktop GUI.

For more information, refer to :

 - `Home page <http://www.python-camelot.com>`_.
 - `Screenshots <http://www.python-camelot.com>`_.
 - `Documentation <http://www.python-camelot.com/docs.html>`_.
