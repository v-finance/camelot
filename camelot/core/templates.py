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
A default Jinja2 environment for the rendering of html in print previews
and others.

The `loader` loads its templates from the camelot/art/templates
folder.  As it is a :class:`jinja2.loaders.ChoiceLoader` object, other
loaders can be appended or prepended to it :attr:`loaders` attribute, to
customize the look of the print previews or reuse the existing style

The `environment` is a :class:`jinja2.environment.Environment` which uses
the `loader` and that can be used with
the :class:`camelot.view.action_steps.print_preview.PrintJinjaTemplate` action
step.
"""

from jinja2.environment import Environment
from jinja2.loaders import ChoiceLoader, PackageLoader

loader = ChoiceLoader( [ PackageLoader( 'camelot.art' ) ] )

class DefaultEnvironment( Environment ):
    
    def __repr__( self ):
        return '<camelot.core.templates.environment>'
    
environment = DefaultEnvironment( loader = loader )

