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
from customdelegate import CustomDelegate
from camelot.view.controls import editors

class ManyToOneChoicesDelegate( CustomDelegate ):
    """Display a ManyToOne field as a ComboBox, filling the list of choices with
  the objects of the target class. 
  
  .. image:: /_static/enumeration.png
  
  The items in the ComboBox are the unicode representation of the related objects.
  So these classes need an implementation of their __unicode__ method to show
  up in a human readable way in the ComboBox.
  """
  
    editor = editors.OneToManyChoicesEditor
