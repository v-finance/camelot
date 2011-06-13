from camelot.admin.entity_admin import EntityAdmin
from camelot.core.utils import ugettext_lazy as _

class VisitorsPerDirector(object):
    
    class Admin(EntityAdmin):
        verbose_name = _('Visitors per director')
        list_display = ['first_name', 'last_name', 'visitors']
        

def setup_views():
    from sqlalchemy.sql import select, func, and_
    from sqlalchemy.orm import mapper
 
    from camelot.model.authentication import Person
    from camelot_example.model import Movie, VisitorReport
    
    s = select([Person.party_id,
                Person.first_name.label('first_name'),
                Person.last_name.label('last_name'),
                func.sum( VisitorReport.visitors ).label('visitors'),],
                whereclause = and_( Person.party_id == Movie.director_party_id,
                                    Movie.id == VisitorReport.movie_id),
                group_by = [ Person.party_id, 
                             Person.first_name, 
                             Person.last_name ] )
                            
    s=s.alias('visitors_per_director')
    
    mapper( VisitorsPerDirector, s, always_refresh=True )
