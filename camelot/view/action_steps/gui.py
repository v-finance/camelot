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

"""
Various ``ActionStep`` subclasses that manipulate the GUI of the application.
"""

from camelot.admin.action.base import ActionStep

class Refresh( ActionStep ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""
    
    def gui_run( self, gui_context ):
        gui_context.workspace.refresh()


class ShowChart( ActionStep ):
    
    def __init__( self, chart ):
        """
        :param chart: a :class:`camelot.core.container.FigureContainer` or
            :class:`camelot.core.container.AxesContainer`
        """
        self.chart = chart
        
    def gui_run( self, gui_context ):
        from camelot.view.controls.editors import ChartEditor
        litebox = ChartEditor.show_fullscreen_chart( self._chart, 
                                                     gui_context.workspace )

    
class ShowPixmap( ActionStep ):
    
    def __init__( self, pixmap ):
        """
        :param pixmap: a :class:`camelot.view.art.Pixmap` object
        """
        self.pixmap = pixmap
        
    def gui_run( self, gui_context ):
        from camelot.view.controls.liteboxview import LiteBoxView
        litebox = LiteBoxView( parent = gui_context.workspace )
        litebox.show_fullscreen_pixmap( self.pixmap.getQPixmap() )
