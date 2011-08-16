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

"""Helper functions related to the connection between the SQLAlchemy
ORM and the Camelot Views.
"""

import logging
logger = logging.getLogger('camelot.core.orm')

def refresh_session(session):
    """Session refresh expires all objects in the current session and sends
    a local entity update signal via the remote_signals mechanism

    this method ought to be called in the model thread.
    """
    from camelot.view.remote_signals import get_signal_handler
    import sqlalchemy.exc as sa_exc
    logger.debug('session refresh requested')
    signal_handler = get_signal_handler()
    refreshed_objects = []
    expunged_objects = []
    for _key, obj in session.identity_map.items():
        try:
            session.refresh( obj )
            refreshed_objects.append( obj )
        except sa_exc.InvalidRequestError:
            #
            # this object could not be refreshed, it was probably deleted
            # outside the scope of this session, so assume it is deleted
            # from the application its point of view
            #
            session.expunge( obj )
            expunged_objects.append( obj )
    for obj in refreshed_objects:
        signal_handler.sendEntityUpdate( None, obj )
    for obj in expunged_objects:
        signal_handler.sendEntityDelete( None, obj )
    return refreshed_objects
