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
"""
The global configuration of a Camelot application is handled through a LazyProxy
object that reads settings from various targets.  The default target reads
the attributes from the 'settings' module, if this is found on the PYTHONPATH.

To access the global configuration, simply import the settings object::
    
    from camelot.core.conf import settings
    
    print(settings.CAMELOT_MEDIA_ROOT)
    
Developers can add targets to the settings proxy, to enable reading settings
from other sources.
"""

import logging
import os
import sys

LOGGER = logging.getLogger('camelot.core.conf')

class LazyProxy(list):
    """A lazy proxy of the 'settings' module on the PYTHONPATH, or other
    targets that contain global configuration.  This proxy behaves as a list
    to which targets can be appended.  The value of the first target in the
    list that has the requested attribute will be returned.
    
    The Proxy is Lazy, because on each request of an attribute, the target
    is queried again.
    """
            
    def get( self, name, default=None ):
        """Get an attribute of the proxy, and when not found return default
        as value.  This function behaves the same as the get function of a
        dictionary.
        """
        try:
            return getattr( self, name )
        except AttributeError:
            return default
        
    def __getattr__(self, name):
        if not len(self):
            self.append_settings_module()
        for target in self:
            if hasattr(target, name):
                return getattr(target, name)
        LOGGER.debug( u'no such settings attribute : %s'%name )
        raise AttributeError()
        
    def append_settings_module(self):
        """Import the 'settings' module and append it as a target to
        the list of targets.  This function will be called, if no other
        targets are specified"""
        
        try:
            mod = __import__('settings', {}, {}, [''])
        except ImportError:
            return False
        self.append( mod )
        return True

settings = LazyProxy()

class SimpleSettings( object ):
    """Settings that can be used for the creation of a simple Camelot
    application.  Use these settings by appending them to the global settings
    at application startup::
    
        from camelot.core.conf import settings, SimpleSettings
        
        settings.append( SimpleSettings('myapp') )
    """

    def __init__( self, author, name, data = 'data.sqlite' ):
        """
        :param author: the name of the writer of the application
        :param name: the name of the application
        :param data: the name of the sqlite database file
        
        These names will be used to create a folder where the local data will 
        be stored.  On Windows this will be in the AppData folder of the user,
        otherwise it will be in a `.author` folder in the home directory of the
        user.
        """        
        self.data = data
        if ('win' in sys.platform) and ('darwin' not in sys.platform):
            import winpaths
            self.data_folder = os.path.join( winpaths.get_local_appdata(), 
                                               author, 
                                               name )
        else:
            self.data_folder = os.path.join( os.path.expanduser('~'), 
                                               u'.%s'%author, name )
        if not os.path.exists( self.data_folder ):
            os.makedirs( self.data_folder )
            
        LOGGER.info( u'store database and media in %s'%self.data_folder )
            
    def CAMELOT_MEDIA_ROOT(self):
        return os.path.join( self.data_folder, 'media' )
    
    def ENGINE( self ):
        from sqlalchemy import create_engine
        return create_engine(u'sqlite:///%s/%s'%( self.data_folder,
                                                  self.data ) )

class SerializableSettings(object):

    def __init__(self, **args):
        for k,v in args.items():
            setattr(self, k, v)
