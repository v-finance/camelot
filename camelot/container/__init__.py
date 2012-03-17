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
    return IntervalsContainer()

  class Admin(EntityAdmin):
    form_display = ['my_interval']
    field_attributes = dict(my_interval=dict(delegate=IntervalsDelegate))

"""

from PyQt4.QtCore import Qt

class Container(object):
    """Top level class for all container classes"""
    pass

class Arrow(Container):
    """
    Container to describe arrows
    """
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width

    def __unicode__(self):
        return "{0!s}, {1!s}, {2!s}]".format(self.x, self.y, self.width)

class Interval(object):
    """Helper class for IntervalsContainer, specifications for one interval"""

    def __init__(self, begin, end, name='', color=Qt.black):
        """
        :param begin: integer of float specifiying the begin of the interval
        :param end: integer of float specifiying the end of the interval
        :param name: a string representing the name of the interval
        :param color: a QColor to be used to display the interval
        """
        self.begin = begin
        self.end = end
        self.name = name
        self.color = color

    def __unicode__(self):
        return u'[%s,%s]'%(self.begin, self.end)

class IntervalsContainer(Container):
    """Containter to hold interval data

    eg : representing the time frame of 8pm till 6am that someone was at work using an hourly
    precision :

    intervals = IntervalsContainer(0, 24, [Interval(8, 18, 'work')])
    """

    def __init__(self, min, max, intervals):
        """
        @param min: minimum value that the begin value of an interval is allowed to have
        @param max: maximum ...
        @param intervals: list of Interval classes
        """
        self.min = min
        self.max = max
        self.intervals = intervals

    def __unicode__(self):
        return u', '.join(unicode(i) for i in self.intervals)



