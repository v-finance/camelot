#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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

import six

from ..core.qt import Qt

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
        return u', '.join(six.text_type(i) for i in self.intervals)





