#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""
Helper functions to search through a collection of entities
"""
import logging

logger = logging.getLogger('camelot.view.search')

import camelot.types

def create_entity_search_query_decorator(admin, text):
    """create a query decorator to search through a collection of entities
    @param admin: the admin interface of the entity
    @param text: the text to search for
    @return: a function that can be applied to a query to make the query filter
    only the objects related to the requested text
    """
    from elixir import entities
    from sqlalchemy import orm

    if len(text.strip()):
        from sqlalchemy import Unicode, or_
        # arguments for the where clause
        args = []
        # join conditions : list of join entities
        joins = []
        search_tables = [admin.entity.table]
        for entity in entities:
            if issubclass(admin.entity, entity):
                search_tables.append(entity.table)

        def append_column(c):
            if issubclass(c.type.__class__, camelot.types.Color):
                pass
            elif issubclass(c.type.__class__, camelot.types.File):
                pass
            elif issubclass(c.type.__class__, camelot.types.Code):
                codes = text.split('.')
                args.append(c.like(['%'] + codes + ['%']))
                args.append(c.like(['%'] + codes))
                args.append(c.like(codes + ['%']))
            elif issubclass(c.type.__class__, camelot.types.VirtualAddress):
                args.append(c.like(('%','%'+text+'%')))
            elif issubclass(c.type.__class__, camelot.types.Image):
                pass
            elif issubclass(c.type.__class__, (Unicode, )) or \
                            (hasattr(c.type, 'impl') and \
                             issubclass(c.type.impl.__class__, (Unicode, ))):
                logger.debug('look in column : %s'%c.name)
                args.append(c.like('%'+text+'%'))

        for table in search_tables:
            for c in table._columns:
                append_column(c)

        for column_name in admin.list_search:
            path = column_name.split('.')
            target = admin.entity
            for p in path:
                mapper = orm.class_mapper(target)
                property = mapper.get_property(p, resolve_synonyms=True)
                if isinstance(property, orm.properties.PropertyLoader):
                    joins.append(getattr(target, p))
                    target = property._get_target().class_
                else:
                    append_column(property.columns[0])
                    #args.append(property.columns[0].like('%'+text+'%'))

        logger.debug('query joins : %s'%str(joins))
        logger.debug('query args : %s'%str(args))

        def create_query_decorator(joins, args):

            def query_decorator(q):
                for join in joins:
                    q = q.join(join)
                if len(args):
                    if len(args)>1:
                        q = q.filter(or_(*args))
                    else:
                        q = q.filter(args[0])
                return q

            return query_decorator

        return create_query_decorator(joins, args)
