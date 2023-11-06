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


from camelot.admin.action import Action
from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import FontIcon

class ImportCovers( Action ):
    verbose_name = _('Import cover images')
    name = 'import_covers'
    icon = FontIcon('image')
    
# begin select files
    def model_run( self, model_context ):
        from camelot.view.action_steps import ( SelectFile, 
                                                UpdateProgress, 
                                                Refresh,
                                                FlushSession )
        
        select_image_files = SelectFile( 'Image Files (*.png *.jpg);;All Files (*)' )
        select_image_files.single = False
        file_names = yield select_image_files
        file_count = len( file_names )
# end select files
# begin create movies
        import os
        from sqlalchemy import orm
        from camelot.core.orm import Session
        from camelot_example.model import Movie
              
        movie_mapper = orm.class_mapper( Movie )
        cover_property = movie_mapper.get_property( 'cover' )
        storage = cover_property.columns[0].type.storage
        session = Session()

        for i, file_name in enumerate(file_names):
            yield UpdateProgress( i, file_count )
            title = os.path.splitext( os.path.basename( file_name ) )[0]
            stored_file = storage.checkin( str( file_name ) )
            movie = Movie( title = str( title ) )
            movie.cover = stored_file
            
        yield FlushSession( session )
# end create movies
# begin refresh
        yield Refresh()
# end refresh

