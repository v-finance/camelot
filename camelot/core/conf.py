#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
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
            
    def get( self, name, default ):
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
        LOGGER.warning( u'no such settings attribute : %s'%name )
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
            self._local_folder = os.path.join( winpaths.get_local_appdata(), 
                                               author, 
                                               name )
        else:
            self._local_folder = os.path.join( os.path.expanduser('~'), 
                                               u'.%s'%author, name )
        if not os.path.exists( self._local_folder ):
            os.makedirs( self._local_folder )
            
        LOGGER.info( u'store database and media in %s'%self._local_folder )
            
    def CAMELOT_MEDIA_ROOT(self):
        return os.path.join( self._local_folder, 'media' )
    
    def ENGINE( self ):
        from sqlalchemy import create_engine
        return create_engine(u'sqlite:///%s/%s'%( self._local_folder,
                                                  self.data ) )
