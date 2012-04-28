# begin column group
from camelot.admin.entity_admin import EntityAdmin
from camelot.admin import table
from camelot.core.utils import ugettext_lazy as _

class VisitorsPerDirector(object):
    
    class Admin(EntityAdmin):
        verbose_name = _('Visitors per director')
        list_display = table.Table( [ table.ColumnGroup( _('Name and Visitors'), ['first_name', 'last_name', 'visitors'] ),
                                      table.ColumnGroup( _('Official'), ['birthdate', 'social_security_number', 'passport_number'] ) ]
                                    )
# end column group

def setup_views():
    from sqlalchemy.sql import select, func, and_
    from sqlalchemy.orm import mapper
 
    from camelot.model.party import Person
    from camelot_example.model import Movie, VisitorReport
        
    s = select([Person.party_id,
                Person.first_name.label('first_name'),
                Person.last_name.label('last_name'),
                Person.birthdate.label('birthdate'),
                Person.social_security_number.label('social_security_number'),
                Person.passport_number.label('passport_number'),
                func.sum( VisitorReport.visitors ).label('visitors'),],
                whereclause = and_( Person.party_id == Movie.director_party_id,
                                    Movie.id == VisitorReport.movie_id),
                group_by = [ Person.party_id, 
                             Person.first_name, 
                             Person.last_name,
                             Person.birthdate,
                             Person.social_security_number,
                             Person.passport_number, ] )
                            
    s=s.alias('visitors_per_director')
    
    mapper( VisitorsPerDirector, s, always_refresh=True )
