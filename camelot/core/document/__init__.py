#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
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
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================
"""Decorators to enhance the docstrings of classes
"""

from sqlalchemy import inspect, orm, util

from ...admin.entity_admin import EntityAdmin

def document_classes(classes):
    """Append mapped property documentation to the docstring of a class
    
    :param classes: the list of classes to document
    """

    def document_property( cls, key, prop ):
        if isinstance(prop, orm.ColumnProperty):
            attrs = EntityAdmin.get_sql_field_attributes(prop.columns)
            python_type = attrs.get('python_type', None)
            docstrings = []
            if prop.doc:
                docstrings.append( prop.doc )
            if isinstance(python_type, type):
                docstrings.append(  python_type.__name__ )
            if attrs.get('nullable', True):
                docstrings.append(  'not required' )
            else:
                docstrings.append(  'required' )
            length = attrs.get('length', None)
            if length!=None:
                docstrings.append(  'length : {}'.format(length) )
                
            setattr( getattr(cls,key), '__doc__', ', '.join(docstrings) ) 
        
    def document_class(model):
        #
        # Add documentation on its fields
        #
        documented_fields = []
        
        mapper = inspect(model)

        # this is a hack to use the items method of ImmutableProperties, without
        # triggering the PY3K convertor
        for key, value in util.ImmutableProperties.items(mapper.column_attrs):
            doc = document_property( cls, key, value )
            if doc:
                documented_fields.append( doc )
                
        model.__doc__ = (model.__doc__ or '') + """

.. image:: /_static/entityviews/new_view_%s.png


        """%(model.__name__.lower()) + ''.join('\n * %s'%(doc) for doc in documented_fields)

    for cls in classes:
        document_class(cls)
