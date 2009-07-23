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

"""Functionallity common to TableViews and FormViews
"""

from PyQt4 import QtCore, QtGui

from camelot.view.model_thread import get_model_thread

class AbstractView(object):
  """A string used to format the title of the view ::

title_format = 'Movie rental overview'
"""  
  
  title_format = ''

class TabView(QtGui.QTabWidget, AbstractView):
  """Class to combine multiple views in Tabs and let them behave as one view.  This class can be
used when defining custom create_table_view methods on an ObjectAdmin class to group multiple
table views together in one view.
"""
  
  def __init__(self, parent, views=[]):
    """
:param views: a list of the views to combine
"""
    QtGui.QTabWidget.__init__(self, parent)
    AbstractView.__init__(self, parent)
    self.setWindowTitle(self.title_format)
    
    def get_views_and_titles():
      return [(view, view.get_title()) for view in views]
    
    def set_views_and_titles(views_and_titles):
      for view, title in views_and_titles:
        self.addTab(view, title)

    get_model_thread().post(get_views_and_titles, set_views_and_titles)