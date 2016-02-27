#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
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
    from sqlalchemy.orm import mapper, class_mapper, exc
 
    from camelot.model.party import Person
    from camelot_example.model import Movie, VisitorReport
        
    try:
        class_mapper(VisitorsPerDirector)
        return
    except exc.UnmappedClassError:
        pass
    
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

