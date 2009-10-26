#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Plugins to include custom Camelot editors into QT Designer"""

class CamelotEditorPlugin(object):
  
    def __init__(self):
        self.initialized = False
        self._widget = None
        
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True
        
    def isInitialized(self):
        return self.initialized
      
    def createWidget(self, parent):
        return self._widget(parent=parent)
      
    def name(self):
        return self._widget.__name__
      
    def group(self):
        return 'Camelot'
      
    def toolTip(self):
        return ""
      
    def whatsThis(self):
        return ""
      
    def isContainer(self):
        return False
      
    def domXml(self):
        name = self._widget.__name__
        return '<widget class="%s" name=\"%s\" />\n'%(name, name)
      
    def includeFile(self):
        return "camelot.view.controls.editors"
