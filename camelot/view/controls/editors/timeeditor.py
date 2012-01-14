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
import datetime

from PyQt4 import QtGui

from customeditor import AbstractCustomEditor, set_background_color_palette, draw_tooltip_visualization
from camelot.core import constants

class TimeEditor(QtGui.QTimeEdit, AbstractCustomEditor):
  
    def __init__(self, 
                 parent,
                 editable = True,
                 field_name = 'time',
                 format = constants.camelot_time_format, **kwargs):
        QtGui.QTimeEdit.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.setDisplayFormat(format)
        self.setEnabled(editable)

    def set_value(self, value):
        value = AbstractCustomEditor.set_value(self, value)
        if value:
            self.setTime(value)
        else:
            self.setTime(self.minimumTime())
            
    def get_value(self):
        value = self.time()
        value = datetime.time(hour=value.hour(),
                              minute=value.minute(),
                              second=value.second())
        return AbstractCustomEditor.get_value(self) or value
        
    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.setToolTip(unicode(tooltip or ''))
      
    def set_enabled(self, editable=True):
        self.setEnabled(editable)

    def paintEvent(self, event):
        super(TimeEditor, self).paintEvent( event )
        if self.toolTip():
            draw_tooltip_visualization(self)
        
    def set_background_color( self, background_color ):
        set_background_color_palette( self.lineEdit(), background_color )


