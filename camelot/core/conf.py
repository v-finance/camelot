"""
The global configuration of a Camelot application is handled through a LazyProxy
object that reads settings from various targets.  The default target reads
the attributes from the 'settings' module, if this is found on the PYTHONPATH.

To access the global configuration, simply import the settings object::
    
    from camelot.core.conf import settings
    
    print settings.CAMELOT_MEDIA_ROOT
    
Developers can add targets to the settings proxy, to enable reading settings
from other sources.
"""

class LazyProxy(list):
    """A lazy proxy of the 'settings' module on the PYTHONPATH, or other
    targets that contain global configuration.  This proxy behaves as a list
    to which targets can be appended.  The value of the first target in the
    list that has the requested attribute will be returned.
    
    The Proxy is Lazy, because on each request of an attribute, the target
    is queried again.
    """
            
    def __getattr__(self, name):
        if not len(self):
            self.append_settings_module()
        for target in self:
            if hasattr(target, name):
                return getattr(target, name)
        raise AttributeError()
        
    def __hasattr__(self, name):
        if not len(self):
            self.append_settings_module()
        for target in self:
            if hasattr(target, name):
                return True
        return False
        
    def append_settings_module(self):
        """Import the 'settings' module and append it as a target to
        the list of targets.  This function will be called, if no other
        targets are specified"""
        
        try:
            mod = __import__('settings', {}, {}, [''])
        except ImportError, e:
            raise ImportError, "Could not import settings (Is it on sys.path? Does it have syntax errors?): %s" % (e)
        self.append( mod )

        
settings = LazyProxy()
