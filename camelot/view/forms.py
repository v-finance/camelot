#  ==================================================================================
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
#  ==================================================================================

"""
Python structures to represent interface forms.  These structures can be transformed
to QT forms.
"""

class Form(object):
  """Use the QFormLayout widget to render a form"""
  
  def __init__(self, fields):
    """@param fields: the fields to render"""
    self.fields = fields 
  
  def get_fields(self):
    """@return : the set of fields, visible in this form"""
    return self.fields
  
  def render(self, widgets):
    """
    @param widgets: a dictionary mapping each field in this form to a tuple of (label widget, value widget) 
    @return : a QWidget into which the form is rendered"""
    from PyQt4 import QtGui
    form_layout = QtGui.QFormLayout()
    for field in self.fields:
      label_widget, value_widget = widgets[field]
      form_layout.addRow(label_widget, value_widget)
    form_widget = QtGui.QWidget()
    form_widget.setLayout(form_layout)
    return form_widget
  
class TabForm(object):
  """Render forms within a QTabWidget"""
  
  