import sys

MUTATORS = '__mutators__'

class ClassMutator( object ):
    """Class to create DSL statements such as `using_options`.  This is used
    to transform Elixir like DSL statements in Declarative class attributes.
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
