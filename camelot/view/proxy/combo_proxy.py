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
A modified query decorator to be used for Combo Boxes
"""

import logging
from PyQt4.QtCore import Qt
from PyQt4 import QtCore, QtGui
from queryproxy import QueryTableProxy

logger = logging.getLogger('proxy.combo_proxy')
logger.setLevel(logging.DEBUG)
    
class ComboProxy(QueryTableProxy):
  """Instead of storing al list_fields of an object, this proxy only stores
  the result of __unicode__ and the primary key.
  
  The proxy also has a special first row element that can be set separately
  and does not depend on the query.  It can be used to set the currently selected
  element without the need to find out its position in the query.
  """
  
  def __init__(self, *args, **kwargs):
    QueryTableProxy.__init__(self, *args, **kwargs)
    self.first_row = None
      
  def setFirstRow(self, instance_getter):
    
    def get_data():
      o = instance_getter()
      return [unicode(o),o.id]
    
    self.mt.post(get_data, lambda data:setattr(self, 'first_row',data))
  
  def setData(self, index, value, role=Qt.EditRole):
    raise Exception('cannot set data for combo box')
  
  def data(self, index, role):
#    logger.debug('get %s %s %s -> with first row %s'%(index.row(), index.column(), role, str(self.first_row)))
#    if index.row()==0 and self.first_row:
#      if role in (Qt.DisplayRole, Qt.EditRole):
#        value = self.first_row[index.column()]
#        logger.debug('return %s'%value)
#        QtCore.QVariant(value or '')
#    elif not self.first_row:
      return super(ComboProxy, self).data(index, role)
#    else:
#      return super(ComboProxy, self).data(self.index(index.row()-1, index.column()), role)
#    return QtCore.QVariant()
    
