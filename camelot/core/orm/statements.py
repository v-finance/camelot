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
import sys

MUTATORS = '__mutators__'

class ClassMutator( object ):
    """Class to create DSL statements such as `using_options`.  This is used
    to transform DSL statements in Declarative class attributes.
    The use of these statements is discouraged in any new code, and exists for
    compatibility with Elixir model definitions"""
    
    def __init__( self, *args, **kwargs ):
        # jam this mutator into the class's mutator list
        class_locals = sys._getframe(1).f_locals
        mutators = class_locals.setdefault( MUTATORS, [] )
        mutators.append( (self, args, kwargs) )
        
    def process( self, entity_dict, *args, **kwargs ):
        """
        Process one mutator.  This method should be overwritten in a subclass
        """
        pass

