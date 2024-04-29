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

"""Set of classes to store internationalization data in the database.  Camelot
applications can be translated by the developer using regular PO files, or by
the user.  In case the user makes a translation, this translation is stored into
the `Translation` table.  This table can be exported to PO files for inclusion
in the development cycle.
"""

from camelot.core.orm import Entity, Session
from camelot.core.utils import ugettext_lazy as _
from camelot.admin.entity_admin import EntityAdmin
from camelot.view.utils import default_language
import camelot.types



from sqlalchemy import sql
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode

import logging
logger = logging.getLogger( 'camelot.model.i18n' )


class Translation( Entity ):
    """Table to store user generated translations or customization.
    """
    
    __tablename__ = 'translation'
    
    language = Column( camelot.types.Language, index = True, nullable = False )
    source = Column( Unicode( 500 ), index = True, nullable = False )
    # value needs to be indexed as well, because when starting up we
    # want to load only the translations that have a value specified
    value = Column( Unicode( 500 ), index = True )
    #cid = Column( INT(), default = 0, index = True )
    #uid = Column( INT(), default = 0, index = True )

    # cache, to prevent too much of the same sql queries
    _cache = dict()

    @classmethod
    def translate( cls, source, language ):
        """Translate source to language, return None if no translation is found"""
        if source:
            key = ( source, language )
            if key in cls._cache:
                return cls._cache[key]
            query = Session().query( cls )
            query = query.filter( sql.and_( cls.source == str( source ),
                                            cls.language == language,
                                            cls.value != None,
                                            cls.value != '' ) )
            translation = query.first()
            if translation:
                cls._cache[key] = translation.value
                return translation.value
            return None
        return ''

    @classmethod
    def translate_or_register( cls, source, language ):
        """Translate source to language, if no translation is found, register the
        source as to be translated and return the source"""
        if source:
            source = str( source )
            translation = cls.translate( source, language )
            if not translation:
                session = Session()
                query = session.query( cls )
                translation = query.filter_by( source = source, 
                                               language = language ).first()
                if not translation:
                    if ( source, language ) not in cls._cache:
                        registered_translation = Translation( source = source, 
                                                              language = language )
                        cls._cache[( source, language )] = source
                        session.flush( [registered_translation] )
                        logger.debug( 'registed %s with id %s' % ( source, registered_translation.id ) )
                return source
            return translation
        return ''

class TranslationAdmin( EntityAdmin ):
    verbose_name_plural = _( 'Translations' )
    form_state = 'right'
    list_display = ['source', 'language', 'value']#, 'uid']
    list_filter = [Translation.language]
    field_attributes = { 'language':{ 'default':default_language } }

Translation.Admin = TranslationAdmin
