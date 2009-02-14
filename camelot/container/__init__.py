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

"""Container classes are classes that are used to transport data between the
model thread and the GUI thread.

When complex data sets need to be visualized (eg.: charts, intervals), built-in
python types don't contain enough information, while dictionary like structures
are not self documented.  Hence the need of specialized container classes to 
transport this data between the model and the GUI.

To use this classes : 

1. On your model class, define properties returning a container class
2. In the admin class, add the property to the list of fields to visualize, and
   specify its delegate
   
eg:

class MyEntity(Entity):

  @property
  def my_interval(self):
    return IntervalContainer(...) 

  class Admin(EntityAdmin):
    form_display = ['my_interval']
    field_attributes = dict(my_interval=dict(delegate=IntervalDelegate))
    
"""

class IntervalContainer(object):
  pass