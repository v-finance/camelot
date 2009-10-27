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

 - `Home page <http://www.conceptive.be/projects/camelot/>`_.
 - `Screenshots <http://www.conceptive.be/projects/camelot/index.php?option=com_phocagallery&view=category&id=1&Itemid=56>`_.
 - `Documentation <http://www.conceptive.be/projects/camelot/index.php?option=com_content&view=article&id=53&Itemid=27>`_.