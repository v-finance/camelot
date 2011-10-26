#  ============================================================================
#
#  Copyright (C) 2007-2011 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================
from camelot.model import metadata
from camelot.admin.action import Action
import camelot.types
from elixir.entity import Entity
from elixir.options import using_options
from elixir.fields import Field
from sqlalchemy.types import Unicode, INT
"""Set of classes to enable internationalization of the user interface"""

__metadata__ = metadata

from camelot.admin.entity_admin import EntityAdmin
from camelot.view.art import Icon
from camelot.core.utils import ugettext_lazy as _
from camelot.view.utils import default_language

import logging
logger = logging.getLogger( 'camelot.model.i18n' )

def tr( source ):
    from PyQt4 import QtCore
    language = unicode( QtCore.QLocale().name() )
    return Translation.translate_or_register( source, language )

class ExportAsPO( Action ):

    verbose_name = _('PO Export')
    icon = Icon('tango/16x16/actions/document-save.png')

    def model_run( self, model_context ):
        from camelot.view.action_steps import SelectFile
        select_file = SelectFile()
        select_file.existing = False
        filenames = yield select_file
        for filename in filenames:
            file = open(filename, 'w')
            for translation in model_context.get_collection():
                file.write( (u'msgid  "%s"\n'%translation.source).encode('utf-8') )
                file.write( (u'msgstr "%s"\n\n'%translation.value).encode('utf-8') )
                
        
class Translation( Entity ):
    using_options( tablename = 'translation' )
    language = Field( camelot.types.Language, index = True )
    source = Field( Unicode( 500 ), index = True )
    # value needs to be indexed as well, because when starting up we
    # want to load only the translations that have a value specified
    value = Field( Unicode( 500 ), index = True )
    cid = Field( INT(), default = 0, index = True )
    uid = Field( INT(), default = 0, index = True )

    # cache, to prevent too much of the same sql queries
    _cache = dict()

    class Admin( EntityAdmin ):
        verbose_name_plural = _( 'Translations' )
        form_size = ( 700, 150 )
        section = 'configuration'
        list_display = ['source', 'language', 'value', 'uid']
        list_filter = ['language']
        list_actions = [ExportAsPO()]
        field_attributes = {'language':{'default':default_language}}

    @classmethod
    def translate( cls, source, language ):
        """Translate source to language, return None if no translation is found"""
        if source:
            key = ( source, language )
            if key in cls._cache:
                return cls._cache[key]
            translation = cls.query.filter_by( source = unicode( source ), language = language ).filter( Translation.uid != 0 ).first()
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
            source = unicode( source )
            translation = cls.translate( source, language )
            if not translation:
                if not cls.query.filter_by( source = source, language = language ).first():
                    if ( source, language ) not in cls._cache:
                        from elixir import session
                        registered_translation = Translation( source = source, language = language )
                        cls._cache[( source, language )] = source
                        session.flush( [registered_translation] )
                        logger.debug( 'registed %s with id %s' % ( source, registered_translation.id ) )
                return source
            return translation
        return ''


